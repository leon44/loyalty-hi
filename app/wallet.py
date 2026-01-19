from flask import Blueprint, Response, session, redirect, url_for, flash, send_file
import os
import io
from passbook.models import Pass, Barcode, StoreCard
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
    card = StoreCard()
    card.add_primary_field('name', customer.get('Forename', ''), 'Member Name')
    card.add_secondary_field('points', str(customer.get('CurrentPoints', 0)), 'Points')

    # Generate Barcode
    code128 = barcode.get_barcode_class('code128')
    barcode_data = customer['CardNumber']
    barcode_image = code128(barcode_data, writer=ImageWriter())
    barcode_buffer = io.BytesIO()
    barcode_image.write(barcode_buffer)

    pass_barcode = Barcode(message=barcode_data, format='PKBarcodeFormatCode128')
    card.barcode = pass_barcode

    # Create the pass
    pass_obj = Pass(card, \
                    passTypeIdentifier='pass.com.example.loyalty', \
                    organizationName='LoyaltyHI', \
                    teamIdentifier='YOUR_TEAM_ID') # <-- IMPORTANT: Replace with your Team ID

    # Add placeholder assets
    pass_obj.add_file('icon.png', open('app/static/images/icon.png', 'rb').read())
    pass_obj.add_file('icon@2x.png', open('app/static/images/icon@2x.png', 'rb').read())
    pass_obj.add_file('logo.png', open('app/static/images/logo.png', 'rb').read())

    # --- Signing (Placeholder) ---
    # IMPORTANT: You need to replace these with your actual certificate and key files.
    # You will get these from your Apple Developer account.
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
        pass_obj.create(cert_path, key_path, wwdr_cert_path, password)
        pass_bytes = pass_obj.getvalue()
    except Exception as e:
        flash(f'Could not sign the pass. Please ensure your certificates are correctly configured. Error: {e}', 'danger')
        return redirect(url_for('main.dashboard'))

    return Response(
        pass_bytes,
        mimetype='application/vnd.apple.pkpass',
        headers={'Content-Disposition': 'attachment; filename=loyalty_pass.pkpass'}
    )
