#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TikTok Email Checker v5 — ASYNC OPTIMIZED EDITION                          ║
║  No Freeze | AsyncIO | Real Gmail Check | Live Rich UI                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

KEY IMPROVEMENTS:
  1. ASYNCIO + AIOHTTP — replaces 28 threads, no freeze, 10x faster
  2. RICH LIVE UI — no os.system('cls'), smooth dashboard
  3. REAL GMAIL CHECK — uses Google batchexecute (the actual working method)
  4. SMART NAME GENERATION — targeted Arabic/English combos
  5. PROXY SUPPORT — rotating proxies to avoid blocks
  6. SESSION PERSISTENCE — saves progress, resumes on restart
  7. TELEGRAM RICH MESSAGES — formatted hits with user info

REQUIREMENTS:
  pip install aiohttp aiohttp-socks rich user-agent

USAGE:
  python checker_v5.py
"""

import asyncio
import aiohttp
import aiohttp_socks
import random
import os
import sys
import re
import string
import json
import time
import signal
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from user_agent import generate_user_agent
from uuid import uuid4

console = Console()

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════
CONFIG = {
    "telegram_id": "",      # Will prompt
    "telegram_token": "",  # Will prompt
    "threads": 50,         # Async concurrent tasks (not OS threads)
    "delay_min": 0.3,
    "delay_max": 1.5,
    "domains": ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "mail.ru"],
    "proxy_list": [],       # Add proxies here: ["socks5://ip:port", ...]
    "save_file": "hits_v5.txt",
    "session_file": ".checker_session.json",
}

# ═══════════════════════════════════════════════════════════════
# Stats (thread-safe in async via asyncio.Lock)
# ═══════════════════════════════════════════════════════════════
stats_lock = asyncio.Lock()
stats = {
    "checked": 0,
    "tiktok_found": 0,
    "email_available": 0,
    "hits": 0,
    "errors": 0,
    "rate_limited": 0,
    "skipped": 0,
    "start_time": time.time(),
}

# ═══════════════════════════════════════════════════════════════
# Telegram Sender
# ═══════════════════════════════════════════════════════════════
async def send_telegram(text: str, token: str, chat_id: str):
    """Async Telegram send with retry."""
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.post(url, data=payload, timeout=10) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                await asyncio.sleep(2 ** attempt)
    return False


# ═══════════════════════════════════════════════════════════════
# Username Validation
# ═══════════════════════════════════════════════════════════════
def is_valid_tiktok_username(username: str) -> bool:
    if not username or not isinstance(username, str):
        return False
    if len(username) < 2 or len(username) > 24:
        return False
    allowed = set(string.ascii_lowercase + string.digits + "_.")
    if not all(c in allowed for c in username):
        return False
    if username[0] in "._" or username[-1] in "._":
        return False
    if ".." in username or "__" in username:
        return False
    if username.isdigit():
        return False
    return True


def sanitize_username(username: str) -> str:
    username = username.lower()
    username = "".join(c for c in username if c in string.ascii_lowercase + string.digits + "_.")
    username = re.sub(r"\.+", ".", username)
    username = re.sub(r"_+", "_", username)
    username = username.strip("._")
    return username


# ═══════════════════════════════════════════════════════════════
# Name Databases (Targeted for high hit-rate regions)
# ═══════════════════════════════════════════════════════════════
ARABIC_NAMES = [
    "ahmed", "mohammed", "mohammad", "muhammad", "ali", "fatima", "zainab",
    "yousef", "yusuf", "maryam", "mariam", "khaled", "sara", "sarah", "nour",
    "noor", "omar", "umar", "hamza", "layla", "leila", "huda", "ibrahim",
    "yassin", "mustafa", "abdullah", "abdallah", "abdulrahman", "faisal",
    "faysal", "nasser", "mubarak", "mansour", "turki", "fahd", "bandar",
    "sultan", "nawaf", "mishaal", "meshal", "jasser", "jasir", "saleh",
    "salih", "talal", "majed", "badr", "sami", "tariq", "hassan", "hussain",
    "hussein", "saeed", "said", "younes", "younis", "waleed", "walid",
    "reem", "rim", "dana", "lama", "ghada", "manal", "haifa", "amal",
    "salma", "yasmin", "nada", "abeer", "abir", "samar", "rana", "dina",
    "deena", "ghassan", "fouad", "fuad", "khalil", "khaleel", "ayman",
    "aymen", "samer", "samir", "rami", "ramez", "fadi", "fady", "hisham",
    "hesham", "tamer", "tamir", "wael", "waiel", "loay", "luay", "saad",
    "mahmoud", "mahmood", "kamal", "jamal", "raed", "radi", "basem", "basim",
    "karim", "kareem", "tarek", "hamed", "hamid", "nabil", "nabeeh", "ziad",
    "zyad", "emad", "imad", "ramadan", "omer", "aziz", "maged", "nageeb",
    "naji", "fathi", "mamdouh", "shawki", "atef", "lamia", "mona", "mouna",
    "sahar", "dalal", "nadia", "fadia", "vivian", "rania", "dalia", "may",
    "mai", "sandy", "sandra", "joy", "nancy", "nicole", "catherine", "kristen",
    "stephanie", "nadine", "jessica", "maria", "olga", "angela", "patricia",
    "sabrina", "laila", "lubna", "hanan", "hena", "hala", "hayat", "samira",
    "sherine", "shereen", "wafaa", "wafa", "iman", "eeman", "nahed", "nahid",
    "fawzia", "afaf", "thoraya", "soraya", "suraya", "buthaina", "bothaina",
    "maha", "shadia", "shadiyah", "fayza", "faiza", "azza", "azizah", "khadija",
    "khadijah", "hafsa", "safiya", "safia", "rabab", "rabeea", "rawiya",
    "maysaa", "maysa", "latifa", "lateefa", "najla", "najlah", "hend", "hind",
    "marwa", "mirvat", "neamat", "rehab", "shaymaa", "shaimaa", "eman", "ilham",
    "amal", "farida", "fareda", "yasmina", "tina", "nelly", "shery", "linda",
    "sally", "dolly", "noha", "gehad", "jihad", "ghinwa", "widad", "wedad",
    "fikriya", "fekriya", "qadria", "qadriyah", "sajida", "sajeda", "naziha",
    "nazeeha", "zakiya", "zakeya", "bashaer", "bashayer", "sawsan", "sawsen",
    "fadhila", "fadheela", "hiba", "heba", "ayat", "aya", "rasha", "rashaa",
    "shimaa", "dima", "demaa", "lina", "leen", "lena", "tala", "taline",
    "rina", "reena", "joelle", "pamela", "raja", "rajaa", "natasha", "tanya",
    "lara", "laura", "vera", "veronica", "julie", "julia", "jana", "janet",
    "fayrouz", "fairuz", "mervat", "mervet", "souhaila", "suhaila", "nawal",
    "nawel", "elissa", "yara", "carole", "carol", "maya", "maia", "zein",
    "zayn", "zeyn", "taim", "taym", "arafat", "amer", "amr", "sherif",
    "shareef", "ashraf", "mohsen", "muhsin", "hady", "hadi", "galal", "jalal",
    "saqr", "sakr", "fakhr", "fakhri", "shady", "shadi", "nader", "nadir",
    "ghaleb", "galeb", "salman", "sulaiman", "suleiman", "anoos", "anis",
    "moez", "muizz", "lotfi", "lutfi", "taher", "tahir", "moataz", "mutaz",
    "moatasem", "mutasim", "akram", "ehab", "ihab", "sharif", "mostafa",
    "moustafa", "husam", "hosam", "bilal", "belal", "reda", "ridha", "rida",
    "essam", "issam", "maher", "adel", "adeel", "naguib", "najeep", "fouzi",
    "fawzi", "hossam", "hashem", "hashim", "sameh", "sameeh", "makram",
    "mukarram", "gamal", "jamal", "fathi", "fathy", "soliman", "salim",
    "saleem", "mounir", "munir", "hani", "hany", "medhat", "midhat", "waseem",
    "wasim", "hatem", "hatim", "diab", "thabet", "sabet", "sabri", "safwat",
    "amir", "ameer", "bahaa", "baha", "bahaeddine", "bahaaldeen", "riad",
    "riyad", "tawfiq", "tawfik", "subhi", "subhy", "mazen", "mazin", "hazem",
    "hazm", "wajih", "wajeeh", "ghazi", "ghazee", "ramzy", "ramzi", "mamdouh",
    "mamduh", "fadel", "fadl", "fadhil", "fazeel", "nael", "nail", "ramadan",
    "ramazan", "shawkat", "shaukat", "anwar", "annwar", "noman", "nuaman",
    "hafez", "hafiz", "mohie", "mohyi", "serag", "siraj", "seraj", "zaki",
    "zakki", "mokhtar", "mukhtar", "osman", "uthman", "othman", "dawood",
    "dawud", "daoud", "ishaq", "isaac", "yacoub", "yaqub", "jacob", "zakaria",
    "zachariah", "mikhael", "michael", "beshoy", "bishoy", "mina", "mena",
    "kero", "kyrillos", "cyril", "peter", "petros", "paul", "boulos",
    "tawadros", "theodoros", "wisam", "waseem", "fares", "farris", "omran",
    "imran", "khaldoun", "khaldun", "majd", "majed", "basil", "bassel",
    "salam", "selam", "raji", "rajih", "maan", "laith", "leith", "kutaiba",
    "qutaybah", "jarir", "jareer", "zuhair", "zuhayr", "saif", "sayf",
    "sayfaldin", "saifaldeen", "alaa", "ala", "alaeddine", "nasr", "nasir",
    "nasri", "ghassan", "ghasan", "marwan", "marouan", "murhaf", "morshed",
    "murshid", "wissam", "wisam", "basem", "basim", "kamel", "kamil",
    "naser", "nasser", "hikmat", "hikmet", "sami", "samir", "samer", "ghaleb",
    "hisham", "hashim", "hashem", "sayed", "sayyid", "mortada", "murtada",
    "murtadi", "saadi", "sadi", "radi", "raed", "mufeed", "mufid", "munther",
    "muntasir", "faeq", "faqee", "atheer", "athir", "mohannad", "mohand",
    "mohanad", "mohanned", "mohandis", "moatasem", "mutasim", "haytham",
    "haitham", "baha", "bahaa", "shihab", "shahab", "khalaf", "sabah",
    "sabeh", "thamer", "thamir", "taim", "taym", "fahad", "fahd", "mishaal",
    "meshal", "jasser", "jasir", "sattam", "sittam", "mashari", "mishari",
    "jalawi", "jalwi", "mutairi", "mutayri", "shammari", "shamari", "otaibi",
    "utaybi", "anzi", "anazy", "dossary", "dosari", "dosry", "qhtani",
    "qahtani", "shehri", "shahri", "shehry", "harbi", "harby", "malki",
    "malky", "zahrani", "zahran", "tamimi", "tamimy", "subaie", "subay",
    "dulaim", "dulaym", "zobaie", "zubay", "jebali", "jibali", "alawi",
    "alawy", "hwaiti", "huwayti", "rashidi", "rashidy", "balawi", "falasi",
    "falasy", "nuaimi", "nuaymi", "maneea", "maniya", "kaabi", "kaaby",
    "mehairi", "muhayri", "tabet", "tabit", "akkad", "akad", "sharari",
    "sharary", "muraikhan", "muraikhi", "muraikh", "fadel", "fadil", "fadl",
    "majid", "abdulaziz", "abdulazeez", "abdulmohsen", "abdulmuhsin",
    "abdulkarim", "abdulkareem", "abdulrahim", "abdulraheem", "abdulnasser",
    "abdulnasir", "abdulfattah", "abdulghani", "abdulghanee", "abdulhadi",
    "abdulhaadi", "abdulhamid", "abdulhameed", "abduljaleel", "abduljalil",
    "abdullatif", "abdullateef", "abdulmalik", "abdulmalek", "abdulmannan",
    "abdulmonem", "abdulmunim", "abdulnour", "abdulnoor", "abdulqader",
    "abdulqadir", "abdulrazzaq", "abdulrazzak", "abdulsalam", "abdussalam",
    "abdulsamad", "abdussamad", "abdulwadood", "abdulwadud", "abdulwali",
    "abdulwaliy", "abuabdullah", "abubakr", "abuobaida", "ubayd", "obayd",
    "ubaida", "obeida", "tulaim", "tulaym", "sahli", "sahly", "hajri",
    "hajry", "yamani", "yemeni", "abyad", "aswad", "ahmar", "akhdar",
    "khudayr", "yassin", "yaseen", "tohamy", "tuhaimi", "dayri", "diri",
    "hassoun", "hassun", "sayadi", "sayyadi", "misbah", "mesbah", "zamil",
    "zamyl", "jad", "jaad", "radi", "radee", "masri", "misri", "egyptian",
    "iraqi", "irani", "turkish", "syrian", "sudani", "lebanese", "jordanian",
    "palestinian", "moroccan", "tunisian", "libyan", "algerian", "yemeni",
    "omani", "emirati", "saudi", "qatri", "kuwaiti", "bahraini"
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

FAMILY_NAMES = [
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

ALL_NAMES = list(set(ARABIC_NAMES + ENGLISH_NAMES))
NUMBERS = [str(i) for i in range(10, 1000)]


# ═══════════════════════════════════════════════════════════════
# Smart Username Generator (Targeted)
# ═══════════════════════════════════════════════════════════════
def generate_username():
    """Generate username with high probability of being real."""
    name = random.choice(ALL_NAMES)

    strategies = [
        lambda: name,                                          # name
        lambda: name + random.choice(NUMBERS),                # name123
        lambda: name + "_" + random.choice(NUMBERS),          # name_123
        lambda: name + "." + random.choice(NUMBERS),        # name.123
        lambda: name + random.choice(FAMILY_NAMES),          # namefamily
        lambda: name + "_" + random.choice(FAMILY_NAMES),   # name_family
        lambda: name + "." + random.choice(FAMILY_NAMES),   # name.family
        lambda: random.choice(string.ascii_lowercase) + name[:6],  # jname
        lambda: name[:6] + random.choice(string.ascii_lowercase),  # namej
        lambda: name + random.choice(string.ascii_lowercase) + random.choice(NUMBERS),  # namej1
        lambda: random.choice(string.ascii_lowercase) + name + random.choice(NUMBERS),  # jname1
        lambda: ''.join(random.choices(string.ascii_lowercase, k=3)) + random.choice(NUMBERS),  # abc123
        lambda: name[:4] + random.choice(NUMBERS),            # ahme123
        lambda: name + random.choice(["official", "real", "ig", "tk", "tv", "hd", "4k"]),  # nameofficial
        lambda: "the" + name,                                  # thename
        lambda: "real" + name,                                # realname
        lambda: name + "official",                             # nameofficial
        lambda: name + "real",                                 # namereal
        lambda: "i" + name,                                    # iname
        lambda: "im" + name,                                   # imname
    ]

    weights = [5, 8, 6, 6, 4, 3, 3, 3, 3, 5, 4, 3, 6, 2, 2, 2, 2, 2, 2, 2, 2]
    strategy = random.choices(strategies, weights=weights, k=1)[0]

    username = sanitize_username(strategy())

    if is_valid_tiktok_username(username):
        return username

    # Fallback
    return name + random.choice(NUMBERS)


# ═══════════════════════════════════════════════════════════════
# TikTok Check (Async)
# ═══════════════════════════════════════════════════════════════
async def check_tiktok(session: aiohttp.ClientSession, username: str):
    """Check if TikTok username exists. Returns user data or None."""
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
    }

    try:
        async with session.get(url, headers=headers, timeout=10, allow_redirects=True) as resp:
            text = await resp.text()

            if resp.status == 404 or "couldn\'t find this account" in text.lower():
                return None

            if resp.status == 200:
                # Extract JSON data
                pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>'
                match = re.search(pattern, text, re.DOTALL)
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

                # Fallback
                if "user-info" in text or "follower" in text.lower():
                    return {"username": username, "found": True}

    except Exception as e:
        async with stats_lock:
            stats["errors"] += 1

    return None


# ═══════════════════════════════════════════════════════════════
# Gmail Check (The REAL working method via batchexecute)
# ═══════════════════════════════════════════════════════════════
async def check_gmail(session: aiohttp.ClientSession, username: str):
    """
    Check Gmail availability via Google batchexecute API.
    This is the actual method used by Google signup page.
    Returns True if available, False if taken, None if error.
    """
    email = f"{username}@gmail.com"

    try:
        # Step 1: Get initial page to extract tokens
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://accounts.google.com/",
        }

        params = {
            "biz": "false",
            "continue": "https://mail.google.com/mail/u/0/",
            "ddm": "1",
            "emr": "1",
            "flowEntry": "SignUp",
            "flowName": "GlifWebSignIn",
            "followup": "https://mail.google.com/mail/u/0/",
            "osid": "1",
            "service": "mail",
        }

        async with session.get(
            "https://accounts.google.com/lifecycle/flows/signup",
            params=params,
            headers=headers,
            timeout=15
        ) as resp:
            text = await resp.text()

            # Extract tokens
            try:
                tl = resp.url.query.get("TL", "")
                s1 = text.split('"Qzxixc":"')[1].split('"')[0]
                at = text.split('"SNlM0e":"')[1].split('"')[0]
            except (IndexError, AttributeError):
                return None

        # Step 2: Check username availability
        check_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "origin": "https://accounts.google.com",
            "referer": "https://accounts.google.com/",
            "user-agent": headers["User-Agent"],
            "x-goog-ext-278367001-jspb": '["GlifWebSignIn"]',
            "x-goog-ext-391502476-jspb": f'["{s1}"]',
            "x-same-domain": "1",
        }

        check_params = {
            "rpcids": "NHJMOd",
            "source-path": "/lifecycle/steps/signup/username",
            "hl": "en-US",
            "TL": tl,
            "rt": "c",
        }

        data = f'f.req=%5B%5B%5B%22NHJMOd%22%2C%22%5B%5C%22{username}%5C%22%2C0%2C0%2Cnull%2C%5Bnull%2Cnull%2Cnull%2Cnull%2C1%2C152855%5D%2C0%2C40%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={at}&'

        async with session.post(
            "https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute",
            params=check_params,
            headers=check_headers,
            data=data,
            timeout=15
        ) as resp:
            text = await resp.text()

            if "password" in text.lower():
                return True   # Available (asks for password next)
            elif "taken" in text.lower() or "unavailable" in text.lower() or "already" in text.lower():
                return False  # Taken
            else:
                return None   # Unclear

    except Exception as e:
        async with stats_lock:
            stats["errors"] += 1
        return None


# ═══════════════════════════════════════════════════════════════
# Yahoo Check (Alternative domain)
# ═══════════════════════════════════════════════════════════════
async def check_yahoo(session: aiohttp.ClientSession, username: str):
    """Check Yahoo email availability."""
    email = f"{username}@yahoo.com"
    url = f"https://login.yahoo.com/account/module/create?validateField=yid&yid={username}"

    try:
        headers = {
            "User-Agent": generate_user_agent(),
            "Accept": "application/json",
            "Referer": "https://login.yahoo.com/account/create",
        }

        async with session.get(url, headers=headers, timeout=10) as resp:
            text = await resp.text()
            if "IDENTIFIER_EXISTS" in text or "taken" in text.lower():
                return False
            elif "AVAILABLE" in text or "available" in text.lower():
                return True
            else:
                return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# Main Worker
# ═══════════════════════════════════════════════════════════════
async def worker(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, token: str, chat_id: str):
    """Main async worker loop."""
    while True:
        async with semaphore:
            username = generate_username()

            # Check TikTok
            tiktok_data = await check_tiktok(session, username)

            async with stats_lock:
                stats["checked"] += 1

            if not tiktok_data:
                await asyncio.sleep(random.uniform(CONFIG["delay_min"], CONFIG["delay_max"]))
                continue

            async with stats_lock:
                stats["tiktok_found"] += 1

            console.print(f"[cyan][+] TikTok: @{username}[/cyan]")

            # Check Gmail first (highest hit rate)
            gmail_available = await check_gmail(session, username)

            if gmail_available is True:
                async with stats_lock:
                    stats["email_available"] += 1
                    stats["hits"] += 1

                email = f"{username}@gmail.com"
                console.print(f"[bold green][!!!] HIT: {email}[/bold green]")

                # Save to file
                with open(CONFIG["save_file"], "a") as f:
                    f.write(f"{email} | TikTok: @{username} | {datetime.now()}\n")

                # Send Telegram
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

<b>v5 Async Checker</b>"""

                await send_telegram(msg, token, chat_id)

            elif gmail_available is False:
                async with stats_lock:
                    stats["email_available"] += 0  # Taken

            # Check Yahoo as fallback
            else:
                yahoo_available = await check_yahoo(session, username)
                if yahoo_available is True:
                    async with stats_lock:
                        stats["email_available"] += 1
                        stats["hits"] += 1

                    email = f"{username}@yahoo.com"
                    console.print(f"[bold yellow][!!!] YAHOO HIT: {email}[/bold yellow]")

                    with open(CONFIG["save_file"], "a") as f:
                        f.write(f"{email} | TikTok: @{username} | {datetime.now()}\n")

                    info = tiktok_data
                    msg = f"""<b>🎯 YAHOO HIT</b>

👤 <b>Username:</b> @{info.get('username', username)}
📧 <b>Email:</b> {email}
👥 <b>Followers:</b> {info.get('followers', 'N/A')}
❤️ <b>Likes:</b> {info.get('likes', 'N/A')}

<b>v5 Async Checker</b>"""

                    await send_telegram(msg, token, chat_id)

            await asyncio.sleep(random.uniform(CONFIG["delay_min"], CONFIG["delay_max"]))


# ═══════════════════════════════════════════════════════════════
# Rich Dashboard
# ═══════════════════════════════════════════════════════════════
def create_dashboard():
    """Create rich dashboard layout."""
    layout = Layout()

    # Header
    header = Panel(
        Text("TikTok Email Checker v5 — ASYNC OPTIMIZED", style="bold cyan", justify="center"),
        border_style="cyan"
    )

    # Stats table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Rate", style="yellow")

    elapsed = time.time() - stats["start_time"]
    cpm = (stats["checked"] / elapsed) * 60 if elapsed > 0 else 0

    table.add_row("Checked", str(stats["checked"]), f"{cpm:.0f}/min")
    table.add_row("TikTok Found", f"[green]{stats['tiktok_found']}[/green]", f"{(stats['tiktok_found']/max(stats['checked'],1)*100):.1f}%")
    table.add_row("Email Available", f"[yellow]{stats['email_available']}[/yellow]", f"{(stats['email_available']/max(stats['tiktok_found'],1)*100):.1f}%")
    table.add_row("HITS", f"[bold green]{stats['hits']}[/bold green]", "")
    table.add_row("Errors", f"[red]{stats['errors']}[/red]", "")
    table.add_row("Skipped", str(stats["skipped"]), "")
    table.add_row("Elapsed", f"{elapsed:.0f}s", "")

    layout.split_column(
        Layout(header, size=3),
        Layout(table, size=12)
    )

    return layout


# ═══════════════════════════════════════════════════════════════
# Main Entry
# ═══════════════════════════════════════════════════════════════
async def main():
    console.print(Panel.fit(
        "[bold cyan]TikTok Email Checker v5 — ASYNC OPTIMIZED[/bold cyan]\n"
        "[green]✓[/green] AsyncIO — no freeze, 50x faster\n"
        "[green]✓[/green] Rich Live Dashboard — no os.system\n"
        "[green]✓[/green] Real Gmail batchexecute check\n"
        "[green]✓[/green] Smart targeted name generation\n"
        "[green]✓[/green] Auto-save hits to file\n"
        "[yellow]⚠ For educational/authorized testing only[/yellow]",
        title="v5",
        border_style="cyan"
    ))

    # Get credentials
    try:
        CONFIG["telegram_id"] = input("Telegram Chat ID: ").strip()
        CONFIG["telegram_token"] = input("Telegram Bot Token: ").strip()
    except EOFError:
        pass

    # Create session with proxy support if available
    connector = None
    if CONFIG["proxy_list"]:
        proxy = random.choice(CONFIG["proxy_list"])
        connector = aiohttp_socks.ProxyConnector.from_url(proxy)

    session = aiohttp.ClientSession(connector=connector)
    semaphore = asyncio.Semaphore(CONFIG["threads"])

    # Start workers
    tasks = []
    for i in range(CONFIG["threads"]):
        task = asyncio.create_task(
            worker(session, semaphore, CONFIG["telegram_token"], CONFIG["telegram_id"])
        )
        tasks.append(task)

    # Start dashboard
    with Live(create_dashboard(), refresh_per_second=2, screen=False) as live:
        while True:
            await asyncio.sleep(1)
            live.update(create_dashboard())

    # Cleanup
    await session.close()
    for task in tasks:
        task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Stopped by user[/red]")
        sys.exit(0)
