from flask import Blueprint, Response, session, redirect, url_for, flash
import os
import io
from pkpass.models import Pass, StoreCard, BarcodeFormat
import barcode
from barcode.writer import ImageWriter
from app.epos_client import EposNowClient

bp = Blueprint('wallet', __name__, url_prefix='/wallet')

@bp.route('/generate_pass')
def generate_pass():
    if 'user_email' not in session:
        flash('You must be logged in to add a pass to your wallet.', 'warning')
        return redirect(url_for('auth.login'))

    epos_client = EposNowClient()
    customer = epos_client.get_customer_by_email(session['user_email'])

    if not customer or 'CardNumber' not in customer:
        flash('Could not retrieve your customer information to generate a pass.', 'danger')
        return redirect(url_for('main.dashboard'))

    # --- Pass Generation ---
    pass_obj = Pass(
        pass_type_id='pass.com.example.loyalty',
        team_id='YOUR_TEAM_ID', # <-- IMPORTANT: Replace with your Team ID
        organization_name='LoyaltyHI'
    )

    card = StoreCard()
    card.add_primary_field('name', customer.get('Forename', ''), 'Member Name')
    card.add_secondary_field('points', str(customer.get('CurrentPoints', 0)), 'Points')
    pass_obj.add_card(card)

    # Generate Barcode
    barcode_data = customer['CardNumber']
    pass_obj.add_barcode(BarcodeFormat.CODE_128, barcode_data)

    # Add placeholder assets
    pass_obj.add_file('icon.png', 'app/static/images/icon.png')
    pass_obj.add_file('icon@2x.png', 'app/static/images/icon@2x.png')
    pass_obj.add_file('logo.png', 'app/static/images/logo.png')

    # --- Signing (Placeholder) ---
    cert_path = 'app/certificates/pass.com.example.loyalty.pem'
    key_path = 'app/certificates/pass.com.example.loyalty.key'
    wwdr_cert_path = 'app/certificates/AppleWWDRCA.pem'
    password = 'YOUR_CERT_PASSWORD' # The password for your .p12 file, if any

    # Create placeholder certificate files if they don't exist
    if not os.path.exists(cert_path):
        open(cert_path, 'w').close()
    if not os.path.exists(key_path):
        open(key_path, 'w').close()
    if not os.path.exists(wwdr_cert_path):
        open(wwdr_cert_path, 'w').close()

    try:
        pass_bytes = pass_obj.create(
            cert_path, key_path, wwdr_cert_path, password
        )
    except Exception as e:
        flash(f'Could not sign the pass. Please ensure your certificates are correctly configured. Error: {e}', 'danger')
        return redirect(url_for('main.dashboard'))

    return Response(
        pass_bytes,
        mimetype='application/vnd.apple.pkpass',
        headers={'Content-Disposition': 'attachment; filename=loyalty_pass.pkpass'}
    )
