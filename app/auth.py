import datetime
import logging
import random
import string
import jwt
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

from app import db
from app.models import RateLimit
from app.epos_client import EposNowClient
from app.email_service import send_login_code

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bp = Blueprint('auth', __name__)

# Constants
MAGIC_LINK_EXPIRATION_MINUTES = 15
RATE_LIMIT_EMAIL_HOUR = 5
RATE_LIMIT_IP_HOUR = 20

class EmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Login Code')

def generate_login_token(email, code):
    """Generate JWT token for login code verification"""
    payload = {
        'email': email,
        'code': code,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        'attempts': 0,
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.secret_key, algorithm='HS256')

def verify_login_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, current_app.secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

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

        # Backdoor for Apple App Review - bypass magic link
        if email == 'leon44+appletestaccount@gmail.com':
            actual_email = 'leon44@gmail.com'
            session['user_email'] = actual_email
            
            # Get customer info for session
            epos_client = EposNowClient()
            customer = epos_client.get_customer_by_email(actual_email)
            if customer:
                customer_name = f"{customer.get('Forename', '')} {customer.get('Surname', '')}".strip()
                session['customer_name'] = customer_name if customer_name else 'User'
            
            logging.info(f'Apple test account backdoor login: {email} -> {actual_email}')
            return redirect(url_for('main.dashboard'))

        # Rate limiting
        is_dev = current_app.debug
        email_limit = 500 if is_dev else RATE_LIMIT_EMAIL_HOUR
        ip_limit = 2000 if is_dev else RATE_LIMIT_IP_HOUR

        if not check_rate_limit(f'email:{email}', email_limit) or \
           not check_rate_limit(f'ip:{ip_address}', ip_limit):
            logging.warning(f'Rate limit exceeded for email {email} or IP {ip_address}')
            # Still show the same page to prevent user enumeration
            return redirect(url_for('auth.check_inbox'))

        # Generate 4-digit code and JWT token
        code = ''.join(random.choices(string.digits, k=4))
        token = generate_login_token(email, code)

        # Send email with 4-digit code
        send_login_code(email, code)
        
        # Store email and token in session for code entry page
        session['pending_email'] = email
        session['login_token'] = token
        
        # Log for debugging purposes
        logging.info(f'Generated 4-digit login code for {email}: {code}')

        return redirect(url_for('auth.check_inbox'))

    return render_template('enter_email.html', form=form)

@bp.route('/login/check-inbox')
def check_inbox():
    return render_template('check_inbox.html')

@bp.route('/login/verify-code', methods=['POST'])
def verify_code():
    # Get token from session
    token = session.get('login_token')
    user_code = request.form.get('code', '')
    
    if not token or not user_code:
        flash('Session expired. Please request a new code.', 'danger')
        return render_template('check_inbox.html')
    
    # Verify JWT token
    payload = verify_login_token(token)
    
    if not payload:
        flash('Session expired. Please request a new code.', 'danger')
        return render_template('check_inbox.html')
    
    # Check if code matches
    if payload['code'] != user_code:
        flash('Invalid code. Please check and try again.', 'danger')
        logging.warning(f'Invalid login code attempt for {payload["email"]}: {user_code}')
        return render_template('check_inbox.html')
    
    # Check attempts (stored in token)
    if payload.get('attempts', 0) >= 4:
        flash('Too many attempts. Please request a new code.', 'danger')
        return render_template('check_inbox.html')
    
    logging.info(f'Successful login for {payload["email"]} using 4-digit code')
    
    # Log the user in. Fetch customer data from EPOS Now to populate the session.
    session.clear()
    session['user_email'] = payload['email']
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(days=14)

    try:
        epos_client = EposNowClient()
        customer = epos_client.get_customer_by_email(payload['email'])
        if customer:
            session['customer_id'] = customer.get('Id')
            session['customer_name'] = f"{customer.get('Forename', '')} {customer.get('Surname', '')}".strip()
            logging.info(f"Existing customer '{session['customer_name']}' logged in.")
        else:
            logging.warning(f"New user with email {payload['email']} logged in. No profile found in EPOS Now.")
            session['customer_id'] = None
            session['customer_name'] = 'New User'
    except Exception as e:
        logging.error(f'Failed to fetch EPOS customer data for {payload["email"]}: {e}')
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
