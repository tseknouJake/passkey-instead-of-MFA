import json
import os

print("="*70)
print("🔍 CHECKING YOUR SETUP:")
print("="*70)

# Check if files exist
if os.path.exists('users.json'):
    print("✅ users.json exists")
    with open('users.json', 'r') as f:
        data = json.load(f)
        print(f"\n📊 Found {len(data)} user(s):")
        for username, user_data in data.items():
            print(f"\n   User: {username}")
            print(f"   - Password: {'[encrypted]' if user_data.get('password') else '[MISSING]'}")
            print(f"   - MFA Secret: {'[encrypted]' if user_data.get('mfa_secret') else '[NOT SET]'}")
            print(f"   - Passkey Credentials: {len(user_data.get('passkey_credentials', []))} registered")

            if user_data.get('passkey_credentials'):
                for i, cred in enumerate(user_data['passkey_credentials']):
                    print(f"     • Passkey {i+1}:")
                    print(f"       ID: {cred.get('id', 'N/A')[:30]}...")
                    print(f"       Type: {cred.get('type', 'N/A')}")
else:
    print("❌ users.json NOT FOUND!")

if os.path.exists('encryption.key'):
    print("\n✅ encryption.key exists")
else:
    print("\n❌ encryption.key NOT FOUND!")

print("\n" + "="*70)
print("🎯 TROUBLESHOOTING:")
print("="*70)
print("""
If passkey_credentials shows 0:
   → The passkey registration didn't complete
   → Check browser console for JavaScript errors
   → Make sure you clicked through Touch ID prompt

If passkey_credentials shows 1 or more:
   → Passkey IS registered
   → Login failure is a different issue
   → Check browser console during login
""")
