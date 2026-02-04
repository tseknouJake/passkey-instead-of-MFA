# MFA vs Passkey Authentication Comparison

A Flask web application comparing two authentication methods:
- **MFA (Multi-Factor Authentication)**: Traditional password + TOTP codes
- **Passkey**: Modern passwordless authentication with biometrics

## Features

### 📱 MFA Path
- Username + Password
- Authenticator app setup (Google Authenticator, Authy, etc.)
- Time-based codes (TOTP)
- Works on any device

### 🔑 Passkey Path
- **Passwordless** - No password needed!
- **Biometric** - Touch ID, Face ID, Windows Hello
- **Faster** - Login in ~2 seconds
- **More Secure** - Phishing-resistant, keys never leave device

## Requirements

- Python 3.7+
- Modern browser supporting WebAuthn (Chrome, Safari, Firefox, Edge)
- macOS with Touch ID, Windows Hello, or Android/iOS device

## Installation

```bash
# Clone/download the repo
cd passkey-instead-of-mfa

# Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
python app.py
```

The app will start on **https://localhost:5000** (HTTPS required for passkeys)

⚠️ Your browser will warn about the self-signed certificate. Click "Advanced" → "Proceed" (safe for local development)

## Usage

### Try MFA Authentication

1. Go to https://localhost:5000
2. Click "Login with MFA"
3. Enter credentials (demo: `admin` / `password123`)
4. Scan QR code with authenticator app
5. Enter the 6-digit code

### Try Passkey Authentication

1. Go to https://localhost:5000
2. Click "Login with Passkey"
3. Click "Register a new passkey"
4. Enter credentials (demo: `admin` / `password123`)
5. Use your fingerprint/Face ID when prompted
6. Done! Next login takes ~2 seconds

## Comparison

| Feature | MFA | Passkey |
|---------|-----|---------|
| Passwordless | ❌ | ✅ |
| Biometric | ❌ | ✅ |
| Phishing-Resistant | Partial | ✅ |
| Setup Time | ~30 seconds | ~10 seconds |
| Login Speed | ~10 seconds | ~2 seconds |
| App Required | ✅ (Authenticator) | ❌ |

## How It Works

### MFA (TOTP)
- Uses **PyOTP** to generate time-based codes
- Secret stored on server, synced with authenticator app
- New 6-digit code every 30 seconds

### Passkey (WebAuthn)
- Uses **Web Authentication API** (WebAuthn)
- Private key stored in device's **Secure Enclave** (never transmitted)
- Public key stored on server
- Biometric verification proves you own the device

## Project Structure

```
passkey-instead-of-mfa/
├── app.py                      # Flask backend
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── templates/
    ├── index.html              # Landing page
    ├── mfa_login.html          # MFA login
    ├── setup_mfa.html          # MFA setup
    ├── verify_mfa.html         # MFA verification
    ├── passkey_login.html      # Passkey login
    ├── passkey_register.html   # Passkey registration
    └── dashboard.html          # Protected page
```

## Demo Credentials

- Username: `admin`
- Password: `password123`

## Security Notes

⚠️ **This is a demonstration app!**

For production use:
- Use a real database (not in-memory)
- Hash passwords with bcrypt
- Store MFA secrets encrypted
- Use proper certificate (not self-signed)
- Implement rate limiting
- Add CSRF protection
- Verify passkey assertions properly
- Add account recovery flows

## Why Passkeys Are Better

1. **No Passwords** - Nothing to remember, leak, or phish
2. **Phishing-Proof** - Keys are domain-bound
3. **Faster** - 2 seconds vs 10+ seconds
4. **User-Friendly** - Same biometric you use to unlock device
5. **More Secure** - Private keys never leave device

## Browser Support

Passkeys work in:
- ✅ Chrome 67+
- ✅ Safari 13+
- ✅ Firefox 60+
- ✅ Edge 18+

## Troubleshooting

**"Passkey not working"**
- Ensure you're using HTTPS (even localhost must be https://)
- Check browser supports WebAuthn
- Ensure biometrics are set up on your device

**"Certificate warning"**
- Normal for self-signed certs
- Click "Advanced" → "Proceed to localhost"

**"Touch ID not prompted"**
- Make sure Touch ID is enabled in System Preferences
- Try Chrome/Safari (best support on macOS)

## Learn More

- [WebAuthn Guide](https://webauthn.guide/)
- [FIDO Alliance](https://fidoalliance.org/)
- [Passkeys.dev](https://passkeys.dev/)

## License

Free to use for learning and demonstration purposes.
