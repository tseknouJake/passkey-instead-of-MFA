"""
Unified local-fallback storage abstraction.

Each service instantiates its own Storage, with its own file path,
default value, and warning label — keeping fallback behaviour
contextual and non-repetitive across the application.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

AUTH_STORAGE_BACKEND = (os.environ.get("AUTH_STORAGE_BACKEND") or "auto").strip().lower()


class Storage:
    """
    Combines atomic JSON file I/O with Supabase-with-local-fallback logic.

    Usage:
        _storage = Storage(
            path=LOCAL_USERS_FILE,
            default={},
            label="user store",
            supabase_client=supabase
        )

        data = _storage.read()
        _storage.write(data)
        _storage.run(remote_operation, local_operation)
    """

    def __init__(self, path: str | Path, default: Any = None, label: str = "local store", supabase_client=None):
        self._path = Path(path)
        self._default = default if default is not None else {}
        self._label = label
        self._fallback_logged = False
        self._supabase = supabase_client

    def read(self) -> Any:
        """
        Local storage file read
        """
        if not self._path.exists():
            return self._make_default()

        try:
            with self._path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to read local store from %s", self._path)
            return self._make_default()

        if not isinstance(data, type(self._default)):
            return self._make_default()

        if isinstance(data, dict):
            for key, value in self._default.items():
                data.setdefault(key, value)

        return data

    def write(self, data: Any) -> None:
        """
        Local storage file write
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4)
            handle.write("\n")
        temp_path.replace(self._path)

    def run(self, remote_operation, local_operation, exc_handler=None) -> Any:
        """
        Run remote_operation against Supabase, falling back to local_operation
        on network errors or if local storage is configured.

        exc_handler: optional callable(exc) -> any for services that need
        custom exception translation (e.g. APIError -> StudyStorageSetupError).
        """
        if self._use_local_store():
            return local_operation()

        try:
            return remote_operation()
        except httpx.RequestError as exc:
            self._log_fallback(str(exc))
            return local_operation()
        except Exception as exc:
            if exc_handler:
                return exc_handler(exc)
            raise

    def _use_local_store(self) -> bool:
        """
        Determine whether local storage is configured or not.
        """
        if AUTH_STORAGE_BACKEND == "file":
            return True
        if AUTH_STORAGE_BACKEND == "supabase":
            return False
        if self._supabase is None:
            self._log_fallback("Supabase configuration is missing")
            return True
        return False

    def _log_fallback(self, reason: str) -> None:
        """
        Log fallback message to logger.
        """
        if self._fallback_logged:
            return
        logger.warning(
            "Supabase unavailable for %s; falling back to local store at %s (%s)",
            self._label,
            self._path,
            reason,
        )
        self._fallback_logged = True

    def _make_default(self) -> Any:
        if isinstance(self._default, dict):
            return dict(self._default)
        if isinstance(self._default, list):
            return list(self._default)
        return self._default