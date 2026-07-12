#!/usr/bin/env python3

import webbrowser
import time
import sys
import requests
import re
import random
import os
import json
from user_agent import generate_user_agent
from threading import Thread
from rich import print as g
from rich.panel import Panel
from cfonts import render, say
from AegosPy import *
import secrets
import binascii
import uuid
from urllib.parse import urlencode
from MedoSigner import Argus, Gorgon, md5, Ladon

# Color codes
R = '\033[1;31;40m'
X = '\033[1;33;40m'
F = '\033[1;32;40m'
C = "\033[1;97;40m"
B = '\033[1;36;40m'
K = '\033[1;35;40m'
V = '\033[1;36;40m'
Z = '\033[1;31m'

# Global counters
hit, ge, be, gt, bt = 0, 0, 0, 0, 0

# User inputs
try:
    iid = input(f'{F}ID : ')
    tok = input(f'{F}Token : ')
except EOFError:
    iid = "YOUR_ID"
    tok = "YOUR_TOKEN"

def send_telegram_message(chat_id, bot_token, text):
    try:
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={text}", timeout=10)
    except:
        pass

def check_tiktok_email(email_prefix, domain):
    global ge, be, bt, iid, tok
    full_email = f"{email_prefix}@{domain}"
    
    try:
        # Check TikTok user availability
        tiktok_check = AegosPy.CheckTik(full_email)
        if tiktok_check.get("Status") == "OK":
            print(f'{B}- {X}GooD TikTok {F}: {C}{full_email}')
            
            email_check = None
            if domain == 'gmail.com': email_check = AegosPy.A_Gmail(full_email)
            elif domain == 'yahoo.com': email_check = AegosPy.A_Yahoo(full_email)
            elif domain == 'hotmail.com': email_check = AegosPy.A_Hotmail(full_email)
            elif domain == 'aol.com': email_check = AegosPy.A_Aol(full_email)
            elif domain == 'mail.ru': email_check = AegosPy.A_MailRu(full_email)

            if email_check and email_check.get("Status") == "Available":
                print(f'{B}- {F}GooD {domain.upper()} {X}: {C}{full_email}')
                user_info = AegosPy.GetInfoTik(email_prefix)
                
                telegram_text = (
                    f'UserName : {email_prefix}\n'
                    f'Email : {full_email}\n'
                    f'Id : {user_info.get("id", "N/A")}\n'
                    f'Name : {user_info.get("name", "N/A")}\n'
                    f'Bio : {user_info.get("bio", "N/A")}\n'
                    f'Region : {user_info.get("code-country", "N/A")}\n'
                    f'Followers : {user_info.get("followers", "N/A")}\n'
                    f'Likes : {user_info.get("likes", "N/A")}\n'
                    f'Programmer : @bsx_h2'
                )
                send_telegram_message(iid, tok, telegram_text)
                ge += 1
            else:
                be += 1
        else:
            bt += 1
    except:
        pass

def hso1_merged():
    global iid, tok
    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "application/json",
        "Referer": "https://livecounts.xyz/"
    }
    
    while True:
        try:
            # Generate random search term
            search_chars = 'qwertyuiopasdfghjklzxcvbnm'
            name_search = "".join(random.choice(search_chars) for _ in range(random.randint(2, 5)))
            
            search_url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{name_search}'
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success') and 'results' in data:
                        for user_data in data['results']:
                            username = user_data.get('username')
                            if username and '_' not in username and 5 <= len(username) <= 30:
                                for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
                                    check_tiktok_email(username, domain)
                                    time.sleep(0.5)
                    else:
                        # If API fails, try a different random search
                        pass
                except json.JSONDecodeError:
                    # This is the error the user saw. It means the site returned something else.
                    # We will just wait and retry to avoid flooding the console.
                    time.sleep(10)
            elif response.status_code == 403 or response.status_code == 429:
                # Rate limited or blocked
                time.sleep(60)
            else:
                time.sleep(10)
                
        except Exception as e:
            # Catch other network errors
            time.sleep(5)
        
        # Mandatory sleep to prevent "freezing" or high CPU
        time.sleep(random.randint(5, 10))

if __name__ == '__main__':
    os.system('clear')
    print(f"{X}[{F} ✓ {X}]{C} Starting Tool...")
    time.sleep(2)

    # Use a reasonable number of threads to avoid instant blocking
    thread_count = 10 
    for _ in range(thread_count):
        t = Thread(target=hso1_merged)
        t.daemon = True
        t.start()

    print(f"{G}Running with {thread_count} threads. Check your Telegram bot for hits.{C}")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nExiting...")
