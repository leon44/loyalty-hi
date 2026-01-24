import datetime
import hashlib
import secrets
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

from app import db
from app.models import MagicLinkToken, RateLimit
from app.epos_client import EposNowClient
from app.email_service import send_magic_link

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bp = Blueprint('auth', __name__)

# Constants
MAGIC_LINK_EXPIRATION_MINUTES = 15
RATE_LIMIT_EMAIL_HOUR = 5
RATE_LIMIT_IP_HOUR = 20

class EmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Magic Link')

def check_rate_limit(key, limit, period_seconds=3600):
    """Checks and increments a rate limit counter in the database."""
    now = datetime.datetime.utcnow()
    period_start = now - datetime.timedelta(seconds=period_seconds)
    
    rate_limit = RateLimit.query.filter(
        RateLimit.key == key,
        RateLimit.window_start >= period_start
    ).first()

    if rate_limit and rate_limit.count >= limit:
        return False
    
    if rate_limit:
        rate_limit.count += 1
    else:
        rate_limit = RateLimit(key=key, count=1, window_start=now)
        db.session.add(rate_limit)
    
    db.session.commit()
    return True

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = EmailForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        ip_address = request.remote_addr

        # Rate limiting
        is_dev = current_app.debug
        email_limit = 500 if is_dev else RATE_LIMIT_EMAIL_HOUR
        ip_limit = 2000 if is_dev else RATE_LIMIT_IP_HOUR

        if not check_rate_limit(f'email:{email}', email_limit) or \
           not check_rate_limit(f'ip:{ip_address}', ip_limit):
            logging.warning(f'Rate limit exceeded for email {email} or IP {ip_address}')
            # Still show the same page to prevent user enumeration
            return redirect(url_for('auth.check_inbox'))

        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=MAGIC_LINK_EXPIRATION_MINUTES)

        new_token = MagicLinkToken(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            request_ip=ip_address,
            user_agent=request.user_agent.string
        )
        db.session.add(new_token)
        db.session.commit()

        # Send email with magic link
        magic_link_url = url_for('auth.verify_link', token=token, _external=True)
        
        # Send email with magic link via MailJet
        send_magic_link(email, magic_link_url)
        
        # Log for debugging purposes
        logging.info(f'Generated magic link for {email}: {magic_link_url}')

        return redirect(url_for('auth.check_inbox'))

    return render_template('enter_email.html', form=form)

@bp.route('/login/check-inbox')
def check_inbox():
    return render_template('check_inbox.html')

@bp.route('/login/verify/<token>')
def verify_link(token):
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    magic_token = MagicLinkToken.query.filter_by(token_hash=token_hash).first()

    if not magic_token or not magic_token.is_valid():
        logging.warning(f'Invalid or expired magic link token used.')
        flash('This magic link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    # Mark token as used
    magic_token.used_at = datetime.datetime.utcnow()
    db.session.commit()

    # Log the user in. Fetch customer data from EPOS Now to populate the session.
    session.clear()
    session['user_email'] = magic_token.email
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(days=14)

    try:
        epos_client = EposNowClient()
        customer = epos_client.get_customer_by_email(magic_token.email)
        print(customer)
        if customer:
            session['customer_id'] = customer.get('Id')
            session['customer_name'] = f"{customer.get('Forename', '')} {customer.get('Surname', '')}".strip()
            logging.info(f"Existing customer '{session['customer_name']}' logged in.")
        else:
            logging.warning(f"New user with email {magic_token.email} logged in. No profile found in EPOS Now.")
            session['customer_id'] = None
            session['customer_name'] = 'New User'
    except Exception as e:
        logging.error(f'Failed to fetch EPOS customer data for {magic_token.email}: {e}')
        flash('Could not retrieve your customer profile at this time. Please try again later.', 'warning')
        # Allow login even if EPOS lookup fails, user will be treated as new.
        session['customer_id'] = None
        session['customer_name'] = 'User'

    return redirect(url_for('main.dashboard'))

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
