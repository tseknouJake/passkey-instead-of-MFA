# MFA vs Passkey Authentication Comparison

A Flask web application comparing two authentication methods:
- **MFA (Multi-Factor Authentication)**: Traditional password + TOTP codes
- **Passkey**: Modern passwordless authentication with biometrics

## ✨ Features

### 📱 MFA Path
- Username + Password
- Authenticator app setup (Google Authenticator, Authy, etc.)
- Time-based 6-digit codes (TOTP)
- Works on any device
- ~10 second login time

### 🔑 Passkey Path
- **Passwordless** - No password needed!
- **Biometric** - Touch ID, Face ID, Windows Hello
- **Faster** - Login in ~2 seconds
- **More Secure** - Phishing-resistant, keys never leave device
- Device-bound authentication

### 🆕 New Features
- **User Registration** - Create your own accounts
- **Encrypted Storage** - Passwords and MFA secrets encrypted with Fernet
- **Dynamic Auth Choice** - Choose MFA or Passkey after registration
- **Persistent Data** - Credentials saved across server restarts

## Requirements

- Python 3.7+
- Modern browser supporting WebAuthn (Chrome, Safari, Firefox, Edge)
- macOS with Touch ID, Windows Hello, or Android/iOS device

## Installation

```bash
# Navigate to project directory
cd passkey-instead-of-mfa

# Install dependencies
pip install -r requirements.txt
```

Dependencies installed:
- `Flask` - Web framework
- `pyotp` - TOTP code generation
- `qrcode` - QR code generation for MFA
- `pyOpenSSL` - SSL/TLS for HTTPS
- `cryptography` - Fernet encryption for data at rest

## Running the App

```bash
python3 app.py
```

The app will start on **https://localhost:5000** (HTTPS required for passkeys)

On first run, the app will automatically:
- Generate an encryption key (`encryption.key`)
- Create an empty encrypted database (`users.json`)

⚠️ Your browser will warn about the self-signed certificate. Click "Advanced" → "Proceed to localhost" (safe for local development)

## Usage

### Register a New Account

1. Go to https://localhost:5000
2. Click **"Create Account"** button at the bottom
3. Enter username and password (minimum 8 characters)
4. Confirm password
5. Click "Create Account"
6. Choose authentication method:
   - **Setup MFA** - Scan QR code with authenticator app
   - **Register Passkey** - Use Touch ID/biometric
   - **Skip for now** - Set up later

### Login with MFA

1. Click "Login with MFA"
2. Enter username and password
3. If first time: Scan QR code with authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
4. Enter the 6-digit code from your app
5. Access dashboard

### Login with Passkey

1. Click "Login with Passkey"
2. Enter username
3. If first time: Click "Register a new passkey", enter password, use Touch ID
4. If already registered: Just use Touch ID
5. Access dashboard in ~2 seconds!

## Feature Comparison

| Feature | MFA | Passkey |
|---------|-----|---------|
| Passwordless | ❌ | ✅ |
| Biometric | ❌ | ✅ |
| Phishing-Resistant | Partial | ✅ |
| Setup Time | ~30 seconds | ~10 seconds |
| Login Speed | ~10 seconds | ~2 seconds |
| App Required | ✅ (Authenticator) | ❌ |
| Works Offline | ❌ (needs time sync) | ✅ |
| Device-Bound | ❌ | ✅ |

## How It Works

### MFA (TOTP)
- Uses **PyOTP** to generate time-based codes
- MFA secret encrypted and stored on server
- Secret synced with authenticator app via QR code
- New 6-digit code generated every 30 seconds
- Time-window validation (±30 seconds)

### Passkey (WebAuthn)
- Uses **Web Authentication API** (WebAuthn standard)
- Private key stored in device's **Secure Enclave** (never transmitted)
- Public key stored on server
- Challenge-response authentication
- Biometric verification proves you own the device
- Domain-bound (phishing-resistant)

### Encryption
- **Fernet symmetric encryption** (AES-128 in CBC mode)
- Passwords encrypted at rest
- MFA secrets encrypted at rest
- Encryption key stored in `encryption.key`
- Transparent encryption/decryption

## Project Structure

```
passkey-instead-of-mfa/
├── app.py                      # Flask backend with all routes
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── encryption.key              # Fernet encryption key (auto-generated)
├── users.json                  # Encrypted user database
└── templates/
    ├── index.html              # Landing page with comparison
    ├── register.html           # User registration form
    ├── setup_choice.html       # Choose auth method
    ├── mfa_login.html          # MFA login page
    ├── setup_mfa.html          # MFA QR code setup
    ├── verify_mfa.html         # MFA code verification
    ├── passkey_login.html      # Passkey login page
    ├── passkey_register.html   # Passkey registration
    └── dashboard.html          # Protected page (shows auth method)
```

## File Descriptions

### Core Files
- **app.py** - Flask application with encryption, MFA, and Passkey routes
- **encryption.key** - Fernet key for encrypting sensitive data (keep secret!)
- **users.json** - Encrypted user database with passwords, MFA secrets, and passkey credentials

### Templates
All HTML templates use modern CSS with gradient backgrounds and responsive design.

## Security Features

✅ **Encrypted Storage** - Passwords and MFA secrets encrypted with Fernet  
✅ **HTTPS Only** - SSL/TLS for all connections  
✅ **Session Management** - Secure Flask sessions  
✅ **Phishing-Resistant** - Passkeys are domain-bound  
✅ **No Password Transmission** - Passkeys use public-key cryptography  
✅ **Biometric Verification** - Device's secure enclave  

## Security Notes

⚠️ **This is a demonstration app for learning purposes!**

For production use, implement:
- ✅ Use a real database (PostgreSQL, MySQL, MongoDB)
- ✅ Hash passwords with bcrypt/argon2 (not just encryption)
- ✅ Store encryption keys in environment variables or key management service
- ✅ Use proper SSL certificates (Let's Encrypt)
- ✅ Implement rate limiting (Flask-Limiter)
- ✅ Add CSRF protection (Flask-WTF)
- ✅ Verify passkey assertions cryptographically
- ✅ Add account recovery flows
- ✅ Implement session timeout
- ✅ Add audit logging
- ✅ Use environment variables for secrets

## Why Passkeys Are Better

1. **No Passwords** - Nothing to remember, leak, or phish
2. **Phishing-Proof** - Keys are domain-bound, can't be used on fake sites
3. **Faster** - 2 seconds vs 10+ seconds for login
4. **User-Friendly** - Same biometric you already use to unlock device
5. **More Secure** - Private keys never leave device's secure hardware
6. **No SMS** - Not vulnerable to SIM swapping attacks
7. **Offline Capable** - Works without internet connection
8. **Cross-Device** - Can sync via iCloud Keychain, etc.

## Browser Support

Passkeys work in:
- ✅ Chrome 67+ (all platforms)
- ✅ Safari 13+ (macOS, iOS)
- ✅ Firefox 60+ (all platforms)
- ✅ Edge 18+ (Windows, macOS)

## Troubleshooting

### "Passkey not working"
- Ensure you're using **https://localhost:5000** (not http://)
- Check browser supports WebAuthn
- Ensure biometrics are set up on your device
- Try using **localhost** instead of **127.0.0.1** in URL

### "Certificate warning"
- Normal for self-signed certificates in development
- Click "Advanced" → "Proceed to localhost (unsafe)"
- This is safe for local development only

### "Touch ID not prompted"
- Verify Touch ID is enabled in System Preferences (macOS)
- Try Chrome or Safari (best WebAuthn support on macOS)
- Ensure your device has biometric hardware

### "cryptography.fernet.InvalidToken error"
- You have an old plaintext users.json file
- **Solution**: Delete or rename it: `mv users.json users.json.backup`
- Restart the app - it will create a fresh encrypted database
- Use the registration form to create new accounts

### "Could not build url for endpoint"
- Your app.py is missing routes
- Make sure you're using the latest version of app.py
- Check that all routes are defined

## Important Files to Keep Secret

Add to `.gitignore`:
```
encryption.key
users.json
*.pyc
__pycache__/
.DS_Store
```

**Never commit these files to version control!**

## Data Format

### Plaintext (in memory)
```json
{
    "username": {
        "password": "password123",
        "mfa_secret": "JBSWY3DPEHPK3PXP",
        "passkey_credentials": [...]
    }
}
```

### Encrypted (in users.json)
```json
{
    "username": {
        "password": "gAAAAABl...",
        "mfa_secret": "gAAAAABl...",
        "passkey_credentials": [...]
    }
}
```

## Learn More

### WebAuthn & Passkeys
- [WebAuthn Guide](https://webauthn.guide/) - Interactive guide
- [FIDO Alliance](https://fidoalliance.org/) - Standards body
- [Passkeys.dev](https://passkeys.dev/) - Implementation guides
- [WebAuthn.io](https://webauthn.io/) - Demo and tools

### Security & Cryptography
- [Fernet Specification](https://github.com/fernet/spec/) - Encryption details
- [OWASP Authentication](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/README) - Best practices

## Development

### Adding New Users Programmatically
```python
from app import users, save_users

users['newuser'] = {
    'password': 'securepassword',
    'mfa_secret': None,
    'passkey_credentials': []
}
save_users(users)
```

### Checking Encrypted Data
```python
import json
with open('users.json', 'r') as f:
    print(json.dumps(json.load(f), indent=2))
```

## License

Free to use for learning and demonstration purposes.

## Contributing

This is a demonstration project. Feel free to fork and modify for your own learning!

## Credits

Built with:
- Flask - Web framework
- PyOTP - TOTP implementation
- Cryptography - Fernet encryption
- WebAuthn API - Passkey standard

---

**Made with ❤️ to demonstrate modern authentication methods**
