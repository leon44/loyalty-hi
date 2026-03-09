from flask import Blueprint, Response, session, redirect, url_for, flash, current_app
import os
import logging
import tempfile
import base64
from py_pkpass.models import Pass, StoreCard, Barcode, BarcodeFormat, Field
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

    # Get configuration from environment variables
    team_id = os.environ.get('APPLE_TEAM_ID')
    pass_type_id = os.environ.get('PASS_TYPE_ID')
    # Password should be None if not set or empty (for unencrypted keys exported with -nodes)
    cert_password = os.environ.get('PASS_CERT_PASSWORD', '').strip()
    cert_password = cert_password if cert_password else None

    if not team_id or not pass_type_id:
        flash('Apple Wallet pass is not configured. Please contact support.', 'danger')
        logging.error('APPLE_TEAM_ID or PASS_TYPE_ID not set in environment variables')
        return redirect(url_for('main.dashboard'))

    # Get certificates from environment variables (base64 encoded) or files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Try to get certificates from environment variables first (for production)
    cert_base64 = os.environ.get('PASS_CERT_BASE64')
    key_base64 = os.environ.get('PASS_KEY_BASE64')
    wwdr_base64 = os.environ.get('WWDR_CERT_BASE64')
    
    if cert_base64 and key_base64 and wwdr_base64:
        # Decode base64 certificates from environment variables
        try:
            cert_data = base64.b64decode(cert_base64)
            key_data = base64.b64decode(key_base64)
            wwdr_data = base64.b64decode(wwdr_base64)
            
            # Write to temporary files for py_pkpass library
            temp_dir = tempfile.gettempdir()
            cert_path = os.path.join(temp_dir, 'pass_cert.pem')
            key_path = os.path.join(temp_dir, 'pass_key.pem')
            wwdr_cert_path = os.path.join(temp_dir, 'wwdr.pem')
            
            with open(cert_path, 'wb') as f:
                f.write(cert_data)
            with open(key_path, 'wb') as f:
                f.write(key_data)
            with open(wwdr_cert_path, 'wb') as f:
                f.write(wwdr_data)
                
            logging.info('Using certificates from environment variables')
        except Exception as e:
            flash('Error decoding certificates. Please contact support.', 'danger')
            logging.error(f'Error decoding base64 certificates: {str(e)}')
            return redirect(url_for('main.dashboard'))
    else:
        # Fallback to file-based certificates (for local development)
        cert_path = os.path.join(base_dir, 'app', 'certificates', 'pass_cert.pem')
        key_path = os.path.join(base_dir, 'app', 'certificates', 'pass_key.pem')
        wwdr_cert_path = os.path.join(base_dir, 'app', 'certificates', 'wwdr.pem')
        
        # Check if certificate files exist
        if not all([os.path.exists(cert_path), os.path.exists(key_path), os.path.exists(wwdr_cert_path)]):
            flash('Apple Wallet certificates are not configured. Please contact support.', 'danger')
            logging.error(f'Missing certificate files. Checked: {cert_path}, {key_path}, {wwdr_cert_path}')
            return redirect(url_for('main.dashboard'))
        
        logging.info('Using certificates from files')

    # --- Pass Generation ---
    # Create store card with customer information
    card = StoreCard()
    
    # Secondary field: Customer name (smaller, no label)
    customer_name = f"{customer.get('Forename', '')} {customer.get('Surname', '')}".strip()
    if customer_name:
        card.addSecondaryField('name', customer_name, '')  # Empty label
    
    # Back field: Link to check balance online
    card.addBackField('website', 'https://loyalty.hotelsinternational.co.uk', 'Check Your Balance')

    # QR code barcode (modern standard)
    barcode_data = customer['CardNumber']
    barcode = Barcode(message=barcode_data, format=BarcodeFormat.QR)
    
    # Create pass with colors (black and gold theme)
    pass_obj = Pass(
        card,
        passTypeIdentifier=pass_type_id,
        organizationName='Hotels International',
        teamIdentifier=team_id
    )
    
    # Set pass properties
    pass_obj.logoText = 'Hotels International'
    pass_obj.description = 'Loyalty Card'
    pass_obj.backgroundColor = 'rgb(26, 26, 26)'  # Deep charcoal
    pass_obj.foregroundColor = 'rgb(245, 245, 245)'  # Off-white
    pass_obj.labelColor = 'rgb(189, 160, 109)'  # Muted gold
    pass_obj.barcode = barcode

    # Add pass assets (icons and logo)
    assets_dir = os.path.join(base_dir, 'app', 'static', 'pass_assets')
    
    # Required assets
    required_assets = [
        'icon.png', 'icon@2x.png', 'icon@3x.png',
        'logo.png', 'logo@2x.png', 'logo@3x.png'
    ]
    
    for asset in required_assets:
        asset_path = os.path.join(assets_dir, asset)
        if os.path.exists(asset_path):
            with open(asset_path, 'rb') as f:
                pass_obj.addFile(asset, f)
        else:
            logging.warning(f'Pass asset not found: {asset_path}')

    # Sign and create the pass
    try:
        # Create the pass - this returns a BytesIO object
        pass_file = pass_obj.create(cert_path, key_path, wwdr_cert_path, cert_password)
        
        logging.info(f'Successfully generated wallet pass for customer {customer.get("Id")}')
        
        return Response(
            pass_file.getvalue(),
            mimetype='application/vnd.apple.pkpass',
            headers={'Content-Disposition': 'attachment; filename=hotels_international_loyalty.pkpass'}
        )
    except Exception as e:
        flash('Unable to generate your wallet pass. Please try again later.', 'danger')
        logging.error(f'Error generating wallet pass: {str(e)}', exc_info=True)
        return redirect(url_for('main.dashboard'))
