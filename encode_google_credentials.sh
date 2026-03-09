#!/bin/bash
# Script to encode Google Wallet service account JSON as base64 for environment variables

echo "Encoding Google Wallet service account JSON to base64..."
echo ""
echo "Add this to your .env file (or production environment variables):"
echo ""

echo "# Google Wallet Service Account (base64 encoded)"
echo "GOOGLE_WALLET_CREDENTIALS_BASE64=\"$(base64 -i app/hotelsintloyalty-7343501665d7.json | tr -d '\n')\""
echo ""
echo "Done! Copy the above line to your .env file or production environment."
