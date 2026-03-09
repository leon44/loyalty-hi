#!/bin/bash
# Script to encode Apple Wallet certificates as base64 for environment variables

echo "Encoding certificates to base64..."
echo ""
echo "Add these to your .env file (or production environment variables):"
echo ""

echo "# Apple Wallet Pass Certificates (base64 encoded)"
echo "PASS_CERT_BASE64=\"$(base64 -i app/certificates/pass_cert.pem | tr -d '\n')\""
echo ""
echo "PASS_KEY_BASE64=\"$(base64 -i app/certificates/pass_key.pem | tr -d '\n')\""
echo ""
echo "WWDR_CERT_BASE64=\"$(base64 -i app/certificates/wwdr.pem | tr -d '\n')\""
echo ""
echo "Done! Copy the above lines to your .env file or production environment."
