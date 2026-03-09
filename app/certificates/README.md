# Apple Wallet Pass Certificates

This directory contains the certificates required to sign Apple Wallet passes.

## Required Files

Place the following PEM files in this directory:

- `pass_cert.pem` - Your Pass Type ID certificate
- `pass_key.pem` - Your Pass Type ID private key
- `wwdr.pem` - Apple Worldwide Developer Relations certificate

## Setup Instructions

See the main `WALLET_SETUP_GUIDE.md` in the project root for complete setup instructions.

## Security

**IMPORTANT**: These files contain sensitive cryptographic keys and should NEVER be committed to version control.

This directory is already included in `.gitignore` to prevent accidental commits.
