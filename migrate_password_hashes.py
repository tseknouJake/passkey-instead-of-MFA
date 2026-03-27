#!/usr/bin/env python3
import argparse
import sys

from cryptography.fernet import InvalidToken

from app import decrypt_data, hash_password, is_password_hash, supabase, update_user_password


def fetch_users_page(offset, page_size):
    response = (
        supabase.table("users")
        .select("username,password")
        .order("username")
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return response.data or []


def get_plaintext_password(stored_password):
    if not stored_password or is_password_hash(stored_password):
        return None

    if stored_password.startswith("gAAAA"):
        try:
            return decrypt_data(stored_password)
        except InvalidToken as exc:
            raise ValueError(
                "encrypted password could not be decrypted with the current FERNET_KEY"
            ) from exc

    return stored_password


def migrate_password_hashes(dry_run=False, page_size=500):
    offset = 0
    scanned = 0
    migrated = 0
    skipped_empty = 0
    skipped_hashed = 0
    errors = []

    while True:
        users = fetch_users_page(offset, page_size)
        if not users:
            break

        for user in users:
            scanned += 1
            username = user.get("username") or "<missing-username>"
            stored_password = user.get("password")

            if not stored_password:
                skipped_empty += 1
                continue

            if is_password_hash(stored_password):
                skipped_hashed += 1
                continue

            try:
                plaintext_password = get_plaintext_password(stored_password)
                if not plaintext_password:
                    skipped_empty += 1
                    continue

                new_hash = hash_password(plaintext_password)
                if not dry_run:
                    update_user_password(username, new_hash)

                migrated += 1
                action = "Would migrate" if dry_run else "Migrated"
                print(f"{action}: {username}")
            except Exception as exc:
                message = str(exc) or exc.__class__.__name__
                errors.append((username, message))
                print(f"Error migrating {username}: {message}", file=sys.stderr)

        if len(users) < page_size:
            break

        offset += page_size

    print(f"Scanned: {scanned}")
    print(f"Migrated: {migrated}")
    print(f"Skipped empty passwords: {skipped_empty}")
    print(f"Skipped already hashed: {skipped_hashed}")
    print(f"Errors: {len(errors)}")

    if errors:
        for username, message in errors:
            print(f" - {username}: {message}", file=sys.stderr)
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Hash all existing non-null user passwords in Supabase."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which users would be migrated without writing changes.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Number of users to fetch per batch.",
    )
    args = parser.parse_args()

    if args.page_size < 1:
        parser.error("--page-size must be at least 1")

    raise SystemExit(migrate_password_hashes(dry_run=args.dry_run, page_size=args.page_size))


if __name__ == "__main__":
    main()
