import os
import requests
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EposNowClient:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key or os.environ.get('EPOS_API_KEY')
        self.api_secret = api_secret or os.environ.get('EPOS_API_SECRET')
        self.base_url = 'https://api.eposnowhq.com/api/v4'
        self.access_token = self._generate_access_token()

    def _generate_access_token(self):
        if not self.api_key or not self.api_secret:
            logging.error('EPOS Now API key or secret not configured.')
            raise ValueError('EPOS Now API credentials are not set.')
        
        token_string = f"{self.api_key}:{self.api_secret}"
        return base64.b64encode(token_string.encode('utf-8')).decode('utf-8')

    def _make_request(self, method, endpoint, **kwargs):
        headers = {
            'Authorization': f'Basic {self.access_token}',
            'Content-Type': 'application/json'
        }
        url = f'{self.base_url}/{endpoint}'
        print(url)
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            print(response.text)
            response.raise_for_status()
            print(response.text)
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f'HTTP error calling EPOS Now API: {e.response.status_code} {e.response.text}')
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f'Error calling EPOS Now API: {e}')
            raise

    def get_customer_by_email(self, email):
        """Fetches a customer by their email address."""
        endpoint = 'Customer/GetByEmail'
        try:
            # The API might return a list or a single object. Let's assume a list.
            customers = self._make_request(
                'GET',
                endpoint,
                params={'email': email}   # 👈 THIS is the key change
            )

            if not customers:
                return None
            if isinstance(customers, list):
                return customers[0] if customers else None
            return customers
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None # Customer not found is not an error in this context
            raise

    def update_customer(self, data):
        """
        Updates a customer's details. The API requires the full customer object.
        The API expects an array of customers for this endpoint.
        """
        endpoint = 'Customer'
        try:
            # The API expects a list of customers, even for a single update.
            return self._make_request('PUT', endpoint, json=[data])
        except Exception as e:
            customer_id = data.get('Id', 'N/A')
            logging.error(f'Failed to update customer {customer_id}: {e}')
            raise

    def create_customer(self, data):
        """
        Creates a new customer.
        The EPOS Now API expects an array of customers for this endpoint.
        """
        endpoint = 'Customer'
        try:
            # The API expects a list of customers, even for a single creation.
            response_data = self._make_request('POST', endpoint, json=[data])
            # The response is also a list containing the created customer(s).
            if response_data and isinstance(response_data, list):
                return response_data[0]
            return None
        except Exception as e:
            logging.error(f'Failed to create customer: {e}')
            raise


