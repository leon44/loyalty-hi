# Mobile App Integration Guide

## Custom URL Scheme for Magic Links

The loyalty web app now supports custom URL schemes for in-app webview authentication.

### How It Works

When a user requests a magic link from within your iOS app's webview, the system will automatically detect this and generate a `loyaltyapp://` URL instead of an `https://` URL.

### Detection Methods

The backend detects in-app requests using either:

1. **Custom User-Agent**: Include `loyaltyapp` in the User-Agent string
2. **Custom Header**: Set `X-Requested-With: LoyaltyApp` header

### Implementation in Your iOS App

#### 1. Configure Custom User-Agent in WKWebView

```swift
import WebKit

let webView = WKWebView()
webView.customUserAgent = "LoyaltyApp/1.0 (iOS) Safari/\(UIWebView.userAgent ?? "")"
```

Or add a custom header:

```swift
var request = URLRequest(url: url)
request.setValue("LoyaltyApp", forHTTPHeaderField: "X-Requested-With")
webView.load(request)
```

#### 2. Register Custom URL Scheme

In your `Info.plist`, add:

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>loyaltyapp</string>
        </array>
        <key>CFBundleURLName</key>
        <string>co.uk.hotelsinternational.LoyaltyApp</string>
    </dict>
</array>
```

#### 3. Handle Custom URL Scheme

In your `AppDelegate.swift` or `SceneDelegate.swift`:

```swift
func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
    guard url.scheme == "loyaltyapp" else { return false }
    
    // Parse the URL
    // Format: loyaltyapp://auth/verify?token=YOUR_TOKEN
    
    if url.host == "auth" && url.path == "/verify" {
        if let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
           let token = components.queryItems?.first(where: { $0.name == "token" })?.value {
            
            // Navigate to verification URL in webview
            let verifyURL = URL(string: "https://loyalty.hotelsinternational.co.uk/login/verify/\(token)")!
            webView.load(URLRequest(url: verifyURL))
            
            return true
        }
    }
    
    return false
}
```

For SwiftUI with `@main` App:

```swift
import SwiftUI

@main
struct LoyaltyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onOpenURL { url in
                    handleCustomURL(url)
                }
        }
    }
    
    func handleCustomURL(_ url: URL) {
        guard url.scheme == "loyaltyapp" else { return }
        
        if url.host == "auth" && url.path == "/verify" {
            if let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
               let token = components.queryItems?.first(where: { $0.name == "token" })?.value {
                
                // Navigate to verification URL
                let verifyURL = URL(string: "https://loyalty.hotelsinternational.co.uk/login/verify/\(token)")!
                // Load in your webview
            }
        }
    }
}
```

### URL Format

**In-App Magic Link:**
```
loyaltyapp://auth/verify?token=MAGIC_TOKEN_HERE
```

**Web Magic Link (fallback):**
```
https://loyalty.hotelsinternational.co.uk/login/verify/MAGIC_TOKEN_HERE
```

### Testing

1. **Test in-app detection:**
   - Open the login page in your app's webview with custom User-Agent
   - Request a magic link
   - Check your email - the link should start with `loyaltyapp://`

2. **Test URL handling:**
   - Click the magic link in your email app
   - Your app should open and handle the URL
   - The webview should navigate to the verification endpoint
   - User should be logged in

3. **Test web fallback:**
   - Open the login page in Safari (not in-app)
   - Request a magic link
   - The link should be a standard `https://` URL

### Debugging

Check the server logs for:
```
Generated in-app magic link for user@example.com
```

This confirms the in-app detection is working.

### Security Notes

- The token is still validated server-side
- Tokens expire after 15 minutes
- Tokens can only be used once
- Rate limiting is still enforced
- The custom URL scheme doesn't bypass any security measures

### Alternative: Universal Links

If you prefer to use Universal Links instead, the configuration is already in place at:
```
https://loyalty.hotelsinternational.co.uk/.well-known/apple-app-site-association
```

However, the custom URL scheme approach (`loyaltyapp://`) is more reliable for in-app webviews.
