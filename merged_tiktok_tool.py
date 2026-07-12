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

# Color codes from Tik.py
R = '\033[1;31;40m'  # Kırmızı
X = '\033[1;33;40m'  # Sarı
F = '\033[1;32;40m'  # Yeşil
C = "\033[1;97;40m"  # Beyaz
B = '\033[1;36;40m'  # Mavi
K = '\033[1;35;40m'  # Mor
V = '\033[1;36;40m'  # Turkuaz
a14 = '\x1b[38;5;153m'
a1 = '\x1b[1;31m'
a3 = '\x1b[1;32m'
a9 = '\x1b[1;37m'
P = '\x1b[1;97m'
H = '\x1b[1;92m'

# Global counters
hit, ge, be, gt, bt = 0, 0, 0, 0, 0

# User inputs for Telegram bot
iid = input(f'{F}ID : ')
tok = input(f'{F}Token : ')

# Initialize session and secret for TikTok API
secret = secrets.token_hex(16)
session = requests.Session()

def generate_tiktok_params():
    device_brands = ["samsung", "huawei", "xiaomi", "apple", "oneplus"]
    device_types = ["SM-S928B", "P40", "Mi 11", "iPhone12,1", "OnePlus9"]
    regions = ["AE", "IQ", "US", "FR", "DE"]
    languages = ["ar", "en", "fr", "de"]
    
    params = {
        'passport-sdk-version': "6030790",
        'iid': str(random.randint(1, 10**19)),
        'device_id': str(random.randint(1, 10**19)),
        'ac': "WIFI",
        'channel': "googleplay",
        'aid': "1233",
        'app_name': "musical_ly",
        'version_code': "360505",
        'version_name': "36.5.5",
        'device_platform': "android",
        'os': "android",
        'ab_version': "36.5.5",
        'ssmix': "a",
        'device_type': random.choice(device_types),
        'device_brand': random.choice(device_brands),
        'language': random.choice(languages),
        'os_api': str(random.randint(28, 34)),
        'os_version': str(random.randint(10, 14)),
        'openudid': str(binascii.hexlify(os.urandom(8)).decode()),
        'manifest_version_code': "2023605050",
        'resolution': "1440*2969",
        'dpi': str(random.choice([420, 480, 532])),
        'update_version_code': "2023605050",
        '_rticket': str(round(random.uniform(1.2, 1.6) * 100000000) * -1) + "4632",
        'is_pad': "0",
        'app_type': "normal",
        'sys_region': random.choice(regions),
        'last_install_time': str(random.randint(1600000000, 1700000000)),
        'mcc_mnc': "41820",
        'timezone_name': "Asia/Baghdad",
        'carrier_region_v2': "418",
        'app_language': random.choice(languages),
        'carrier_region': random.choice(regions),
        'ac2': "wifi",
        'uoo': "0",
        'op_region': random.choice(regions),
        'timezone_offset': str(random.randint(0, 14400)),
        'build_number': "36.5.5",
        'host_abi': "arm64-v8a",
        'locale': random.choice(languages),
        'region': random.choice(regions),
        'ts': str(round(random.uniform(1.2, 1.6) * 100000000) * -1),
        'cdid': str(uuid.uuid4()),
        'support_webview': "1",
        'reg_store_region': random.choice(regions).lower(),
        'user_selected_region': "0",
        'cronet_version': "1c651b66_2024-08-30",
        'ttnet_version': "4.2.195.8-tiktok",
        'use_store_region_cookie': "1"
    }
    return params

def generate_tiktok_headers(params):
    # MedoSigner's Gorgon expects params as a dictionary, not urlencoded string
    m = Gorgon(params, int(time.time()), payload=None, cookie=None).get_value() 
    
    app_name = "com.zhiliaoapp.musically"
    app_version = f"{random.randint(2000000000, 3000000000)}"
    platform = "Linux"
    os_version_str = f"Android {random.randint(10, 15)}"
    locales = ["ar_AE", "en_US", "fr_FR", "es_ES"]
    locale = random.choice(locales)
    device_types = ["phone", "tablet", "tv"]
    device_type_str = random.choice(device_types)
    build = f"UP1A.{random.randint(200000000, 300000000)}"
    cronet_version = f"{random.randint(10000000, 20000000)}" 
    cronet_date = f"{random.randint(2023, 2025)}-{random.randint(1, 12):02}-{random.randint(1, 28):02}"
    quic_version = f"{random.randint(10000000, 20000000)}"
    quic_date = f"{random.randint(2023, 2025)}-{random.randint(1, 12):02}-{random.randint(1, 28):02}"

    user_agent = (f"{app_name}/{app_version} ({platform}; U; {os_version_str}; {locale}; {device_type_str}; "
                  f"Build/{build}; Cronet/{cronet_version} {cronet_date}; "
                  f"QuicVersion:{quic_version} {quic_date})")

    headers = {
        'User-Agent': user_agent,
        'x-tt-passport-csrf-token': secret,
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
        'x-argus': m["x-argus"],
        'x-gorgon': m["x-gorgon"],
        'x-khronos': m["x-khronos"],
        'x-ladon': m["x-ladon"],
    }
    return headers

def send_telegram_message(chat_id, bot_token, text):
    try:
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def check_tiktok_email(email_prefix, domain):
    global hit, ge, be, gt, bt, iid, tok
    full_email = f"{email_prefix}@{domain}"
    
    try:
        # Use AegosPy to check TikTok user and email availability
        tiktok_check_response = AegosPy.CheckTik(full_email)
        if tiktok_check_response["Status"] == "OK":
            print(f'{B}- {X}GooD TikTok {F}: {C}{full_email}')
            
            email_available_response = None
            if domain == 'gmail.com':
                email_available_response = AegosPy.A_Gmail(full_email)
            elif domain == 'yahoo.com':
                email_available_response = AegosPy.A_Yahoo(full_email)
            elif domain == 'hotmail.com':
                email_available_response = AegosPy.A_Hotmail(full_email)
            elif domain == 'aol.com':
                email_available_response = AegosPy.A_Aol(full_email)
            elif domain == 'mail.ru':
                email_available_response = AegosPy.A_MailRu(full_email)

            if email_available_response and email_available_response["Status"] == "Available":
                print(f'{B}- {F}GooD {domain.split(".")[0].upper()} {X}: {C}{full_email}')
                user_info = AegosPy.GetInfoTik(email_prefix)
                
                Id = user_info.get('id', 'N/A')
                Name = user_info.get('name', 'N/A')
                Bio = user_info.get('bio', 'N/A')
                Region = user_info.get('code-country', 'N/A')
                Private = user_info.get('private', 'N/A')
                Followers = user_info.get('followers', 'N/A')
                Following = user_info.get('following', 'N/A')
                Likes = user_info.get('likes', 'N/A')
                VideoCount = user_info.get('video', 'N/A')
                
                telegram_text = (
                    f'UserName : {email_prefix}\n'
                    f'Email : {full_email}\n'
                    f'Id : {Id}\n'
                    f'Name : {Name}\n'
                    f'Bio : {Bio}\n'
                    f'Region : {Region}\n'
                    f'Private : {Private}\n'
                    f'Followers : {Followers}\n'
                    f'Following : {Following}\n'
                    f'Likes : {Likes}\n'
                    f'VideoCount : {VideoCount}\n'
                    f'Programmer : @bsx_h2'
                )
                send_telegram_message(iid, tok, telegram_text)
                ge += 1 # Good email count
            else:
                print(f'{B}-{R} BaD {domain.split(".")[0].upper()} {F}:{C} {full_email}')
                be += 1 # Bad email count
        else:
            print(f'{B}-{R} BaD TikTok {F}:{C} {full_email}')
            bt += 1 # Bad TikTok count
    except Exception as e:
        print(f"Error in check_tiktok_email for {full_email}: {e}")

def hso1_merged():
    global hit, ge, be, gt, bt, iid, tok
    while True:
        try:
            # Generate random keyword for TikTok search (from Tik.py)
            g_chars = random.choice([
                'ğüişöçñäüğüişöçñäüğüişöçñäüqw.ertyuiopasdfghjklzxcvbnm',
                'abcdefghijklmnopqrstuvwxyzéèêëàâäôùûüîïç'
            ])
            keyword = ''.join((random.choice(g_chars) for i in range(random.randrange(4, 9))))
            
            # Use livecounts.xyz API to find usernames (from user's script)
            user1_chars = 'qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbnm'
            number_chars = '6789'
            rng = int("".join(random.choice(number_chars) for i in range(1)))
            name_search = str("".join(random.choice(user1_chars) for i in range(rng)))
            
            search_url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{name_search}'
            search_response = requests.get(search_url).json()
            
            if 'results' in search_response:
                for user_data in search_response['results']:
                    username = user_data['username']
                    # Apply filtering logic from Tik.py
                    if '_' in username or len(username) < 5 or len(username) > 30:
                        continue
                    
                    # Check with AegosPy for different email domains
                    check_tiktok_email(username, 'gmail.com')
                    check_tiktok_email(username, 'yahoo.com')
                    check_tiktok_email(username, 'hotmail.com')
                    check_tiktok_email(username, 'aol.com')
                    check_tiktok_email(username, 'mail.ru')

        except Exception as e:
            print(f"Error in hso1_merged: {e}")
        time.sleep(random.randint(5, 15)) # Add a delay to avoid rate limiting

# Main execution logic
if __name__ == '__main__':
    print(f"{X}[{F} ✓ {X}]{C} Done Login is Tool")
    time.sleep(2)
    os.system('clear')

    # Start multiple threads for hso1_merged
    for i in range(28):
        Thread(target=hso1_merged).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)
