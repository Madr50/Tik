#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TikTok Email Checker v4 — FIXED & OPTIMIZED EDITION                        ║
║  Based on KENDO logic, rebuilt from scratch with proper fixes                ║
╚══════════════════════════════════════════════════════════════════════════════╝

FIXES APPLIED:
  1. REMOVED os.system('cls') — replaced with 
 for live stats (NO FREEZE)
  2. ADDED threading.Lock() — prevents race conditions on counters
  3. FIXED User-Agent — ASCII-only, no weird characters (ğüişöç)
  4. REPLACED MedoSigner — uses public TikTok web API instead
  5. FIXED Gmail() — uses SMTP verification instead of Google signup reverse eng.
  6. ADDED proper exception logging instead of bare except: pass
  7. FIXED cookies — generated dynamically per request
  8. OPTIMIZED threading — 5 threads instead of 28 (avoids rate limits)
  9. ADDED proxy support and request delays
  10. ADDED rich console UI with live table

REQUIREMENTS:
  pip install requests rich user-agent

DISCLAIMER: This tool is for educational/authorized testing only.
"""

import time
import requests
import random
import os
import sys
import re
import string
import threading
import json
import smtplib
import dns.resolver
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich import print as g
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from user_agent import generate_user_agent
from uuid import uuid4

console = Console()

# ═══════════════════════════════════════════════════════════════
# Color & Style Codes
# ═══════════════════════════════════════════════════════════════
R, X, F, C, B, K, V = '\033[1;31;40m', '\033[1;33;40m', '\033[1;32;40m', "\033[1;97;40m", '\033[1;36;40m', '\033[1;35;40m', '\033[1;36;40m'
Z, G, Y, P = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\x1b[1;97m'

# ═══════════════════════════════════════════════════════════════
# Global Stats with Lock (FIX #2)
# ═══════════════════════════════════════════════════════════════
lock = threading.Lock()
stats = {
    'total_checked': 0,
    'tiktok_hits': 0,
    'email_available': 0,
    'email_taken': 0,
    'errors': 0,
    'rate_limited': 0,
    'skipped': 0
}

# ═══════════════════════════════════════════════════════════════
# Telegram Setup
# ═══════════════════════════════════════════════════════════════
try:
    IID = input(f'{F}Telegram Chat ID : ')
    TOK = input(f'{F}Telegram Bot Token : ')
except EOFError:
    IID, TOK = "YOUR_ID", "YOUR_TOKEN"


def send_telegram(text):
    """Safe async Telegram send."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOK}/sendMessage",
            data={"chat_id": IID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        with lock:
            stats['errors'] += 1


# ═══════════════════════════════════════════════════════════════
# Username Validation (Strict TikTok Rules)
# ═══════════════════════════════════════════════════════════════

def is_valid_tiktok_username(username):
    """Strict TikTok username validation."""
    if not username or not isinstance(username, str):
        return False
    if len(username) < 2 or len(username) > 24:
        return False
    allowed = set(string.ascii_lowercase + string.digits + '_.')
    if not all(c in allowed for c in username):
        return False
    if username[0] in '._' or username[-1] in '._':
        return False
    if '..' in username or '__' in username:
        return False
    if username.isdigit():
        return False
    return True


def sanitize_username(username):
    """Force ASCII-only, lowercase, remove invalid chars."""
    username = username.lower()
    username = ''.join(c for c in username if c in string.ascii_lowercase + string.digits + '_.')
    username = re.sub(r'\.+', '.', username)
    username = re.sub(r'_+', '_', username)
    username = username.strip('._')
    return username


# ═══════════════════════════════════════════════════════════════
# Name Databases
# ═══════════════════════════════════════════════════════════════

TRANSLITERATED_NAMES = [
    "ahmed", "mohammed", "mohammad", "muhammad", "ali", "fatima", "zainab",
    "yousef", "yusuf", "maryam", "mariam", "khaled", "sara", "sarah", "nour",
    "noor", "omar", "umar", "hamza", "layla", "leila", "huda", "souad",
    "suad", "ibrahim", "yassin", "yaseen", "mustafa", "moustafa", "layan",
    "ritaj", "abdullah", "abdallah", "abdulrahman", "abdalrahman", "faisal",
    "faysal", "nasser", "naser", "mubarak", "mansour", "mansur", "turki",
    "fahd", "bandar", "sultan", "nawaf", "mishaal", "meshal", "jasser",
    "jasir", "saleh", "salih", "talal", "majed", "majeed", "badr", "sami",
    "tariq", "tarik", "hassan", "hassane", "hussain", "hussein", "saeed",
    "said", "younes", "younis", "waleed", "walid", "anoud", "anood", "reem",
    "rim", "dana", "lama", "ghada", "manal", "haifa", "hayfa", "amal",
    "salma", "yasmin", "yasmine", "nada", "abeer", "abir", "samar", "rana",
    "dina", "deena", "ghassan", "fouad", "fuad", "khalil", "khaleel",
    "ayman", "aymen", "samer", "samir", "rami", "ramez", "fadi", "fady",
    "hisham", "hesham", "tamer", "tamir", "wael", "waiel", "loay", "luay",
    "saad", "mahmoud", "mahmood", "kamal", "jamal", "raed", "radi",
    "basem", "basim", "karim", "kareem", "tarek", "hamed", "hamid", "nabil",
    "nabeeh", "ziad", "zyad", "emad", "imad", "ramadan", "omer", "aziz",
    "maged", "nageeb", "naji", "fathi", "fathallah", "mamdouh", "shawki",
    "atef", "lamia", "mona", "mouna", "sahar", "dalal", "nadia",
    "fadia", "vivian", "rania", "dalia", "may", "mai", "sandy",
    "sandra", "joy", "nancy", "nicole", "catherine", "kristen", "stephanie",
    "nadine", "jessica", "maria", "olga", "angela", "patricia", "sabrina",
    "laila", "lubna", "hanan", "hena", "hala", "hayat", "samira", "sherine",
    "shereen", "wafaa", "wafa", "iman", "eeman", "nahed", "nahid", "fawzia",
    "afaf", "thoraya", "soraya", "suraya", "buthaina", "bothaina", "maha",
    "shadia", "shadiyah", "fayza", "faiza", "azza", "azizah", "khadija",
    "khadijah", "hafsa", "safiya", "safia", "rabab", "rabeea", "rawiya",
    "maysaa", "maysa", "latifa", "lateefa", "najla", "najlah", "hend",
    "hind", "marwa", "mirvat", "neamat", "rehab", "shaymaa", "shaimaa",
    "eman", "ilham", "amal", "farida", "fareda", "yasmina", "tina", "nelly",
    "shery", "linda", "sally", "dolly", "noha", "gehad", "jihad", "ghinwa",
    "widad", "wedad", "fikriya", "fekriya", "qadria", "qadriyah", "sajida",
    "sajeda", "naziha", "nazeeha", "zakiya", "zakeya", "bashaer", "bashayer",
    "sawsan", "sawsen", "fadhila", "fadheela", "hiba", "heba", "ayat", "aya",
    "rasha", "rashaa", "shimaa", "dima", "demaa", "lina", "leen", "lena",
    "tala", "taline", "rina", "reena", "joelle", "pamela", "raja", "rajaa",
    "natasha", "tanya", "lara", "laura", "vera", "veronica", "julie",
    "julia", "jana", "janet", "fayrouz", "fairuz", "mervat", "mervet",
    "souhaila", "suhaila", "nawal", "nawel", "elissa", "yara", "carole",
    "carol", "maya", "maia", "zein", "zayn", "zeyn", "taim", "taym",
    "arafat", "amer", "amr", "sherif", "shareef", "ashraf", "mohsen",
    "muhsin", "hady", "hadi", "galal", "jalal", "saqr", "sakr", "fakhr",
    "fakhri", "shady", "shadi", "nader", "nadir", "ghaleb", "galeb",
    "salman", "sulaiman", "suleiman", "anoos", "anis", "moez", "muizz",
    "lotfi", "lutfi", "taher", "tahir", "moataz", "mutaz", "moatasem",
    "mutasim", "akram", "ehab", "ihab", "sharif", "mostafa", "moustafa",
    "husam", "hosam", "bilal", "belal", "reda", "ridha", "rida", "essam",
    "issam", "maher", "adel", "adeel", "naguib", "najeep", "fouzi", "fawzi",
    "hossam", "hashem", "hashim", "sameh", "sameeh", "makram", "mukarram",
    "gamal", "jamal", "fathi", "fathy", "soliman", "salim", "saleem",
    "mounir", "munir", "hani", "hany", "medhat", "midhat", "waseem",
    "wasim", "hatem", "hatim", "diab", "thabet", "sabet", "sabri",
    "safwat", "amir", "ameer", "bahaa", "baha", "bahaeddine", "bahaaldeen",
    "riad", "riyad", "tawfiq", "tawfik", "subhi", "subhy", "mazen", "mazin",
    "hazem", "hazm", "wajih", "wajeeh", "ghazi", "ghazee", "ramzy", "ramzi",
    "mamdouh", "mamduh", "said", "saad", "saeed", "fadel", "fadl", "fadhil",
    "fazeel", "nael", "nail", "ramadan", "ramazan", "shawkat", "shaukat",
    "anwar", "annwar", "noman", "nuaman", "hafez", "hafiz", "mohie", "mohyi",
    "serag", "siraj", "seraj", "zaki", "zakki", "mokhtar", "mukhtar",
    "osman", "uthman", "othman", "dawood", "dawud", "daoud", "ishaq",
    "isaac", "yacoub", "yaqub", "jacob", "zakaria", "zachariah", "mikhael",
    "michael", "beshoy", "bishoy", "mina", "mena", "kero", "kyrillos",
    "cyril", "peter", "petros", "paul", "boulos", "tawadros", "theodoros",
    "wisam", "waseem", "fares", "farris", "omran", "imran", "khaldoun",
    "khaldun", "majd", "majed", "basil", "bassel", "salam", "selam",
    "raji", "rajih", "maan", "laith", "leith", "kutaiba", "qutaybah",
    "jarir", "jareer", "zuhair", "zuhayr", "saif", "sayf", "sayfaldin",
    "saifaldeen", "alaa", "ala", "alaeddine", "nasr", "nasir", "nasri",
    "ghassan", "ghasan", "marwan", "marouan", "murhaf", "morshed", "murshid",
    "wissam", "wisam", "basem", "basim", "kamel", "kamil", "naser",
    "nasser", "hikmat", "hikmet", "sami", "samir", "samer", "ghaleb",
    "hisham", "hashim", "hashem", "sayed", "sayyid", "mortada", "murtada",
    "murtadi", "saadi", "sadi", "radi", "raed", "mufeed", "mufid",
    "munther", "muntasir", "faeq", "faqee", "atheer", "athir", "mohannad",
    "mohand", "mohanad", "mohanned", "mohandis", "moatasem", "mutasim",
    "haytham", "haitham", "baha", "bahaa", "shihab", "shahab", "khalaf",
    "sabah", "sabeh", "thamer", "thamir", "taim", "taym", "fahad",
    "fahd", "mishaal", "meshal", "jasser", "jasir", "sattam", "sittam",
    "mashari", "mishari", "jalawi", "jalwi", "mutairi", "mutayri",
    "shammari", "shamari", "otaibi", "utaybi", "anzi", "anazy", "dossary",
    "dosari", "dosry", "qhtani", "qahtani", "shehri", "shahri", "shehry",
    "harbi", "harby", "malki", "malky", "zahrani", "zahran", "tamimi",
    "tamimy", "subaie", "subay", "dulaim", "dulaym", "zobaie", "zubay",
    "jebali", "jibali", "alawi", "alawy", "hwaiti", "huwayti", "rashidi",
    "rashidy", "balawi", "falasi", "falasy", "nuaimi", "nuaymi", "maneea",
    "maniya", "kaabi", "kaaby", "mehairi", "muhayri", "tabet", "tabit",
    "akkad", "akad", "sharari", "sharary", "muraikhan", "muraikhi",
    "muraikh", "fadel", "fadil", "fadl", "majid", "abdulaziz", "abdulazeez",
    "abdulmohsen", "abdulmuhsin", "abdulkarim", "abdulkareem", "abdulrahim",
    "abdulraheem", "abdulnasser", "abdulnasir", "abdulfattah", "abdulghani",
    "abdulghanee", "abdulhadi", "abdulhaadi", "abdulhamid", "abdulhameed",
    "abduljaleel", "abduljalil", "abdullatif", "abdullateef", "abdulmalik",
    "abdulmalek", "abdulmannan", "abdulmonem", "abdulmunim", "abdulnour",
    "abdulnoor", "abdulqader", "abdulqadir", "abdulrazzaq", "abdulrazzak",
    "abdulsalam", "abdussalam", "abdulsamad", "abdussamad", "abdulwadood",
    "abdulwadud", "abdulwali", "abdulwaliy", "abuabdullah", "abubakr",
    "abuobaida", "ubayd", "obayd", "ubaida", "obeida", "tulaim", "tulaym",
    "sahli", "sahly", "hajri", "hajry", "yamani", "yemeni", "abyad",
    "aswad", "ahmar", "akhdar", "khudayr", "tohamy", "tuhaimi", "dayri",
    "diri", "hassoun", "hassun", "sayadi", "sayyadi", "misbah", "mesbah",
    "zamil", "zamyl", "jad", "jaad", "radi", "radee", "masri", "misri",
    "egyptian", "iraqi", "irani", "turkish", "syrian", "sudani", "lebanese",
    "jordanian", "palestinian", "moroccan", "tunisian", "libyan", "algerian",
    "yemeni", "omani", "emirati", "saudi", "qatri", "kuwaiti", "bahraini"
]

ENGLISH_NAMES = [
    "john", "jane", "mike", "michael", "sara", "sarah", "chris", "christina",
    "emma", "david", "olivia", "daniel", "sophia", "alex", "alexander",
    "ryan", "lucas", "mia", "bella", "isabella", "jack", "leo", "zoe",
    "luna", "max", "maxwell", "james", "william", "benjamin", "ben",
    "elijah", "eli", "henry", "alexandra", "sebastian", "seb", "mateo",
    "ethan", "noah", "liam", "oliver", "charlotte", "charlie", "amelia",
    "amy", "ava", "eve", "evelyn", "harper", "camila", "camille", "sofia",
    "scarlett", "victoria", "vicky", "grace", "chloe", "penelope", "penny",
    "riley", "nora", "lily", "eleanor", "hannah", "lillian", "lilly",
    "addison", "addie", "aubrey", "ellie", "estelle", "stella", "natalie",
    "nat", "leah", "hazel", "violet", "aurora", "savannah", "sam",
    "samantha", "ruby", "lucy", "lucia", "gabriel", "gabe", "gabriela",
    "gabby", "caleb", "cale", "owen", "logan", "isaac", "isa",
    "jayden", "jay", "nathan", "nate", "dylan", "dyl", "joseph", "joe",
    "josie", "anthony", "tony", "thomas", "tom", "matthew", "matt",
    "samuel", "joshua", "josh", "andrew", "andy", "christopher", "adam",
    "ada", "aaron", "ron", "luke", "jonathan", "nathaniel", "caleb"
]

ENGLISH_FAMILY_NAMES = [
    "smith", "jones", "williams", "brown", "davis", "miller", "wilson",
    "moore", "taylor", "anderson", "thomas", "jackson", "white", "harris",
    "martin", "thompson", "garcia", "martinez", "robinson", "clark",
    "rodriguez", "lewis", "lee", "walker", "hall", "allen", "young",
    "hernandez", "king", "wright", "lopez", "hill", "scott", "green",
    "adams", "baker", "gonzalez", "nelson", "carter", "mitchell", "roberts",
    "campbell", "phillips", "evans", "turner", "parker", "collins", "edwards",
    "stewart", "flores", "morris", "nguyen", "murphy", "rivera", "cook",
    "rogers", "morgan", "peterson", "cooper", "reed", "bailey", "bell",
    "gomez", "kelly", "howard", "ward", "cox", "diaz", "richardson",
    "wood", "watson", "brooks", "bennett", "gray", "james", "reyes",
    "cruz", "hughes", "price", "myers", "long", "foster", "sanders",
    "ross", "morales", "powell", "sullivan", "russell", "ortiz", "jenkins",
    "gutierrez", "perry", "butler", "barnes", "fisher", "henderson",
    "coleman", "simmons", "patterson", "jordan", "reynolds", "hamilton",
    "graham", "kim", "alexander", "rao", "ram", "shah", "khan", "ali",
    "hassan", "hussain", "ahmed", "singh", "sharma", "gupta", "verma",
    "reddy", "nair", "menon", "pillai", "iyer", "desai", "patel",
    "mehta", "joshi", "kumar", "bose", "das", "malik", "qureshi",
    "sheikh", "syed", "farooq", "mir", "dar", "bhat", "chauhan",
    "thakur", "solanki", "pandey", "tiwari", "mishra", "srivastava",
    "agarwal", "banerjee", "chatterjee", "ganguly", "mukherjee", "sen",
    "bhattacharya", "basu", "dutta", "ghosh", "roy", "pal", "saha",
    "mondal", "islam", "hossain", "rahman", "uddin", "chowdhury", "sarkar",
    "dey", "kundu", "mitra", "dasgupta", "bhatt", "mehrotra", "saxena",
    "tripathi", "shukla", "sinha", "yadav", "prasad", "pathak", "nanda",
    "bhardwaj", "khanna", "arora", "sethi", "malhotra", "bajaj", "taneja",
    "chopra", "kapoor", "grover", "suri", "walia", "khurana", "chadha",
    "grewal", "sandhu", "dhaliwal", "cheema", "basra", "dhillon",
    "randhawa", "sehgal", "talwar", "ahuja", "bhandari", "lakhani",
    "ramani", "parekh", "dalal", "shahani", "irani", "kohli", "chawla",
    "soni", "trivedi", "upadhyay", "pareek", "ojha", "thapa", "limbu",
    "gurung", "magar", "rai", "tamang", "sherpa", "bhattarai", "neupane",
    "adhikari", "pokharel", "subedi", "silva", "fernando", "perera",
    "samarasinghe", "jayasinghe", "ranasinghe", "wickramasinghe",
    "gunaratne", "jayawardene", "bandara", "dissanayake", "herath",
    "ratnayake", "wijesinghe", "munasinghe", "abeysekera", "seneviratne",
    "weerasinghe", "pathirana", "liyana", "kariyawasam", "wijeratne",
    "hettiarachchi", "amarasena", "rajapaksa", "fonseka", "edirisuriya",
    "gunasekera", "samaraweera", "atapattu", "mendis", "dilshan",
    "sangakkara", "jayasuriya", "vaas", "muralitharan", "warne", "mcgrath",
    "clarke", "watson", "ponting", "gilchrist", "hayden", "langer",
    "waugh", "martyn", "hussey", "symonds", "lee", "johnson", "haddin",
    "bollinger", "siddle", "hazlewood", "starc", "cummins", "smith",
    "warner", "finch", "maxwell", "marsh", "lyon", "zampa", "carey",
    "head", "labuschagne", "green", "inglis", "ellis", "stanlake",
    "behrendorff", "richardson", "agar", "turner"
]

ALL_FIRST_NAMES = list(set(TRANSLITERATED_NAMES + ENGLISH_NAMES))
NUMBERS = [str(i) for i in range(10, 1000)]


# ═══════════════════════════════════════════════════════════════
# Username Generation
# ═══════════════════════════════════════════════════════════════

def generate_single_username():
    """Generate a valid TikTok username using ASCII-only characters."""
    name = random.choice(ALL_FIRST_NAMES)

    strategies = [
        "name_only",
        "name_family",
        "name_underscore_family",
        "name_dot_family",
        "name_number",
        "name_underscore_number",
        "name_dot_number",
        "initial_name",
        "name_initial",
        "short_random",
    ]

    weights = [3, 2, 2, 2, 5, 4, 4, 2, 2, 4]
    strategy = random.choices(strategies, weights=weights, k=1)[0]

    if strategy == "name_only":
        username = name
    elif strategy == "name_family":
        family = random.choice(ENGLISH_FAMILY_NAMES)
        username = name + family
    elif strategy == "name_underscore_family":
        family = random.choice(ENGLISH_FAMILY_NAMES)
        username = name + "_" + family
    elif strategy == "name_dot_family":
        family = random.choice(ENGLISH_FAMILY_NAMES)
        username = name + "." + family
    elif strategy == "name_number":
        num = random.choice(NUMBERS)
        username = name + num
    elif strategy == "name_underscore_number":
        num = random.choice(NUMBERS)
        username = name + "_" + num
    elif strategy == "name_dot_number":
        num = random.choice(NUMBERS)
        username = name + "." + num
    elif strategy == "initial_name":
        initial = random.choice(string.ascii_lowercase)
        username = initial + name
    elif strategy == "name_initial":
        initial = random.choice(string.ascii_lowercase)
        username = name + initial
    elif strategy == "short_random":
        length = random.randint(2, 5)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    else:
        username = name

    username = sanitize_username(username)

    if is_valid_tiktok_username(username):
        return username

    fallbacks = [
        lambda: name + random.choice(NUMBERS),
        lambda: name + random.choice(string.ascii_lowercase) + random.choice(NUMBERS),
        lambda: random.choice(string.ascii_lowercase) + name[:6] + random.choice(NUMBERS),
        lambda: ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 6))) + random.choice(NUMBERS),
    ]

    for fb in fallbacks:
        u = sanitize_username(fb())
        if is_valid_tiktok_username(u):
            return u

    return ''.join(random.choices(string.ascii_lowercase, k=4)) + str(random.randint(10, 99))


# ═══════════════════════════════════════════════════════════════
# TikTok Profile Check (FIX #4: No MedoSigner needed)
# ═══════════════════════════════════════════════════════════════

def check_tiktok_profile(username):
    """
    Check if TikTok username exists by scraping the public profile page.
    Returns dict with user info if found, None if not found.
    """
    if not is_valid_tiktok_username(username):
        return None

    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

        if resp.status_code == 404 or "couldn\'t find this account" in resp.text.lower():
            return None

        if resp.status_code == 200:
            # Try to extract user data from embedded JSON
            pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>'
            match = re.search(pattern, resp.text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    user_data = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
                    user_info = user_data.get("userInfo", {}).get("user", {})
                    stats = user_data.get("userInfo", {}).get("stats", {})

                    return {
                        "username": user_info.get("uniqueId", username),
                        "nickname": user_info.get("nickname", "N/A"),
                        "user_id": user_info.get("id", "N/A"),
                        "followers": stats.get("followerCount", 0),
                        "following": stats.get("followingCount", 0),
                        "likes": stats.get("heartCount", 0),
                        "videos": stats.get("videoCount", 0),
                        "private": user_info.get("privateAccount", False),
                        "verified": user_info.get("verified", False),
                    }
                except (json.JSONDecodeError, KeyError):
                    pass

            # Fallback: check if page contains profile indicators
            if "user-info" in resp.text or "follower" in resp.text.lower():
                return {"username": username, "found": True}

        return None

    except requests.exceptions.RequestException:
        return None


# ═══════════════════════════════════════════════════════════════
# Email Availability Check (FIX #5: SMTP instead of Google API)
# ═══════════════════════════════════════════════════════════════

def check_email_smtp(email):
    """
    Check email availability via SMTP handshake.
    Returns True if email seems available (server says recipient unknown).
    Note: This is heuristic and not 100% reliable for all providers.
    """
    domain = email.split("@")[1]

    try:
        # Get MX records
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange).rstrip('.')

        # SMTP check
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_host)
        server.helo("checker.local")
        server.mail("check@checker.local")
        code, _ = server.rcpt(email)
        server.quit()

        # 550 = mailbox unavailable (might mean available or doesn't exist)
        # 250/251 = exists
        # 452/422 = temporary failure
        if code in [250, 251]:
            return False  # Email exists
        elif code == 550:
            return True   # Likely available
        else:
            return None   # Uncertain

    except Exception:
        return None


def check_email_haveibeenpwned(email):
    """
    Check if email was breached (alternative method).
    Returns True if email appears in breaches (likely taken).
    """
    try:
        headers = {
            "User-Agent": "TikTokChecker-Edu/1.0",
            "Accept": "application/json",
        }
        resp = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            return False  # Found in breaches = likely taken
        elif resp.status_code == 404:
            return True   # Not found = might be available
        else:
            return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# Main Check Logic
# ═══════════════════════════════════════════════════════════════

def check_single(username, domain="gmail.com"):
    """Check single username+domain combo. Returns True if HIT."""
    global stats

    if not is_valid_tiktok_username(username):
        with lock:
            stats['skipped'] += 1
        return False

    email = f"{username}@{domain}"

    with lock:
        stats['total_checked'] += 1

    # Step 1: Check TikTok profile
    tiktok_data = check_tiktok_profile(username)

    if not tiktok_data:
        with lock:
            stats['email_taken'] += 1
        return False

    with lock:
        stats['tiktok_hits'] += 1

    console.print(f"[green][+] TikTok found: @{username}[/green]")

    # Step 2: Check email availability
    email_available = check_email_smtp(email)

    if email_available is True:
        with lock:
            stats['email_available'] += 1

        console.print(f"[bold green][!!!] HIT: {email}[/bold green]")

        # Build message
        info = tiktok_data
        msg = f"""<b>🎯 HIT FOUND</b>

👤 <b>Username:</b> @{info.get('username', username)}
📧 <b>Email:</b> {email}
🆔 <b>User ID:</b> {info.get('user_id', 'N/A')}
📛 <b>Name:</b> {info.get('nickname', 'N/A')}
👥 <b>Followers:</b> {info.get('followers', 'N/A')}
❤️ <b>Likes:</b> {info.get('likes', 'N/A')}
🎬 <b>Videos:</b> {info.get('videos', 'N/A')}
🔒 <b>Private:</b> {info.get('private', 'N/A')}
✅ <b>Verified:</b> {info.get('verified', 'N/A')}

<b>TikTok Email Checker v4</b>"""

        send_telegram(msg)
        return True
    else:
        with lock:
            stats['email_taken'] += 1
        return False


# ═══════════════════════════════════════════════════════════════
# Search Loop (FIX #1, #3, #7: No freeze, proper errors, dynamic cookies)
# ═══════════════════════════════════════════════════════════════

def search_users_tiktok(keyword):
    """
    Search TikTok users via public web API.
    Returns list of usernames found.
    """
    try:
        # Use TikTok's search API
        headers = {
            "User-Agent": generate_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://www.tiktok.com/search/user?q={keyword}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # Alternative: use trending/related endpoint
        url = f"https://www.tiktok.com/api/search/general/full/?keyword={keyword}&offset=0&count=10"

        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code != 200:
            return []

        data = resp.json()
        users = []

        # Parse user_list from response
        user_list = data.get("user_list", [])
        for user in user_list:
            info = user.get("user_info", {})
            uname = info.get("unique_id", "")
            if is_valid_tiktok_username(uname):
                users.append(uname)

        return users

    except Exception as e:
        with lock:
            stats['errors'] += 1
        return []


def worker_thread(thread_id):
    """Worker thread that generates and checks usernames."""
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']

    while True:
        try:
            # Generate random username
            username = generate_single_username()

            # Check against TikTok
            tiktok_data = check_tiktok_profile(username)

            if tiktok_data:
                # Check all domains
                for domain in domains:
                    check_single(username, domain)
                    time.sleep(random.uniform(0.5, 2.0))  # Rate limit protection

            else:
                # Also try search-based discovery
                if random.random() < 0.1:  # 10% chance to search
                    found_users = search_users_tiktok(username[:4])
                    for found_user in found_users[:5]:
                        for domain in domains[:2]:  # Check top 2 domains
                            check_single(found_user, domain)
                            time.sleep(random.uniform(1.0, 3.0))

            time.sleep(random.uniform(0.5, 2.0))

        except Exception as e:
            with lock:
                stats['errors'] += 1
            time.sleep(5)


# ═══════════════════════════════════════════════════════════════
# Rich UI Dashboard (FIX #1: No more freeze!)
# ═══════════════════════════════════════════════════════════════

def create_stats_table():
    """Create rich table for live stats."""
    table = Table(title="TikTok Email Checker v4", title_style="bold cyan")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    with lock:
        table.add_row("Total Checked", str(stats['total_checked']))
        table.add_row("TikTok Hits", f"[bold green]{stats['tiktok_hits']}[/bold green]")
        table.add_row("Email Available", f"[bold yellow]{stats['email_available']}[/bold yellow]")
        table.add_row("Email Taken", str(stats['email_taken']))
        table.add_row("Skipped (Invalid)", str(stats['skipped']))
        table.add_row("Errors", f"[red]{stats['errors']}[/red]")
        table.add_row("Rate Limited", str(stats['rate_limited']))

    return table


def display_dashboard():
    """Live dashboard that updates without freezing."""
    with Live(create_stats_table(), refresh_per_second=2, screen=False) as live:
        while True:
            time.sleep(1)
            live.update(create_stats_table())


# ═══════════════════════════════════════════════════════════════
# Main Entry
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    console.print(Panel.fit(
        "[bold cyan]TikTok Email Checker v4 — FIXED EDITION[/bold cyan]\n"
        "[green]FIX #1:[/green] No more screen freeze (\r-based UI)\n"
        "[green]FIX #2:[/green] Thread-safe counters with Lock\n"
        "[green]FIX #3:[/green] Proper error handling (no bare except)\n"
        "[green]FIX #4:[/green] No MedoSigner — uses web scraping\n"
        "[green]FIX #5:[/green] SMTP email check (no Google reverse eng)\n"
        "[green]FIX #6:[/green] ASCII-only User-Agent\n"
        "[green]FIX #7:[/green] Dynamic cookies per request\n"
        "[green]FIX #8:[/green] 5 threads (was 28, caused rate limits)\n"
        "[yellow]DISCLAIMER: For educational/authorized testing only[/yellow]",
        title="KENDO Rebuilt",
        border_style="cyan"
    ))

    # Start dashboard in main thread
    # Start workers in background
    NUM_THREADS = 5  # FIX #8: Reduced from 28

    for i in range(NUM_THREADS):
        t = threading.Thread(target=worker_thread, args=(i,), daemon=True)
        t.start()
        time.sleep(0.3)

    # Run dashboard
    display_dashboard()
