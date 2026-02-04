# Basic Website with Login and MFA

A simple Flask web application with login functionality and Multi-Factor Authentication (MFA) using TOTP (Time-based One-Time Password).

## Features

- ✅ User authentication with username/password
- 🔐 Multi-Factor Authentication (MFA) using TOTP
- 📱 QR code generation for easy authenticator app setup
- 🛡️ Session management and security
- 🎨 Modern, responsive UI design

## Requirements

- Python 3.7+
- Flask
- pyotp
- qrcode

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## How to Use

### First Time Login

1. **Login**: Use the demo credentials
   - Username: `admin`
   - Password: `password123`

2. **Setup MFA**: 
   - Download an authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
   - Scan the QR code displayed on screen
   - Alternatively, manually enter the secret key into your authenticator app

3. **Verify MFA**:
   - Enter the 6-digit code from your authenticator app
   - Click "Verify" to complete login

### Subsequent Logins

1. Enter your username and password
2. Enter the current 6-digit code from your authenticator app
3. Access the secure dashboard

## Security Notes

⚠️ **This is a demo application. For production use:**

- Replace the in-memory user database with a proper database
- Use bcrypt or similar to hash passwords (never store plaintext!)
- Use environment variables for the secret key
- Implement HTTPS/TLS
- Add rate limiting to prevent brute force attacks
- Add password complexity requirements
- Implement account lockout after failed attempts
- Add CSRF protection
- Store MFA secrets securely (encrypted in database)

## File Structure

```
.
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── login.html        # Login page
│   ├── setup_mfa.html    # MFA setup page
│   ├── verify_mfa.html   # MFA verification page
│   └── dashboard.html    # Protected dashboard page
└── README.md             # This file
```

## How It Works

1. **Authentication**: Users provide credentials which are verified against the user database
2. **MFA Setup**: A unique secret is generated and encoded as a QR code for the user to scan
3. **TOTP Verification**: The app generates time-based codes that change every 30 seconds
4. **Session Management**: Successfully authenticated users receive a secure session cookie

## Customization

### Adding New Users

Edit the `users` dictionary in `app.py`:

```python
users = {
    "newuser": {
        "password": "securepassword",  # Hash this in production!
        "mfa_secret": None
    }
}
```

### Changing the Port

Modify the last line in `app.py`:

```python
app.run(debug=True, port=8080)  # Change to your preferred port
```

## License

Free to use and modify for any purpose.
