# Apple Wallet Pass Setup Guide

This guide will help you configure Apple Wallet pass generation for the Hotels International Loyalty app.

## Prerequisites

- Apple Developer Account (paid membership required)
- macOS with Keychain Access
- OpenSSL installed (comes with macOS)

## Step 1: Apple Developer Portal Setup

### 1.1 Get Your Team ID

1. Go to [Apple Developer Account](https://developer.apple.com/account)
2. Sign in with your Apple ID
3. Your **Team ID** is displayed in the top right corner (10 characters, e.g., `A1B2C3D4E5`)
4. Save this for later

### 1.2 Create a Pass Type ID

1. Go to [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/identifiers/list)
2. Click the **+** button
3. Select **Pass Type IDs** and click Continue
4. Enter a description: `Hotels International Loyalty Pass`
5. Enter an identifier: `pass.com.hotelsinternational.loyalty`
   - Use reverse domain notation
   - Must be unique
6. Click **Register**

## Step 2: Generate Certificate Signing Request (CSR)

1. Open **Keychain Access** on your Mac
2. Go to **Keychain Access** → **Certificate Assistant** → **Request a Certificate From a Certificate Authority**
3. Fill in the form:
   - **User Email Address**: Your email
   - **Common Name**: `Hotels International Pass Signing`
   - **CA Email Address**: Leave blank
   - **Request is**: Select **Saved to disk**
4. Click **Continue** and save the `.certSigningRequest` file

## Step 3: Create Pass Type ID Certificate

1. Go to [Certificates](https://developer.apple.com/account/resources/certificates/list) in Apple Developer Portal
2. Click the **+** button
3. Select **Services** → **Pass Type ID Certificate**
4. Click **Continue**
5. Select your Pass Type ID: `pass.com.hotelsinternational.loyalty`
6. Click **Continue**
7. Upload the `.certSigningRequest` file you created in Step 2
8. Click **Continue**
9. Download the certificate (`.cer` file)

## Step 4: Export Certificate as .p12

1. Double-click the downloaded `.cer` file to add it to Keychain Access
2. In Keychain Access, find the certificate under **My Certificates**
   - It should be named something like "Pass Type ID: pass.com.hotelsinternational.loyalty"
3. Right-click the certificate and select **Export**
4. Choose file format: **Personal Information Exchange (.p12)**
5. Save as `pass_certificate.p12`
6. **Set a password** when prompted (you'll need this later)
7. Save this file securely

## Step 5: Download Apple WWDR Certificate

1. Go to [Apple PKI](https://www.apple.com/certificateauthority/)
2. Download **Worldwide Developer Relations - G4** certificate
3. The file will be named something like `AppleWWDRCAG4.cer`

## Step 6: Convert Certificates to PEM Format

Open Terminal and navigate to your project directory:

```bash
cd /Users/leonm/CascadeProjects/LoyaltyHI
```

Run these commands to convert the certificates:

```bash
# Convert .p12 to certificate PEM (enter the password you set in Step 4)
openssl pkcs12 -in pass_certificate.p12 -out app/certificates/pass_cert.pem -clcerts -nokeys

# Convert .p12 to key PEM (enter the password you set in Step 4)
# NOTE: The -nodes flag exports the key WITHOUT encryption
openssl pkcs12 -in pass_certificate.p12 -out app/certificates/pass_key.pem -nocerts -nodes

# Convert WWDR certificate to PEM
openssl x509 -inform DER -in AppleWWDRCAG4.cer -out app/certificates/wwdr.pem
```

**IMPORTANT:** The `-nodes` flag in the key export command means the private key will be **unencrypted**. This is the recommended approach for this implementation. Do NOT set `PASS_CERT_PASSWORD` in your `.env` file if you use `-nodes`.

## Step 7: Create Pass Assets (Images)

You need to create icon and logo images for the pass. These should match your brand.

### Required Files

Place these in `app/static/pass_assets/`:

**Icons** (square, no transparency):
- `icon.png` - 29×29 px
- `icon@2x.png` - 58×58 px
- `icon@3x.png` - 87×87 px

**Logos** (rectangular, can have transparency):
- `logo.png` - 160×50 px (recommended)
- `logo@2x.png` - 320×100 px
- `logo@3x.png` - 480×150 px

### Creating Assets from Existing Logo

You can use your existing logo and resize it:

```bash
# If you have ImageMagick installed:
# For icons (square, cropped):
convert app/static/images/logo.png -resize 29x29^ -gravity center -extent 29x29 app/static/pass_assets/icon.png
convert app/static/images/logo.png -resize 58x58^ -gravity center -extent 58x58 app/static/pass_assets/icon@2x.png
convert app/static/images/logo.png -resize 87x87^ -gravity center -extent 87x87 app/static/pass_assets/icon@3x.png

# For logos (rectangular):
convert app/static/images/logo.png -resize 160x50 app/static/pass_assets/logo.png
convert app/static/images/logo.png -resize 320x100 app/static/pass_assets/logo@2x.png
convert app/static/images/logo.png -resize 480x150 app/static/pass_assets/logo@3x.png
```

Or use any image editing software (Photoshop, GIMP, Preview, etc.)

## Step 8: Configure Environment Variables

Add these to your `.env` file:

```bash
# Apple Wallet Pass Configuration
APPLE_TEAM_ID=YOUR_TEAM_ID_HERE
PASS_TYPE_ID=pass.com.hotelsinternational.loyalty
# PASS_CERT_PASSWORD=  # Leave empty or omit if you used -nodes flag (recommended)
```

Replace:
- `YOUR_TEAM_ID_HERE` with your Team ID from Step 1.1

**About PASS_CERT_PASSWORD:**
- If you exported the key with `-nodes` flag (recommended in Step 6), **leave this empty or comment it out**
- Only set a password here if you exported the key WITH encryption (without `-nodes` flag)
- An empty value or no value means the key is unencrypted

## Step 9: Verify Setup

Check that all files are in place:

```bash
# Check certificates
ls -la app/certificates/
# Should show: pass_cert.pem, pass_key.pem, wwdr.pem

# Check assets
ls -la app/static/pass_assets/
# Should show: icon.png, icon@2x.png, icon@3x.png, logo.png, logo@2x.png, logo@3x.png
```

## Step 10: Test

1. Restart your Flask application
2. Log in to the customer portal
3. Click **Add to Apple Wallet**
4. The `.pkpass` file should download
5. Open it on your iPhone or Mac to add to Wallet

## Troubleshooting

### "Apple Wallet pass is not configured"
- Check that `APPLE_TEAM_ID` and `PASS_TYPE_ID` are set in `.env`
- Restart the Flask app after updating `.env`

### "Apple Wallet certificates are not configured"
- Verify all three certificate files exist in `app/certificates/`
- Check file permissions: `chmod 644 app/certificates/*.pem`

### "Unable to generate your wallet pass"
- Check the Flask logs for detailed error messages
- Verify the certificate password is correct in `.env`
- Ensure the Pass Type ID matches exactly between Apple Developer Portal and `.env`

### Pass won't open on iPhone
- The certificate must be valid and not expired
- The Pass Type ID in the code must match the certificate
- Try opening on a Mac first for better error messages

## Security Notes

- **Never commit certificates to git** - they are already in `.gitignore`
- **Never commit `.env` file** - it contains sensitive passwords
- Keep your `.p12` file secure and backed up
- Rotate certificates before they expire (they're valid for 1 year)

## Production Deployment

### Option 1: Base64-Encoded Certificates (Recommended for Digital Ocean, Heroku, etc.)

If your hosting platform doesn't allow file uploads or you prefer environment variables:

1. **Encode your certificates to base64:**
   ```bash
   ./encode_certificates.sh
   ```
   This will output three environment variables with your certificates encoded.

2. **Copy the output and add to your production environment variables:**
   - `PASS_CERT_BASE64`
   - `PASS_KEY_BASE64`
   - `WWDR_CERT_BASE64`

3. **Also set these environment variables:**
   - `APPLE_TEAM_ID`
   - `PASS_TYPE_ID`
   - Leave `PASS_CERT_PASSWORD` empty/unset if using unencrypted key

4. **Deploy your code:**
   ```bash
   git add .
   git commit -m "Add Apple Wallet pass generation"
   git push origin main
   ```

The application will automatically detect and use the base64-encoded certificates from environment variables.

### Option 2: File-Based Certificates (For servers with file system access)

When deploying to production (e.g., VPS, dedicated server):

1. Upload certificate files securely to your server
2. Set environment variables in your hosting platform
3. Ensure file paths are correct for your production environment
4. Test thoroughly before going live

## Support

If you encounter issues:
1. Check the Flask application logs
2. Verify all steps in this guide
3. Consult [Apple's Wallet Developer Guide](https://developer.apple.com/wallet/)
