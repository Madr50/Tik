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

# Color codes
R = '\033[1;31;40m'
X = '\033[1;33;40m'
F = '\033[1;32;40m'
C = "\033[1;97;40m"
B = '\033[1;36;40m'
K = '\033[1;35;40m'
V = '\033[1;36;40m'
Z = '\033[1;31m'
G = '\033[1;32m'
Y = '\033[1;33m'

# Global counters and Lock for clean printing
hit, ge, be, gt, bt = 0, 0, 0, 0, 0
print_lock = Lock()

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
    
    with print_lock:
        print(f'{Y}[*] Checking: {C}{full_email}', end='\r')
        
    try:
        tiktok_check = AegosPy.CheckTik(full_email)
        if tiktok_check.get("Status") == "OK":
            with print_lock:
                print(f'\n{B}[+] {X}GooD TikTok {F}: {C}{full_email}')
            
            email_check = None
            if domain == 'gmail.com': email_check = AegosPy.A_Gmail(full_email)
            elif domain == 'yahoo.com': email_check = AegosPy.A_Yahoo(full_email)
            elif domain == 'hotmail.com': email_check = AegosPy.A_Hotmail(full_email)
            elif domain == 'aol.com': email_check = AegosPy.A_Aol(full_email)
            elif domain == 'mail.ru': email_check = AegosPy.A_MailRu(full_email)

            if email_check and email_check.get("Status") == "Available":
                with print_lock:
                    print(f'{G}[!] FOUND HIT: {C}{full_email}')
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
    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "application/json",
        "Referer": "https://livecounts.xyz/"
    }
    
    while True:
        try:
            search_chars = 'qwertyuiopasdfghjklzxcvbnm'
            name_search = "".join(random.choice(search_chars) for _ in range(random.randint(2, 4)))
            
            with print_lock:
                print(f'{V}[~] Searching for users matching: {name_search}...', end='\r')
                
            search_url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{name_search}'
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success') and 'results' in data:
                        results = data['results']
                        random.shuffle(results)
                        for user_data in results[:5]: # Check top 5 from each search to stay efficient
                            username = user_data.get('username')
                            if username and '_' not in username and 5 <= len(username) <= 20:
                                for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
                                    check_tiktok_email(username, domain)
                                    time.sleep(1)
                    else:
                        time.sleep(2)
                except:
                    time.sleep(5)
            elif response.status_code == 403 or response.status_code == 429:
                time.sleep(30)
            else:
                time.sleep(5)
                
        except:
            time.sleep(5)
        
        time.sleep(random.randint(2, 5))

if __name__ == '__main__':
    os.system('clear')
    print(f"{X}[{F} ✓ {X}]{C} TikTok Multi-Checker Started")
    print(f"{V}----------------------------------------{C}")
    time.sleep(1)

    thread_count = 5 # Starting with 5 threads for better visibility and stability
    for _ in range(thread_count):
        t = Thread(target=hso1_merged)
        t.daemon = True
        t.start()

    print(f"{G}[+] Running with {thread_count} threads.{C}")
    print(f"{G}[+] Live status will be shown below...{C}\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
