from flask import Blueprint, redirect, session, flash, url_for
import os
import logging
import base64
import json
import tempfile
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from app.epos_client import EposNowClient

bp = Blueprint('google_wallet', __name__, url_prefix='/google-wallet')

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
    issuer_id = os.environ.get('GOOGLE_WALLET_ISSUER_ID')
    class_id = os.environ.get('GOOGLE_WALLET_CLASS_ID')
    
    if not issuer_id or not class_id:
        flash('Google Wallet pass is not configured. Please contact support.', 'danger')
        logging.error('GOOGLE_WALLET_ISSUER_ID or GOOGLE_WALLET_CLASS_ID not set in environment variables')
        return redirect(url_for('main.dashboard'))

    # Get credentials from environment variable (base64 encoded) or file
    credentials_base64 = os.environ.get('GOOGLE_WALLET_CREDENTIALS_BASE64')
    
    if credentials_base64:
        # Decode base64 credentials from environment variable
        try:
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            logging.info('Using Google Wallet credentials from environment variable')
        except Exception as e:
            flash('Error decoding Google Wallet credentials. Please contact support.', 'danger')
            logging.error(f'Error decoding base64 credentials: {str(e)}')
            return redirect(url_for('main.dashboard'))
    else:
        # Fallback to file-based credentials (for local development)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(base_dir, 'app', 'hotelsintloyalty-7343501665d7.json')
        
        if not os.path.exists(credentials_path):
            flash('Google Wallet credentials are not configured. Please contact support.', 'danger')
            logging.error(f'Missing credentials file: {credentials_path}')
            return redirect(url_for('main.dashboard'))
        
        with open(credentials_path, 'r') as f:
            credentials_dict = json.load(f)
        
        logging.info('Using Google Wallet credentials from file')

    try:
        # Create service account credentials
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
        )
        
        # Create authorized session
        http_client = AuthorizedSession(credentials)
        
        # First, ensure the loyalty class exists
        class_full_id = f"{issuer_id}.{class_id}"
        class_url = f'https://walletobjects.googleapis.com/walletobjects/v1/loyaltyClass/{class_full_id}'
        
        # Check if class exists
        class_response = http_client.get(class_url)
        
        if class_response.status_code == 404:
            # Class doesn't exist, create it
            loyalty_class = {
                'id': class_full_id,
                'issuerName': 'Hotels International',
                'programName': 'Hotels International Loyalty',
                'programLogo': {
                    'sourceUri': {
                        'uri': 'https://loyalty.hotelsinternational.co.uk/static/images/logo.png'
                    }
                },
                'hexBackgroundColor': '#1a1a1a',
                'reviewStatus': 'UNDER_REVIEW'
            }
            
            create_class_url = 'https://walletobjects.googleapis.com/walletobjects/v1/loyaltyClass'
            class_create_response = http_client.post(create_class_url, json=loyalty_class)
            
            if class_create_response.status_code not in [200, 201]:
                logging.error(f'Failed to create loyalty class: {class_create_response.status_code} - {class_create_response.text}')
                raise Exception(f'Failed to create loyalty class: {class_create_response.status_code}')
            
            logging.info(f'Created loyalty class: {class_full_id}')
        elif class_response.status_code == 200:
            logging.info(f'Loyalty class already exists: {class_full_id}')
        else:
            logging.error(f'Error checking loyalty class: {class_response.status_code} - {class_response.text}')
            raise Exception(f'Error checking loyalty class: {class_response.status_code}')
        
        # Create unique object ID for this customer
        object_id = f"{issuer_id}.{customer['CardNumber']}"
        
        # Customer name
        customer_name = f"{customer.get('Forename', '')} {customer.get('Surname', '')}".strip()
        
        # Define the loyalty object
        loyalty_object = {
            'id': object_id,
            'classId': f"{issuer_id}.{class_id}",
            'state': 'ACTIVE',
            'accountName': customer_name,
            'accountId': customer['CardNumber'],
            'barcode': {
                'type': 'QR_CODE',
                'value': customer['CardNumber']
            },
            'textModulesData': [
                {
                    'header': 'Name',
                    'body': customer_name,
                    'id': 'name'
                },
                {
                    'header': 'ID',
                    'body': customer['CardNumber'],
                    'id': 'customer_id'
                }
            ],
            'linksModuleData': {
                'uris': [
                    {
                        'uri': 'https://loyalty.hotelsinternational.co.uk',
                        'description': 'Check Your Balance'
                    }
                ]
            }
        }
        
        # Try to create or update the object
        object_url = f'https://walletobjects.googleapis.com/walletobjects/v1/loyaltyObject/{object_id}'
        
        # Try to get existing object first
        response = http_client.get(object_url)
        
        if response.status_code == 200:
            # Object exists, update it
            response = http_client.put(object_url, json=loyalty_object)
            logging.info(f'Updated existing Google Wallet pass for customer {customer.get("Id")}')
        elif response.status_code == 404:
            # Object doesn't exist, create it
            create_url = 'https://walletobjects.googleapis.com/walletobjects/v1/loyaltyObject'
            response = http_client.post(create_url, json=loyalty_object)
            logging.info(f'Created new Google Wallet pass for customer {customer.get("Id")}')
        else:
            raise Exception(f'Unexpected response: {response.status_code} - {response.text}')
        
        if response.status_code not in [200, 201]:
            raise Exception(f'Failed to create/update pass: {response.status_code} - {response.text}')
        
        # Generate the "Add to Google Wallet" link
        save_url = f'https://pay.google.com/gp/v/save/{object_id}'
        
        return redirect(save_url)
        
    except Exception as e:
        flash('Unable to generate your Google Wallet pass. Please try again later.', 'danger')
        logging.error(f'Error generating Google Wallet pass: {str(e)}', exc_info=True)
        return redirect(url_for('main.dashboard'))
