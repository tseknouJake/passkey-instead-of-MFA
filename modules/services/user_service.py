from modules.database import supabase
from modules.utils.encryptor import encrypt_data, decrypt_data

def get_user(username):
    response = supabase.table("users").select("*").eq("username", username).execute()
    user = response.data[0] if response.data else None
    if user:
        if user.get("password"):
            user["password"] = decrypt_data(user["password"])
        if user.get("mfa_secret"):
            user["mfa_secret"] = decrypt_data(user["mfa_secret"])
    return user

def create_user(username, password):
    encrypted_password = encrypt_data(password)
    supabase.table("users").insert({
        "username": username, "password": encrypted_password
    }).execute()

def create_social_user(username, _provider): #TODO: remove and use create user instead
    supabase.table("users").insert({
        "username": username,
        "password": None
    }).execute()

def update_mfa_secret(username, secret):
    encrypted_secret = encrypt_data(secret)
    supabase.table("users").update({
        "mfa_secret": encrypted_secret
    }).eq("username", username).execute()

def add_passkey_credential(username, credential):
    user = get_user(username)
    current_credentials = user.get("passkey_credentials") or []
    updated_credentials = current_credentials + [credential]
    supabase.table("users").update({
        "passkey_credentials": updated_credentials
    }).eq("username", username).execute()