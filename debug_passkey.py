#!/usr/bin/env python3
"""
Passkey Registration Debugger
Run this to check your setup and identify issues
"""

import os
import json

print("=" * 70)
print("🔍 PASSKEY REGISTRATION DEBUGGER")
print("=" * 70)

# Check files exist
files_to_check = {
    'app.py': 'Flask application',
    'templates/passkey_register.html': 'Passkey registration template',
    'templates/passkey_login.html': 'Passkey login template',
    'users.json': 'User database',
    'encryption.key': 'Encryption key'
}

print("\n📁 FILE CHECK:")
print("-" * 70)
for file, desc in files_to_check.items():
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file:<35} ({size:,} bytes) - {desc}")
    else:
        print(f"❌ {file:<35} MISSING! - {desc}")

# Check users.json structure
print("\n👥 USER DATABASE:")
print("-" * 70)
if os.path.exists('users.json'):
    try:
        with open('users.json', 'r') as f:
            data = json.load(f)
        print(f"✅ Valid JSON - {len(data)} user(s) found")

        for username, user_data in data.items():
            print(f"\n   User: {username}")
            print(f"   ├─ Password: {'✅ Set (encrypted)' if user_data.get('password') else '❌ Missing'}")
            print(f"   ├─ MFA Secret: {'✅ Set (encrypted)' if user_data.get('mfa_secret') else '⚪ Not set'}")

            passkeys = user_data.get('passkey_credentials', [])
            print(f"   └─ Passkeys: {len(passkeys)} registered")

            if passkeys:
                for i, cred in enumerate(passkeys, 1):
                    cred_id = cred.get('id', 'N/A')[:20]
                    print(f"      • Passkey {i}: {cred_id}...")
            else:
                print(f"      ⚠️  No passkeys registered for this user!")

    except json.JSONDecodeError as e:
        print(f"❌ INVALID JSON: {e}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
else:
    print("❌ users.json not found!")

# Check passkey_register.html
print("\n🔑 PASSKEY REGISTRATION TEMPLATE:")
print("-" * 70)
if os.path.exists('templates/passkey_register.html'):
    with open('templates/passkey_register.html', 'r') as f:
        content = f.read()

    checks = {
        'async function registerPasskey()': 'JavaScript function exists',
        'navigator.credentials.create': 'WebAuthn API call',
        '/api/passkey/register-options': 'API endpoint call',
        '/api/passkey/register-verify': 'Verify endpoint call',
        '{% if username %}': 'Username check (Jinja2)',
        'arrayBufferToBase64': 'Base64 conversion function'
    }

    for check, desc in checks.items():
        if check in content:
            print(f"✅ {desc}")
        else:
            print(f"❌ MISSING: {desc}")
            print(f"   Search for: {check}")
else:
    print("❌ templates/passkey_register.html not found!")

# Check app.py routes
print("\n🛣️  FLASK ROUTES:")
print("-" * 70)
if os.path.exists('app.py'):
    with open('app.py', 'r') as f:
        content = f.read()

    routes = {
        "@app.route('/passkey-register'": 'Passkey registration page',
        "@app.route('/api/passkey/register-options'": 'Get registration options',
        "@app.route('/api/passkey/register-verify'": 'Verify registration',
        "@app.route('/api/passkey/login-options'": 'Get login options',
        "@app.route('/api/passkey/login-verify'": 'Verify login'
    }

    for route, desc in routes.items():
        if route in content:
            print(f"✅ {desc}")
        else:
            print(f"❌ MISSING: {desc}")
else:
    print("❌ app.py not found!")

print("\n" + "=" * 70)
print("💡 RECOMMENDATIONS:")
print("=" * 70)

if not os.path.exists('templates/passkey_register.html'):
    print("❌ Critical: passkey_register.html is missing!")
    print("   Run the fix script to recreate this file.")
elif os.path.exists('users.json'):
    try:
        with open('users.json', 'r') as f:
            data = json.load(f)
        has_passkeys = any(
            len(user.get('passkey_credentials', [])) > 0 
            for user in data.values()
        )
        if not has_passkeys:
            print("⚠️  No passkeys registered yet.")
            print("   Try registering a passkey and check browser console (F12) for errors.")
    except:
        pass

print("\n🎯 NEXT STEPS:")
print("-" * 70)
print("1. Run your Flask app: python3 app.py")
print("2. Open browser to: https://localhost:5000")
print("3. Open browser console: Press F12 → Console tab")
print("4. Try to register a passkey")
print("5. Share any RED error messages from console")
print("=" * 70)
