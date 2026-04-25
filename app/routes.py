from flask import Blueprint, render_template, session, redirect, url_for, flash, request, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional
import qrcode
import io
import base64
import datetime
import os

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
    # Allow public access to apple-app-site-association for iOS deep linking
    if request.endpoint == 'main.apple_app_site_association':
        return None
    
    # Allow public access to assetlinks.json for Android TWA deep linking
    if request.endpoint == 'main.assetlinks':
        return None
    
    # Allow public access to app-redirect for magic link redirects
    if request.endpoint == 'main.app_redirect':
        return None
    
    # Allow public access to PWA files
    if request.endpoint in ['main.manifest', 'main.service_worker']:
        return None
    
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
                    'Type': 861, # Customer Type ID
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


    # Get customer type for badge display
    customer_type = customer.get('Type') if customer else None
    
    return render_template('dashboard.html', 
                           customer=customer, 
                           form=form, 
                           points_balance=points_balance,
                           last_updated=last_updated,
                           show_edit_form=show_edit_form, 
                           qr_code_data=qr_code_data,
                           customer_type=customer_type)

@bp.route('/.well-known/apple-app-site-association')
def apple_app_site_association():
    """Serve the Apple App Site Association file for deep linking."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
    return send_from_directory(os.path.join(static_dir, '.well-known'), 
                                'apple-app-site-association',
                                mimetype='application/json')

@bp.route('/.well-known/assetlinks.json')
def assetlinks():
    """Serve the Asset Links file for Android TWA deep linking."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
    return send_from_directory(os.path.join(static_dir, '.well-known'), 
                                'assetlinks.json',
                                mimetype='application/json')

@bp.route('/manifest.json')
def manifest():
    """Serve the PWA manifest file."""
    from flask import make_response
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
    response = make_response(send_from_directory(static_dir, 'manifest.json', mimetype='application/json'))
    # Prevent aggressive caching - allow updates to be picked up quickly
    response.headers['Cache-Control'] = 'public, max-age=600'  # 10 minutes
    return response

@bp.route('/service-worker.js')
def service_worker():
    """Serve the service worker file."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
    return send_from_directory(static_dir, 'service-worker.js', mimetype='application/javascript')

@bp.route('/app-redirect')
def app_redirect():
    """Redirect page that launches the app via custom URL scheme."""
    target_url = request.args.get('url', '')
    
    if not target_url:
        flash('Invalid redirect link.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Return HTML page with JavaScript redirect to custom URL scheme
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Opening Loyalty App...</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                text-align: center;
                padding: 20px;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #1a1a1a;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h2>Opening Loyalty App...</h2>
            <p>If the app doesn't open, <a href="{target_url}">click here</a> to continue in your browser.</p>
        </div>
        <script>
            const targetUrl = new URLSearchParams(window.location.search).get('url');
            if (targetUrl) {{
                // Attempt to open the app with custom URL scheme
                window.location.href = 'loyaltyapp://open?url=' + encodeURIComponent(targetUrl);
                
                // Fallback to web URL after a short delay if app doesn't open
                setTimeout(function() {{
                    window.location.href = targetUrl;
                }}, 2000);
            }}
        </script>
    </body>
    </html>
    '''

@bp.route('/app')
def app_download():
    """Redirect page that sends users to appropriate app store."""
    return render_template('app_download.html')
