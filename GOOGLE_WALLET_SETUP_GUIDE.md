# Google Wallet Pass Setup Guide

## What You Have
- ✅ Issuer ID: `3388000000023094154`
- ✅ Class ID: `hotelsInternationalLoyalty`

## What You Need: Service Account JSON Key

### Step 1: Create a Service Account

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project (or create one if you haven't)

2. **Navigate to Service Accounts**
   - In the left menu, go to: **IAM & Admin** → **Service Accounts**
   - Or use this direct link: https://console.cloud.google.com/iam-admin/serviceaccounts

3. **Create Service Account**
   - Click **"+ CREATE SERVICE ACCOUNT"** at the top
   - Fill in the details:
     - **Service account name**: `wallet-pass-service`
     - **Service account ID**: `wallet-pass-service` (auto-filled)
     - **Description**: `Service account for generating Google Wallet passes`
   - Click **"CREATE AND CONTINUE"**

4. **Grant Permissions**
   - In the "Grant this service account access to project" section:
   - Click **"Select a role"** dropdown
   - Search for and select: **"Owner"** (or at minimum "Google Wallet API Admin")
   - Click **"CONTINUE"**
   - Click **"DONE"**

### Step 2: Download the JSON Key File

1. **Find Your Service Account**
   - You should see your new service account in the list
   - Click on the **email address** of the service account (e.g., `wallet-pass-service@your-project.iam.gserviceaccount.com`)

2. **Create a Key**
   - Click the **"KEYS"** tab at the top
   - Click **"ADD KEY"** → **"Create new key"**
   - Select **"JSON"** as the key type
   - Click **"CREATE"**

3. **Save the File**
   - A JSON file will automatically download to your computer
   - It will be named something like: `your-project-123456-abc123def456.json`
   - **IMPORTANT**: Keep this file secure! It's like a password for your Google Cloud account

4. **Move the File**
   - Save it somewhere safe on your computer
   - You'll provide this to me, and we'll encode it as a base64 environment variable (just like the Apple certificates)

### Step 3: Enable Google Wallet API

1. **Go to APIs & Services**
   - In Google Cloud Console, go to: **APIs & Services** → **Library**
   - Or use this link: https://console.cloud.google.com/apis/library

2. **Search for Google Wallet API**
   - In the search box, type: `Google Wallet API`
   - Click on **"Google Wallet API"**

3. **Enable the API**
   - Click **"ENABLE"** button
   - Wait a few seconds for it to activate

### Step 4: Verify Your Setup

You should now have:
- ✅ Issuer ID: `3388000000023094154`
- ✅ Class ID: `hotelsInternationalLoyalty`
- ✅ Service Account created
- ✅ JSON key file downloaded
- ✅ Google Wallet API enabled

## Next Steps

Once you have the JSON key file:
1. Let me know you have it
2. I'll create a script to encode it (like we did for Apple certificates)
3. We'll add it as an environment variable
4. I'll implement the Google Wallet pass generation
5. We'll add the "Add to Google Wallet" button next to the Apple one

## Security Notes

- **Never commit the JSON key file to git** - we'll add it to `.gitignore`
- **Never share the JSON key publicly** - it gives full access to your Google Cloud project
- Store it securely and back it up
- We'll encode it as base64 for production deployment (same approach as Apple certificates)

## Troubleshooting

### "Permission denied" errors
- Make sure you granted the service account the correct role (Owner or Google Wallet API Admin)
- Wait a few minutes after creating the service account for permissions to propagate

### Can't find Google Wallet API
- Make sure you're in the correct Google Cloud project
- The API might be called "Google Pay API" in some regions

### JSON key download didn't work
- Try a different browser
- Make sure pop-ups are not blocked
- You can create multiple keys if needed (and delete old ones)
