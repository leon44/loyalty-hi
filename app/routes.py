from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional
import qrcode
import io
import base64
import datetime

from app.epos_client import EposNowClient

bp = Blueprint('main', __name__)

class ProfileForm(FlaskForm):
    forename = StringField('First Name', validators=[DataRequired()])
    surname = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Contact Number', validators=[Optional()])
    marketing_email = BooleanField('Receive email marketing')
    marketing_text = BooleanField('Receive text marketing')
    submit = SubmitField('Update Profile')

@bp.before_request
def require_login():
    if 'user_email' not in session and request.endpoint != 'static':
        if request.blueprint != 'auth':
            return redirect(url_for('auth.login'))

@bp.route('/')
@bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    epos_client = EposNowClient()
    customer = epos_client.get_customer_by_email(session['user_email'])
    customer_id = customer.get('Id') if customer else None


    form_data = {}
    if customer:
        form_data = {
            'forename': customer.get('Forename'),
            'surname': customer.get('Surname'),
            'phone': customer.get('ContactNumber'),
            'marketing_email': customer.get('MarketingConsent', {}).get('Email'),
            'marketing_text': customer.get('MarketingConsent', {}).get('Text')
        }
    form = ProfileForm(data=form_data)

    if form.validate_on_submit():
        try:
            if customer:  # Existing customer, so update
                # The API requires the full customer object for updates.
                updated_customer_data = customer.copy()
                updated_customer_data.update({
                    'Forename': form.forename.data,
                    'Surname': form.surname.data,
                    'ContactNumber': form.phone.data,
                    'MarketingConsent': {
                        'Email': form.marketing_email.data,
                        'Text': form.marketing_text.data
                    }
                })
                epos_client.update_customer(updated_customer_data)
                flash('Your profile has been updated successfully!', 'success')
                session['customer_name'] = f"{updated_customer_data['Forename']} {updated_customer_data['Surname']}"
            else:  # New customer, so create
                new_customer_data = {
                    'Forename': form.forename.data,
                    'Surname': form.surname.data,
                    'EmailAddress': session['user_email'],
                    'ContactNumber': form.phone.data,
                    'Type': 6594, # Customer Type ID
                    'MarketingConsent': {
                        'Email': form.marketing_email.data,
                        'Text': form.marketing_text.data
                    }
                }
                new_customer = epos_client.create_customer(new_customer_data)
                session['customer_id'] = new_customer.get('Id')
                flash('Welcome! Your profile has been created.', 'success')
                session['customer_name'] = f"{new_customer_data['Forename']} {new_customer_data['Surname']}"

            return redirect(url_for('main.dashboard'))
        except Exception as e:
            flash('There was an error saving your profile.', 'danger')

    # Show the edit form only if 'edit=true' is in the URL, or if it's a new customer.
    show_edit_form = request.args.get('edit') == 'true' or not customer

    points_raw = customer.get('CurrentPoints', 0) if customer else 0
    points_balance = f"£{points_raw / 100:.2f}"
    last_updated = None
    if customer:
        last_updated = datetime.datetime.now().strftime('%d %b %Y, %H:%M')

    qr_code_data = None
    if customer and customer.get('CardNumber'):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(customer['CardNumber'])
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf)
        buf.seek(0)
        
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        qr_code_data = f'data:image/png;base64,{img_base64}'


    return render_template('dashboard.html', 
                           customer=customer, 
                           form=form, 
                           points_balance=points_balance,
                           last_updated=last_updated,
                           show_edit_form=show_edit_form, 
                           qr_code_data=qr_code_data)
