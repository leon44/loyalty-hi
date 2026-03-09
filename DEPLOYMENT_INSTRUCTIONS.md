# Deployment Instructions for Digital Ocean

## Quick Deployment Steps

### 1. Encode Your Certificates

Run the encoding script to get base64-encoded certificates:

```bash
./encode_certificates.sh
```

This will output three environment variables. Copy them - you'll need them for step 3.

### 2. Commit and Push Your Code

```bash
git add .
git commit -m "Add Apple Wallet pass generation feature"
git push origin main
```

### 3. Set Environment Variables in Digital Ocean

In your Digital Ocean app settings, add these environment variables:

**Required for Apple Wallet:**
- `APPLE_TEAM_ID` - Your Apple Developer Team ID (10 characters)
- `PASS_TYPE_ID` - Your Pass Type ID (e.g., `pass.com.hotelsinternational.loyalty`)
- `PASS_CERT_BASE64` - From encode_certificates.sh output
- `PASS_KEY_BASE64` - From encode_certificates.sh output
- `WWDR_CERT_BASE64` - From encode_certificates.sh output

**Optional (leave empty/unset if using unencrypted key):**
- `PASS_CERT_PASSWORD` - Only if you encrypted your private key

**Existing environment variables (make sure these are still set):**
- `SECRET_KEY`
- `DATABASE_URL`
- `EPOS_API_KEY`
- `EPOS_API_SECRET`
- `MJ_APIKEY_PUBLIC`
- `MJ_APIKEY_PRIVATE`

### 4. Deploy

Digital Ocean should automatically deploy when you push to your main branch. If not, trigger a manual deployment from the Digital Ocean dashboard.

### 5. Verify

Once deployed:
1. Visit your production site
2. Log in to the customer portal
3. Click "Add to Apple Wallet"
4. The `.pkpass` file should download
5. Open it on your iPhone or Mac to verify it works

## How It Works

The application now supports **two modes** for certificates:

### Production Mode (Environment Variables)
- If `PASS_CERT_BASE64`, `PASS_KEY_BASE64`, and `WWDR_CERT_BASE64` are set
- Certificates are decoded from base64 and written to temporary files
- Perfect for platforms like Digital Ocean, Heroku, etc.

### Development Mode (Local Files)
- If environment variables are NOT set
- Reads certificates from `app/certificates/` directory
- Perfect for local development

## Troubleshooting

### "Apple Wallet pass is not configured"
- Check that `APPLE_TEAM_ID` and `PASS_TYPE_ID` are set in production environment
- Verify they match your Apple Developer account settings

### "Error decoding certificates"
- Verify the base64 strings were copied completely (they're very long)
- Make sure there are no extra spaces or line breaks
- Re-run `./encode_certificates.sh` and copy fresh values

### "Unable to generate your wallet pass"
- Check application logs for detailed error messages
- Verify the Pass Type ID matches exactly between Apple Developer Portal and environment variable
- Ensure certificates haven't expired (valid for 1 year)

### Pass downloads but won't open on iPhone
- The certificate must be valid and not expired
- The Pass Type ID must match the certificate
- Try opening on a Mac first for better error messages

## Security Notes

- The base64-encoded certificates in environment variables are still sensitive
- Never commit them to git or share them publicly
- Rotate certificates before they expire
- Keep your `.p12` file backed up securely

## Need Help?

Check the logs in your Digital Ocean dashboard for detailed error messages. The application logs will show:
- Whether it's using environment variables or files
- Any certificate decoding errors
- Pass generation errors with stack traces
