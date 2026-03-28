# Authentication comparison

A Flask web application comparing several authentication methods:
- **MFA (Multi-Factor Authentication)**: Traditional password + TOTP codes
- **Passkey**: Modern passwordless authentication with biometrics
- **Social login**: Single Sign-On with Google account
- **Classic authentication**: Traditional username and password

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
- `gunicorn` - python web app deployment
- `subabase` - PostgreSQL
- `python-dotenv` - reading `.env` file
- `AuthLib` - OAuth for social login
- `requests` - allows GET and POST

## Running the App

For a successful experience, you need the following environment variables:
```
FERNET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
SUPABASE_KEY=
SUPABASE_URL=
```
- If you don't have the environment variables, you can check the deployed version: https://project2-2-group10-2026.onrender.com

- If you have acquired them, you can run the app with the command:
```bash
python3 app.py
```

The app will start on **https://localhost:5001**
AND **https://127.0.0.1:5001**
AND **https://192.168.1.150:5001**

 Your browser will warn about the self-signed certificate. Click "Advanced" → "Proceed to localhost" (safe for local development)

The app can also be run with the command
```bash
gunicorn app:app
```

Then the app will start on **http://127.0.0.1:8000**

⚠️ **Currently, all the features can be accessed on any of those ports, except for social login, which will be set up 
later. To access the full functionality set, see the deployed version: https://project2-2-group10-2026.onrender.com**


## Usage

### Register a New Account

1. Go to https://project2-2-group10-2026.onrender.com (OR any of the locally running hosts)
2. Click **"Create Account"** button at the bottom
3. Enter username and password (minimum 8 characters)
4. Confirm password
5. Click "Create Account"
6. Choose authentication method:
   - **Setup MFA** - Scan QR code with authenticator app
   - **Register Passkey** - Use Touch ID/biometric
   - **Link Google** - Choose a Google account
   - **Skip for now** - Set up later

### Login with MFA

1. Click "Login with MFA"
2. Enter username and password
3. If first time: Scan QR code with authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
4. Enter the 6-digit code from your app
5. Access questionnaire

### Login with Passkey

1. Click "Login with Passkey"
2. Enter username
3. If first time: Click "Register a new passkey", enter password, use Touch ID
4. If already registered: Just use Touch ID
5. Access questionnaire

### Login with Socials
1. Click "Login with Google"
2. Click "Continue with Google"
3. Select your Google account
4. If first time: set up a password
5. Access questionnaire

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

### Social Login (AuthLib - Google)
- Uses **Authlib** to implement the secure OAuth 2.0 authorization code flow
- Users authenticate via external identity providers (e.g., Google) entirely on the provider's secure platform
- Eliminates the need to handle or store passwords and MFA secrets for these accounts locally
- Accounts are automatically provisioned or linked locally upon the first successful sign-in

### Storage & Cryptography
- **Password Hashing**: Passwords are one-way hashed using Werkzeug's built-in secure hashing (e.g., PBKDF2/scrypt) and are **never** stored in plaintext or reversibly encrypted.
- **Symmetric Encryption (Fernet)**: Used to securely encrypt sensitive data at rest, such as MFA secrets (AES-128 in CBC mode).
- The symmetric encryption key is securely generated and stored in `.env`.
- The application handles transparent encryption/decryption of these MFA secrets during the authentication flow.

## Project Structure

```
passkey-instead-of-MFA/
├── .env                        # Environment variables (not tracked by git)
├── .gitignore                  # Git ignore rules
├── app.py                      # Main application entry point
├── config.py                   # Application configuration settings
├── package.json                # Node dependencies
├── package-lock.json           # Node dependencies lockfile
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── modules/                    # Application logic
│   ├── database.py             # Database models and connection setup
│   ├── routes/                 # Flask blueprint route definitions
│   │   ├── __init__.py         # Route blueprints initialization
│   │   ├── auth_classic.py     # Traditional username/password routes
│   │   ├── auth_otp.py         # MFA/OTP authentication routes
│   │   ├── auth_passkey.py     # WebAuthn/Passkey routes
│   │   ├── auth_social.py      # OAuth/Social login routes
│   │   └── main.py             # Core application routes (e.g., dashboard)
│   ├── services/               # Business logic
│   │   └── user_service.py     # User data management and retrieval
│   └── utils/                  # Helper utilities
│       ├── decorators.py       # Authentication requirement decorators
│       ├── encryptor.py        # Fernet encryption/decryption functions
│       ├── oauth.py            # OAuth integration helpers
│       └── passkey_helpers.py  # WebAuthn credential processing helpers
├── questionnaire/              # Frontend interactive components
│   ├── app.js                  
│   ├── index.html              
│   └── styles.css              
├── static/                     # Public static assets
│   ├── css/                    # Stylesheets for each page
│   │   ├── dashboard.css
│   │   ├── google_login.css
│   │   ├── login.css
│   │   ├── mfa_login.css
│   │   ├── passkey_login.css
│   │   ├── passkey_register.css
│   │   ├── register.css
│   │   ├── setup_choice.css
│   │   ├── setup_mfa.css
│   │   ├── style.css
│   │   └── verify_mfa.css
│   └── js/                     # Frontend interactivity JavaScript
│       ├── app.js
│       ├── passkey_login.js
│       ├── passkey_register.js
│       └── setup_choice.js
└── templates/                  # HTML templates
    ├── dashboard.html          # Protected user dashboard
    ├── google_login.html       # Social login interface
    ├── index.html              # Landing page with comparison
    ├── login.html              # Basic username login
    ├── mfa_login.html          # MFA login page
    ├── passkey_login.html      # Passkey login page
    ├── passkey_register.html   # Passkey registration
    ├── register.html           # User registration form
    ├── setup_choice.html       # Setup authentication method choice
    ├── setup_mfa.html          # MFA QR code setup
    └── verify_mfa.html         # MFA code verification

```

## Security Features

- **Secure Password Hashing** - Passwords are irreversibly hashed using Werkzeug's default secure hashing algorithms before being stored.
- **Encrypted Storage** - App-specific sensitive data, like MFA setup secrets, are encrypted at rest using Fernet symmetric encryption.
- **HTTPS Only** - SSL/TLS for all connections  
- **Session Management** - Secure Flask sessions  
- **Phishing-Resistant** - Passkeys are domain-bound  
- **No Password Transmission** - Passkeys use public-key cryptography  
- **Biometric Verification** - Relies on the device's secure enclave


## Browser Support

### Passkeys work in:
- Chrome 67+ (all platforms)
- Safari 13+ (macOS, iOS)
- Firefox 60+ (all platforms)
- Edge 18+ (Windows, macOS)


## For future improvements, we plan to:
- Use proper SSL certificates (Let's Encrypt)
- Implement rate limiting (Flask-Limiter)
- Add CSRF protection (Flask-WTF)
- Verify passkey assertions cryptographically
- Add account recovery flows
- Implement session timeout
- Add audit logging



## Credits

### Developers

- Jake Lockitch
- Leah Goldin
- Irina Vilcu
- Condoleezza Agbeko
- Mariam Kamara
- Enna Pirvu

### Built with:
- Flask - Web framework
- PyOTP - TOTP implementation
- Cryptography - Fernet encryption
- WebAuthn API - Passkey standard
- OAuth 2.0 - Social authentication

### Deployed with:
- Render - web server
- Supabase - PostgreSQL database manager

## Learn More

### WebAuthn & Passkeys
- [WebAuthn Guide](https://webauthn.guide/) - Interactive guide
- [FIDO Alliance](https://fidoalliance.org/) - Standards body
- [Passkeys.dev](https://passkeys.dev/) - Implementation guides
- [WebAuthn.io](https://webauthn.io/) - Demo and tools

### Security & Cryptography
- [Fernet Specification](https://github.com/fernet/spec/) - Encryption details
- [OWASP Authentication](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/README) - Best practices