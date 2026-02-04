
# Quick diagnostic - check if register route exists in your app.py

import re

try:
    with open('app.py', 'r') as f:
        content = f.read()

    # Check for register route
    if "@app.route('/register'" in content:
        print("✅ Register route EXISTS in app.py")
    else:
        print("❌ Register route MISSING from app.py")
        print("\nYou need to replace your app.py with the updated version!")

    # Check for encryption functions
    if "def get_encryption_key" in content:
        print("✅ Encryption functions EXIST")
    else:
        print("❌ Encryption functions MISSING")

    # Check for setup_choice route
    if "@app.route('/setup-choice')" in content:
        print("✅ Setup choice route EXISTS")
    else:
        print("❌ Setup choice route MISSING")

except FileNotFoundError:
    print("❌ app.py not found in current directory")
