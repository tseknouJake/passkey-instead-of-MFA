"""
Service layer for user study profiles and per-auth-method responses

Supabase is the primary store. When network access to Supabase is unavailable,
the service falls back to a local JSON file. This allows local dev to continue working.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from postgrest.exceptions import APIError

from modules.database import supabase
from modules.utils.storage_fallback import Storage

LOCAL_STUDY_DATA_FILE = Path(
    os.environ.get("LOCAL_STUDY_DATA_FILE") or Path(__file__).resolve().parents[2] / "study_data.json"
).expanduser()

_storage = Storage(
    path=LOCAL_STUDY_DATA_FILE,
    default={"profiles": {}, "responses": {}},
    label="study data",
    supabase_client=supabase,
)

STUDY_PROFILE_TABLE = "study_profiles"
STUDY_RESPONSE_TABLE = "study_responses"

AUTH_METHOD_LABELS = {
    "classic": "Classic Username + Password",
    "mfa": "Username + Password + Authenticator (MFA/TOTP)",
    "passkey": "Passkey (Face ID / Touch ID / device unlock)",
    "social": "Sign in with Google",
}

LIKERT_QUESTIONS = [
    ("easy_to_log_in", "It was easy for me to log in using this method"),
    ("easy_to_understand", "It was easy for me to understand how to log in using this method"),
    ("easy_to_get_set_up", "This login method was easy for me to set up"),
    ("set_up_without_assistance", "I could set up this login method without needing assistance"),
    ("quick_to_complete", "I could complete the login quickly using this method"),
    ("complete_without_help", "I could complete the login without needing help"),
    ("felt_secure", "This login method felt secure"),
    ("trust_to_protect_account", "I would trust this login method to protect an important account"),
    ("comfortable_regularly", "I would be comfortable using this login method regularly"),
]

TECHNICAL_EXPERTISE_OPTIONS = [
    (1, "1 - Not technical at all"),
    (2, "2 - Slightly technical"),
    (3, "3 - Moderately technical"),
    (4, "4 - Very technical"),
    (5, "5 - Expert"),
]

GENDER_OPTIONS = [
    "Woman",
    "Man",
    "Non-binary",
    "Prefer to self-describe",
    "Prefer not to say",
]

USED_BEFORE_OPTIONS = [
    ("yes", "Yes"),
    ("no", "No"),
]

USE_PASSWORD_MANAGER = [
    ("yes", "Yes"),
    ("no", "No"),
]

_fallback_logged = False


class StudyStorageSetupError(RuntimeError):
    """
    Raised when study storage is configured but the required database objects do not exist.
    """


STUDY_STORAGE_SETUP_MESSAGE = (
    "Study storage is not ready yet. Run sql/study_schema.sql in Supabase "
    "to create the study_profiles and study_responses tables."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_auth_method_label(auth_method: str | None) -> str:
    return AUTH_METHOD_LABELS.get(auth_method or "", "Unknown login method")


def _is_missing_study_table_error(exc: APIError) -> bool:
    """
    Detect the Supabase/PostgREST error returned when the study tables do not exist.
    """
    error_code = getattr(exc, "code", None)
    if not error_code and hasattr(exc, "json"):
        try:
            error_code = exc.json().get("code")
        except Exception:
            error_code = None

    message = str(exc)
    return error_code == "PGRST205" and (
        STUDY_PROFILE_TABLE in message or STUDY_RESPONSE_TABLE in message
    )

def _response_key(username: str, auth_method: str) -> str:
    return f"{username}:{auth_method}"


def get_study_profile(username: str) -> dict | None:
    def remote_operation():
        response = supabase.table(STUDY_PROFILE_TABLE).select("*").eq("username", username).execute()
        return response.data[0] if response.data else None

    def local_operation():
        return _storage.read()["profiles"].get(username)

    return _storage.run(remote_operation, local_operation)


def save_study_profile(username: str, profile_data: dict) -> None:
    payload = {
        "username": username,
        "age": profile_data["age"],
        "gender": profile_data["gender"],
        "technical_expertise": profile_data["technical_expertise"],
        "use_password_manager": profile_data["use_password_manager"],
        "updated_at": _utc_now(),
    }

    def remote_operation():
        existing_profile = get_study_profile(username)
        if not existing_profile:
            payload["created_at"] = payload["updated_at"]
        supabase.table(STUDY_PROFILE_TABLE).upsert(
            payload,
            on_conflict="username"
        ).execute()

    def local_operation():
        data = _storage.read()
        existing_profile = data["profiles"].get(username, {})
        if "created_at" in existing_profile:
            payload["created_at"] = existing_profile["created_at"]
        else:
            payload["created_at"] = payload["updated_at"]
        data["profiles"][username] = payload
        _storage.write(data)

    _storage.run(remote_operation, local_operation)


def get_study_response(username: str, auth_method: str) -> dict | None:
    def remote_operation():
        response = (
            supabase.table(STUDY_RESPONSE_TABLE)
            .select("*")
            .eq("username", username)
            .eq("auth_method", auth_method)
            .execute()
        )
        return response.data[0] if response.data else None

    def local_operation():
        return _storage.read()["responses"].get(_response_key(username, auth_method))

    return _storage.run(remote_operation, local_operation)


def save_study_response(username: str, auth_method: str, response_data: dict) -> None:
    payload = {
        "username": username,
        "auth_method": auth_method,
        "used_before": response_data["used_before"],
        "additional_feedback": response_data.get("additional_feedback", ""),
        "updated_at": _utc_now(),
    }

    for key, _ in LIKERT_QUESTIONS:
        payload[key] = response_data[key]

    def remote_operation():
        existing_response = get_study_response(username, auth_method)
        if not existing_response:
            payload["created_at"] = payload["updated_at"]
        supabase.table(STUDY_RESPONSE_TABLE).upsert(
            payload,
            on_conflict="username,auth_method"
        ).execute()

    def local_operation():
        data = _storage.read()
        response_key = _response_key(username, auth_method)
        existing_response = data["responses"].get(response_key, {})
        if "created_at" in existing_response:
            payload["created_at"] = existing_response["created_at"]
        else:
            payload["created_at"] = payload["updated_at"]
        data["responses"][response_key] = payload
        _storage.write(data)

    _storage.run(remote_operation, local_operation)
