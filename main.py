# -*- coding: utf-8 -*-
# Telegram Daily Love / Hope Bot
# Full version v2 - Stable for Railway + python-telegram-bot v21.4

import json
import logging
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Optional dotenv support
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Optional ZoneInfo support
try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except Exception:
    ZoneInfo = None
    HAS_ZONEINFO = False

# ----------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("DailyLoveBot")

# ----------------------------------------------------------------------------

def parse_positive_int(text: str):
    text = str(text or "").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    return None

def parse_uid_value(text: str):
    text = str(text or "").strip()
    if not text:
        return None
    if text.startswith("-") and len(text) > 1 and text[1:].isdigit():
        return int(text)
    if text.isdigit():
        return int(text)
    return None

def command_arguments(update: Update):
    text = update.message.text if update.message else ""
    parts = text.strip().split()
    if not parts:
        return []
    return parts[1:]

# ----------------------------------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = parse_uid_value(os.getenv("ADMIN_ID", ""))
TARGET_CHAT_ID = parse_uid_value(os.getenv("CHAT_ID", ""))

TIMEZONE_NAME = (os.getenv("TIMEZONE", "Asia/Tehran").strip() or "Asia/Tehran")
SEND_TIME_RAW = (os.getenv("SEND_TIME", "08:30").strip() or "08:30")

# Optional sticker environment variables.
# If you do not fill them, daily text will only be sent (no sticker).
DEFAULT_STICKER = os.getenv("STICKER_ID", "").strip()

STICKERS = {
    "love": os.getenv("STICKER_LOVE", DEFAULT_STICKER).strip(),
    "hope": os.getenv("STICKER_HOPE", DEFAULT_STICKER).strip(),
    "morning": os.getenv("STICKER_MORNING", DEFAULT_STICKER).strip(),
    "night": os.getenv("STICKER_NIGHT", DEFAULT_STICKER).strip(),
    "mix": os.getenv("STICKER_MIX", DEFAULT_STICKER).strip(),
}

# ----------------------------------------------------------------------------

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "bot_data.json"

DEFAULT_NAME = "عزیزم"
DEFAULT_CATEGORY = "mix"
DEFAULT_TONE = "friendly"

# ----------------------------------------------------------------------------

CATEGORY_LABELS = {
    "love": "عاشقانه",
    "hope": "امیدوارکننده",
    "morning": "صبح‌بخیر",
    "night": "خوب‌شب",
    "mix": "ترکیبی",
}

CATEGORY_KEYS = ["love", "hope", "morning", "night", "mix"]
CATEGORY_NUMBER_TO_KEY = {str(i + 1): k for i, k in enumerate(CATEGORY_KEYS)}
CATEGORY_TO_KEYS = {CATEGORY_LABELS[k]: k for k in CATEGORY_KEYS}

TONE_LABELS = {
    "friendly": "صمیمی",
    "poetic": "شاعرانه",
    "formal": "رسمی",
    "short": "کوتاه",
}

TONE_KEYS = ["friendly", "poetic", "formal", "short"]
TONE_NUMBER_TO_KEY = {str(i + 1): k for i, k in enumerate(TONE_KEYS)}
TONE_TO_KEYS = {TONE_LABELS[k]: k for k in TONE_KEYS}

# ----------------------------------------------------------------------------

MESSAGES = {
    "love": {
        "friendly": [
            "صبح بخیر {NAME} عزیزم 💛 امیدوارم امروزت پر از آرامش و لبخند باشه.",
            "سلام {NAME} جان! تو یکی از قشنگ‌ترین دلایلِ لبخندهای منی، امروزت درخشان باشه ✨",
            "{NAME} عزیزم، صبحت بخیر! امروز را با مهربونی و امید شروع کن ❤️",
            "سلام به {NAME} مهربون؛ امیدوارم امروزت پر از اتفاق‌های کوچکِ خوب باشه 🌸",
        ],
        "poetic": [
            "صبح بخیر {NAME}؛ تو نوری که بر روزِ من تابیده‌ای 🌹",
            "سلام به {NAME} جان؛ هر صبح دلم با یادِ تو بیدار می‌شود 🌙",
            "{NAME} عزیزم، آفتاب به احترامِ نامِ تو طلوع می‌کند؛ امروزت عاشقانه باد",
            "صبحِ تو بخیر {NAME}؛ تو قشنگ‌ترین شعرِ ناخوانده‌ی این جهانی 💫",
        ],
        "formal": [
            "صبح بخیر {NAME} گرامی؛ برایتان روزه سرشار از آرامش و شادی آرزو می‌کنم.",
            "سلام؛ آرزومندم امروز {NAME} عزیز، روزی نیکو و پربار باشد.",
            "با احترام، صبح بخیر {NAME} گرامی؛ امید است امروزتان به بهترین شکل پیش برود.",
        ],
        "short": [
            "صبح، {NAME} 💛",
            "سلام {NAME} ❤️",
            "{NAME} عزیز 💫",
            "امروزت خوب {NAME} 🌸",
        ],
    },

    "hope": {
        "friendly": [
            "صبح بخیر {NAME}! یادت نره هر روز یه شانس تازه‌ست؛ من بهت ایمان دارم 💪",
            "سلام {NAME} جان؛ امروزت پر از امید باشه؛ هر دری که بستی هم باز می‌شه 🔓✨",
            "{NAME} عزیز، اگر خسته‌ای، فقط یه قدم کوچک بردار؛ من همراهتم 🌱",
            "صبح بخیر {NAME}! تو از چیزی که فکر می‌کنی قوی‌تر و دوست‌داشتنی‌تری 🌈",
        ],
        "poetic": [
            "صبح بخیر {NAME}؛ صبر از میانِ شب می‌رسد و دلتان به صبحِ روشن‌تر نزدیک می‌گردد 🌄",
            "سلام به {NAME} جان؛ امید چراغی است در دستِ تو؛ فردا منتظرِ تو می‌ماند",
            "{NAME} عزیزم، حتی در سخت‌ترین ثانیه‌ها، نور از شیارِ ابرها سرک می‌کشد 💡",
            "روزت به امیدِ تو روشن {NAME}؛ تو همان نوری که تاریکیِ توپ را بی‌رونق می‌کند",
        ],
        "formal": [
            "سلام {NAME} گرامی؛ امیدوارم امروزتان سرشار از آرامش، امید و موفقیت باشد.",
            "روز بخیر؛ باور دارید که هر گام، شما را به افقِ روشن‌تری نزدیک‌تر می‌کند.",
            "{NAME} عزیز، صبح‌تان به نیکی؛ آرزومندم دلتان پرنور و اميدتان پابرجا باد.",
        ],
        "short": [
            "امید، {NAME} ✨",
            "قوی {NAME} 💪",
            "ادامه بده {NAME} 🌱",
            "فردا بهتر {NAME} 🌈",
        ],
    },

    "morning": {
        "friendly": [
            "صبح بخیر {NAME} ☀️ قهوه‌ات داغ، دلت آروم.",
            "سلام {NAME} جان! امروزت را مثل یک هدیه باز کن 🎁",
            "صبح قشنگ بخیر {NAME} مهربون 🌼",
            "{NAME} عزیز، صحت بخیر! لبخندت مثل خورشید باشد 🌞",
        ],
        "poetic": [
            "صبحِ تو بخیر {NAME}؛ خورشید برای تو برآمد و پنجره‌ات به نور گشوده شد 🌅",
            "سلام به {NAME} جان؛ صبح، نامِ تو را به هر آفتاب می‌آموزد",
            "{NAME} عزیزم، بیدار شو که امروز به پنجره‌ی تو رسیده است 🍃",
            "صبحِ تو به قشنگیِ تو {NAME}؛ هر لحظه‌اش را آهسته و مهربان بخوان",
        ],
        "formal": [
            "صبح بخیر {NAME} گرامی؛ روزتان سرشار از آرامش، بهره‌وری و شادی باشد.",
            "سلام و عرض ادب؛ برایتان صبحی روشن و امروزِ پربار آرزو می‌کنم.",
            "روز به خیر {NAME} عزیز؛ امیدوارم امروزتان، شروعِ بهترین مسیرها باشد.",
        ],
        "short": [
            "صبح، {NAME} ☕",
            "روز {NAME} خوب ✨",
            "سلام، {NAME} 🌻",
            "امروز {NAME} شروع نو 🌱",
        ],
    },

    "night": {
        "friendly": [
            "شبِ {NAME} آروم 🌙 یادت باشد هر روزی که تمام شد، یک پیروزیه.",
            "خوب شب {NAME} عزیز! خسته نباشی؛ فردا دوباره از نو قشنگ می‌شود ✨",
            "شبت بخیر {NAME} جان، امیدوارم خواب‌های خوش و آرام ببینی ⭐",
            "شب بخیر {NAME}؛ همه‌چیز همان‌قدر که بود، تو عالی بودی 😌",
        ],
        "poetic": [
            "شب بخیر {NAME}؛ ماه بر پشتِ بامِ تو ایستاد و ستاره‌ها نگهبانِ خوابِ تو شدند 🌌",
            "خوب شبِ {NAME} جان؛ روز می‌رود و امید در پنجره‌ی فردا روشن می‌ماند",
            "شب، {NAME} عزیز، آرامشی است که تو را به فردا باز می‌گرداند",
            "بخواب {NAME} جان؛ صبح در راه است و تو را دوباره با نور می‌خواند",
        ],
        "formal": [
            "شبت به نیکی {NAME} گرامی؛ برایتان خوابی آرام و فردایی پرانرژی آرزو دارم.",
            "شب بخیر؛ امید است آرامشِ امشب، سرچشمه‌ی موفقیتِ فردای شما باشد.",
            "{NAME} عزیز، شبتان بخیر؛ آرامشِ شایسته‌ی قلبِ مهربانتان را آرزو می‌کنم.",
        ],
        "short": [
            "شب بخیر {NAME} 🌙",
            "خوب شب عزیز 💖",
            "فردا {NAME} ✨",
            "آرام بخواب {NAME} 💤",
        ],
    },

    "mix": {
        "friendly": [
            "صبح بخیر {NAME}! امیدوارم امروزت پر از عشق، امید و آرامش باشد 💛",
            "سلام {NAME} عزیز؛ تو همان دلیلِ خوبِ امروزت هستی ✨",
            "{NAME} جان، هر نفس امروزت را برای خودت بردار؛ تو لایق بهترین‌هاست 💗",
            "سلام به {NAME} مهربون؛ امروزت درخشان‌تر از آن چیزی باشد که فکرش را می‌کنی 🌈",
        ],
        "poetic": [
            "صبحِ تو بخیر {NAME}؛ دلم با یادِ تو مثل صبح باز می‌شود 🌸",
            "سلام به {NAME} جان؛ تو آرامشی که میانِ هیاهو پیدا می‌شود",
            "روزت به نامِ تو روشن {NAME}؛ هر لحظه‌ات پر از امید و عشق باشد 💫",
            "{NAME} عزیز، هر آینه‌ی صبح، زیبایی‌ات را به دنیا بازتاب می‌دهد",
        ],
        "formal": [
            "صبح بخیر {NAME} گرامی؛ برایتان روزی سرشار از امید، آرامش و موفقیت آرزو دارم.",
            "سلام؛ قدردانی‌ام از حضورِ شماست {NAME} عزیز؛ روزتان نیکو باد.",
            "با احترام و آرزوی بهترین‌ها برای {NAME} عزیز؛ صبحتون به نیکی.",
        ],
        "short": [
            "صبح {NAME} 💛",
            "تو خاص {NAME} 💫",
            "امروز {NAME} عزیز ✨",
            "بهترین {NAME} ❤️",
        ],
    },
}

# ----------------------------------------------------------------------------

def default_profile(name: str = "", subscribed: bool = False, muted: bool = True) -> dict:
    return {
        "name": name or "",
        "category": DEFAULT_CATEGORY,
        "tone": DEFAULT_TONE,
        "subscribed": bool(subscribed),
        "muted": bool(muted),
        "last_sent_day": None,
    }

def normalize_profile(profile: dict) -> dict:
    if not isinstance(profile, dict):
        profile = {}

    profile.setdefault("name", "")
    profile.setdefault("category", DEFAULT_CATEGORY)
    profile.setdefault("tone", DEFAULT_TONE)
    profile.setdefault("subscribed", False)
    profile.setdefault("muted", True)
    profile.setdefault("last_sent_day", None)

    if profile.get("category") not in CATEGORY_LABELS:
        profile["category"] = DEFAULT_CATEGORY
    if profile.get("tone") not in TONE_LABELS:
        profile["tone"] = DEFAULT_TONE

    return profile

def default_data() -> dict:
    return {
        "admin_id": ADMIN_ID,
        "users": {},
        "settings": {
            "send_time": SEND_TIME_RAW,
            "timezone": TIMEZONE_NAME,
        },
    }

def save_data():
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("Failed to save data: %s", exc)

def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception as exc:
            logger.warning("Failed to load data, creating a new file: %s", exc)
            obj = default_data()

        if not isinstance(obj, dict):
            obj = default_data()

        obj.setdefault("admin_id", ADMIN_ID)
        obj.setdefault("users", {})
        obj.setdefault("settings", {})

        if not isinstance(obj["users"], dict):
            obj["users"] = {}
        if not isinstance(obj["settings"], dict):
            obj["settings"] = {}

        obj["settings"].setdefault("send_time", SEND_TIME_RAW)
        obj["settings"].setdefault("timezone", TIMEZONE_NAME)

        for uid in list(obj["users"].keys()):
            profile = obj["users"].get(uid)
            obj["users"][uid] = normalize_profile(profile if isinstance(profile, dict) else default_profile())

        # Environment admin has priority if it is defined.
        if ADMIN_ID is not None:
            obj["admin_id"] = ADMIN_ID

        # Migrate users created by old versions that have no subscribed field.
        for uid, profile in obj["users"].items():
            if "subscribed" not in profile or not isinstance(profile.get("subscribed"), bool):
                profile["subscribed"] = False
                if not profile.get("muted"):
                    profile["muted"] = True

        return obj
    return default_data()

DATA = load_data()

def ensure_startup_targets():
    # Admin from environment (optional)
    if ADMIN_ID is not None:
        uid_str = str(ADMIN_ID)
        if uid_str not in DATA["users"] or not isinstance(DATA["users"].get(uid_str), dict):
            DATA["users"][uid_str] = normalize_profile(default_profile(muted=True, subscribed=False))
        else:
            DATA["users"][uid_str] = normalize_profile(DATA["users"][uid_str])
            if uid_str == str(ADMIN_ID):
                DATA["admin_id"] = ADMIN_ID

    # Target chat from environment (optional; for admin-friendly usage)
    if TARGET_CHAT_ID is not None:
        uid_str = str(TARGET_CHAT_ID)
        if uid_str not in DATA["users"] or not isinstance(DATA["users"].get(uid_str), dict):
            DATA["users"][uid_str] = normalize_profile(default_profile(muted=False, subscribed=True))
        else:
            DATA["users"][uid_str] = normalize_profile(DATA["users"][uid_str])
            DATA["users"][uid_str]["subscribed"] = True
            DATA["users"][uid_str]["muted"] = False

    save_data()

ensure_startup_targets()

# ----------------------------------------------------------------------------

def get_uid_key(uid) -> str:
    return str(int(uid))

def get_profile(uid) -> dict:
    uid_str = get_uid_key(uid)
    if uid_str in DATA["users"] and isinstance(DATA["users"][uid_str], dict):
        return normalize_profile(DATA["users"][uid_str])

    subscribed = False
    muted = True

    # If this id is already the configured target, subscribe and unmute it.
    if TARGET_CHAT_ID is not None and int(uid) == int(TARGET_CHAT_ID):
        subscribed = True
        muted = False

    # New ordinary user starts not subscribed; admin can add with /addfriend
    profile = normalize_profile(default_profile(subscribed=subscribed, muted=muted))
    DATA["users"][uid_str] = profile
    save_data()
    return profile

def is_admin(uid) -> bool:
    admin_id = DATA.get("admin_id")
    if admin_id is None:
        return False
    try:
        return int(admin_id) == int(uid)
    except Exception:
        return False

def can_operate_profile(uid) -> bool:
    profile = get_profile(uid)
    return bool(profile.get("subscribed")) or is_admin(uid)

def ensure_subscription(uid) -> dict:
    profile = get_profile(uid)
    profile["subscribed"] = True
    profile["muted"] = False
    save_data()
    return profile

# ----------------------------------------------------------------------------

def parse_hhmm(time_str: str):
    try:
        parts = str(time_str or "").strip().split(":")
        if len(parts) != 2:
            return None
        hour = int(parts[0])
        minute = int(parts[1])
        if 0 <= hour < 24 and 0 <= minute < 60:
            return hour, minute
    except Exception:
        return None
    return None

def get_send_time():
    settings = DATA.get("settings", {})
    raw = (settings.get("send_time") or "").strip()
    parsed = parse_hhmm(raw)
    if parsed is None:
        parsed = parse_hhmm(SEND_TIME_RAW)
    if parsed is None:
        parsed = (8, 30)
    return parsed

def get_timezone_name() -> str:
    settings = DATA.get("settings", {})
    name = (settings.get("timezone") or "").strip()
    return name or TIMEZONE_NAME

def now_local():
    tz_name = get_timezone_name()
    if HAS_ZONEINFO and ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass

    # Helpful fallback without zoneinfo/tzdata: fixed +3:30 for Asia/Tehran.
    if tz_name in ("Asia/Tehran", "Iran"):
        tehran_tz = timezone(timedelta(hours=3, minutes=30))
        return datetime.now(tehran_tz)

    return datetime.now(timezone.utc)

def should_send_now() -> bool:
    h, m = get_send_time()
    now = now_local()
    return now.hour > h or (now.hour == h and now.minute >= m)

def seconds_to_next_send() -> float:
    h, m = get_send_time()
    now = now_local()
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return max(1, (target - now).total_seconds())

# ----------------------------------------------------------------------------

def choose_category(value, uid, hour: int):
    raw = str(value or "").strip()
    lower = raw.lower()

    if raw and raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(CATEGORY_KEYS):
            return CATEGORY_KEYS[idx - 1]
    if lower in MESSAGES:
        return lower
    if raw.upper() in CATEGORY_LABELS:
        pass
    if raw in CATEGORY_TO_KEYS:
        return CATEGORY_TO_KEYS[raw]
    if raw in ["۱", "۲", "۳", "۴", "۵", "۱", "۲", "۳", "۴", "۵"]:
        persian_to_index = {
            "۱": "love",
            "۲": "hope",
            "۳": "morning",
            "۴": "night",
            "۵": "mix",
            "1": "love",
            "2": "hope",
            "3": "morning",
            "4": "night",
            "5": "mix",
        }
        if raw in persian_to_index:
            return persian_to_index[raw]

    # If stored value is invalid or a missing key, fallback.
    profile = get_profile(uid)
    stored = profile.get("category")
    if stored in MESSAGES:
        return stored
    return DEFAULT_CATEGORY

def choose_tone(value, uid):
    raw = str(value or "").strip()
    lower = raw.lower()

    if raw and raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(TONE_KEYS):
            return TONE_KEYS[idx - 1]
    if lower in TONe_KEYS:
        pass
    if lower in TONE_KEYS:
        return lower
    if raw in TONE_TO_KEYS:
        return TONE_TO_KEYS[raw]
    if raw in ["۱", "۲", "۳", "۴", "۱", "۲", "۳", "۴"]:
        persian_to_index = {
            "۱": "friendly",
            "۲": "poetic",
            "۳": "formal",
            "۴": "short",
            "1": "friendly",
            "2": "poetic",
            "3": "formal",
            "4": "short",
        }
        if raw in persian_to_index:
            return persian_to_index[raw]

    profile = get_profile(uid)
    stored = profile.get("tone")
    if stored in TONE_LABELS:
        return stored
    return DEFAULT_TONE

def effective_category(category: str, hour: int) -> str:
    cat = category if category in MESSAGES else DEFAULT_CATEGORY
    if cat == "mix":
        # Mix category automatically picks an appropriate category for this hour.
        if 18 <= hour or hour < 6:
            pool = ["night", "hope", "love"]
        else:
            pool = ["love", "hope", "morning"]
        cat = random.choice(pool)
    return cat

def build_message_text(uid) -> tuple:
    profile = get_profile(uid)
    now = now_local()
    hour = now.hour

    category = choose_category(profile.get("category"), uid, hour)
    tone = choose_tone(profile.get("tone"), uid)

    real_category = effective_category(category, hour)
    templates = (
        MESSAGES.get(real_category, MESSAGES["mix"])
        .get(tone, [])
    )

    if not templates:
        templates = MESSAGES.get(real_category, MESSAGES["mix"]).get("friendly", [
            "صبح بخیر {NAME} عزیزم 💛"
        ])

    text = random.choice(templates)
    name = (profile.get("name") or "").strip() or DEFAULT_NAME
    text = text.replace("{NAME}", name)

    return text, real_category

def sticker_id_for_category(category: str) -> str:
    cat = category if category in STICKERS else DEFAULT_CATEGORY
    sticker = STICKERS.get(cat, "").strip()
    if not sticker:
        sticker = STICKERS.get("mix", "").strip() or DEFAULT_STICKER.strip()
    return sticker

# ----------------------------------------------------------------------------

async def send_one_message(bot, chat_id):
    chat_id = int(chat_id)
    text, category = build_message_text(chat_id)

    await bot.send_message(chat_id=chat_id, text=text)

    sticker = sticker_id_for_category(category)
    if sticker:
        try:
            await bot.send_sticker(chat_id=chat_id, sticker=sticker)
        except Exception as exc:
            logger.warning("Sticker send failed for %s: %s", chat_id, exc)

# ----------------------------------------------------------------------------

def settings_keyboard(uid) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📚 دسته‌بندی پیام", callback_data="settings:category")],
        [InlineKeyboardButton("🎭 لحن پیام", callback_data="settings:tone")],
        [InlineKeyboardButton("✏️ تغییر نام", callback_data="settings:name")],
        [
            InlineKeyboardButton("🔕 قطع پیام", callback_data="settings:mute"),
            InlineKeyboardButton("🔔 وصل پیام", callback_data="settings:unmute"),
        ],
        [
            InlineKeyboardButton("✅ وضعیت", callback_data="settings:status"),
            InlineKeyboardButton("🆔 شناسه چت", callback_data="settings:id"),
        ],
        [InlineKeyboardButton("❌ اشتراک‌زدایی", callback_data="settings:unsubscribe")],
    ]

    if is_admin(uid):
        rows.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin:panel")])

    return InlineKeyboardMarkup(rows)

def category_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key in CATEGORY_KEYS:
        rows.append([InlineKeyboardButton(CATEGORY_LABELS[key], callback_data=f"set_category:{key}")])
    rows.append([InlineKeyboardButton("↩️ بازگشت", callback_data="settings:back")])
    return InlineKeyboardMarkup(rows)

def tone_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key in TONE_KEYS:
        rows.append([InlineKeyboardButton(TONE_LABELS[key], callback_data=f"set_tone:{key}")])
    rows.append([InlineKeyboardButton("↩️ بازگشت", callback_data="settings:back")])
    return InlineKeyboardMarkup(rows)

def profile_summary_text(uid) -> str:
    profile = get_profile(uid)
    subscribed = bool(profile.get("subscribed"))
    muted = bool(profile.get("muted"))
    active = subscribed and not muted

    category = choose_category(profile.get("category"), uid, 12)
    tone = choose_tone(profile.get("tone"), uid)
    real_cat = CATEGORY_LABELS.get(category, category)
    real_tone = TONE_LABELS.get(tone, tone)
    name = (profile.get("name") or "").strip()

    if not active:
        status = "❌ پیام روزانه: خاموش / unsubscribed"
    else:
        status = "✅ پیام روزانه: روشن"

    lines = [
        "🌼 تنظیمات دریافت پیام شما:",
        "",
        f"شناسه چت: `{uid}`",
        f"نام: {name or '(تنظیم نشده)'}",
        f"دسته‌بندی: {real_cat}",
        f"لحن: {real_tone}",
        status,
        "",
        "برای انتخاب گزینه‌ها، روی دکمه‌ها بزنید.",
    ]
    if is_admin(uid):
        lines.insert(0, "👑 شما ادمین این ربات هستید.")
    return "\n".join(lines)

# ----------------------------------------------------------------------------

ADMIN_USAGE_TEXT = (
    "👑 پنل ادمین\n\n"
    "برای افزودن دوست:\n"
    "`/addfriend 123456789 اسم دلخواه`\n\n"
    "دستورهای ادمین:\n"
    "`/removefriend ۱۲۳۴۵۶۷۸۹` حذف دوست\n"
    "`/friends` لیست دوستان\n"
    "`/setname ۱۲۳۴۵۷۸۹ اسم دوست` تغییر نام دوست\n"
    "`/setcategory ۱۲۳۴۵۶۷۸۹ ۱` دسته‌بندی دوست\n"
    "`/settone ۱۲۳۴۵۶۷۸۹ ۲` لحن پیام دوست\n"
    "`/settime 09:00` ساعت ارسال روزانه\n"
    "`/test ۱۲۳۴۵۶۷۸۹` تست ارسال به آیدی مشخص\n"
    "⚠️ دوست باید حداقل یک‌بار `/start` بزند؛ اگر پیام `/start` نزد، ربات می‌تواند پیام ارسال نکند."
)

GENERAL_HELP_TEXT = (
    "📖 راهنمای ربات:\n\n"
    "`/start` شروع / منو\n"
    "`/help` راهنما\n"
    "`/id` نمایش شناسه چت تو\n"
    "`/settings` منوی تنظیمات\n"
    "`/status` وضعیت دریافت پیام\n"
    "`/name` تغییر نام خودت\n"
    "`/category` تغییر دسته‌بندی پیام\n"
    "`/tone` تغییر لحن پیام\n"
    "`/mute` قطع موقت پیام روزانه\n"
    "`/unmute` وصل دوباره\n"
    "`/test` ارسال یک تست فوری\n"
    "`/unsubscribe` حذف از لیست\n"
    "`/time` نمایش ساعت ارسال\n\n"
    "اگر هنوز عضو نیستی، به ادمین بگو: `/addfriend شناسه_تو`."
)

# ----------------------------------------------------------------------------

async def respond_allowed_or_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = int(update.effective_chat.id)
    if can_operate_profile(uid):
        return True
    await update.message.reply_text("🚫 شما هنوز به لیست دریافت پیام روزانه اضافه نشدید.")
    return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)

    # If admin_id is not set, first /start can claim it.
    if DATA.get("admin_id") is None:
        DATA["admin_id"] = uid
        save_data()

    profile = get_profile(uid)

    if not profile.get("name"):
        first_name = ""
        try:
            first_name = update.effective_user.first_name or ""
        except Exception:
            pass
        if first_name:
            profile["name"] = first_name
            save_data()

    lines = []

    if is_admin(uid):
        lines.extend([
            "👑 سلام ادمین عزیز، ربات فعال است.\n",
            "برای افزودن دوست، این قالب را بفرست:",
            "`/addfriend 123456789 نام دوست`\n",
            "برای مدیریت، /help و /admin را ببین.",
        ])
        if is_admin(uid):
            lines.append("\nبرای تنظیمات خودت: /settings")

    if profile.get("subscribed"):
        lines.extend([
            "🌸 سلام عزیزم، صبح‌بخیر/عشق/امید فعال شد.\n",
            "اگر می‌خواهی فقط یک‌بار اسمت را بفرستاند و همه‌چیز را انتخاب کن:",
            "`/name اسم تو`",
            "سپس `/settings`.",
        ])

    if not lines:
        lines.extend([
            "🌱 سلام عزیزم؛ ربات روزانه فعال است.\n",
            "برای دریافت پیام، لازم است به لیست اضافه شوی.\n",
            "برای افزودن، از ادمین بخواه این دستور را برای تو بزند:\n",
            "`/addfriend شناسه_چت_تو نام تو`\n",
            "برای دیدن شناسه چت از `/id` استفاده کن.",
        ])

    text = "\n".join(lines)
    if profile.get("subscribed") or is_admin(uid):
        await update.message.reply_text(text)
        await update.message.reply_text(
            "🌼 منوی تنظیمات:\n\n" + profile_summary_text(uid),
            reply_markup=settings_keyboard(uid),
        )
    else:
        await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    text = GENERAL_HELP_TEXT
    if is_admin(uid):
        text = (
            GENERAL_HELP_TEXT
            + "\n\n👑 دستورات ادمین:\n"
            + "`/admin`\n`/addfriend 123456789 نام`"
            "\n`/removefriend 123456789`"
            "\n`/friends`"
            "\n`/setname 123456789 اسم`"
            "\n`/setcategory 123456789 شماره`"
            "\n`/settone 123456789 شماره`"
            "\n`/settime 09:00`"
            "\n`/test 123456789`"
        )
    await update.message.reply_text(text)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"شناسه چت تو: `{int(update.effective_chat.id)}`")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await respond_allowed_or_blocked(update, context):
        return
    uid = int(update.effective_chat.id)
    await update.message.reply_text(
        profile_summary_text(uid),
        reply_markup=settings_keyboard(uid),
    )

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await respond_allowed_or_blocked(update, context):
        return
    uid = int(update.effective_chat.id)
    profile = get_profile(uid)
    profile["muted"] = True
    save_data()
    await update.message.reply_text("🔕 پیام روزانه موقتاً قطع شد. با /unmute دوباره وصلش کن.")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await respond_allowed_or_blocked(update, context):
        return
    uid = int(update.effective_chat.id)
    profile = get_profile(uid)
    profile["muted"] = False
    save_data()
    await update.message.reply_text("✅ پیام روزانه فعال شد.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    await update.message.reply_text(profile_summary_text(uid))

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    uid_str = get_uid_key(uid)
    profile = DATA["users"].get(uid_str)
    if is_admin(uid):
        await update.message.reply_text("⚠️ ادمین نمی‌تواند خودش را حذف کند؛ برای قطع فقط /mute.")
        return
    if isinstance(profile, dict):
        del DATA["users"][uid_str]
        save_data()
    await update.message.reply_text("❌ از لیست دریافت پیام‌ها حذف شدی.\nبرای بازگشت به ادمین بگو /addfriend.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    args = command_arguments(update)

    target = uid
    if args:
        parsed = parse_positive_int(args[0])
        if parsed is None:
            await update.message.reply_text("برای خودت /test، یا به‌عنوان ادمین: /test CHAT_ID")
            return
        if not is_admin(uid):
            await update.message.reply_text("⛔ فقط ادمین می‌تواند به شناسه دیگر تست بفرستد.")
            target = uid
        else:
            target = parsed

    try:
        await send_one_message(context.bot, target)
        if target == uid:
            await update.message.reply_text("✅ تست ارسال شد اگر پیام روزانه قطع/عضو نیست هم ارسال می‌شود.")
        else:
            await update.message.reply_text(f"✅ پیام تستی به شناسه {target} ارسال شد.")
    except Exception as exc:
        logger.error("Test send failed: %s", exc)
        await update.message.reply_text(
            "❌ ارسال پیام ممکن نبود.\n"
            "اگر این همان دوستی‌ست که به‌تازگی اضافه شده، احتمالاً هنوز باید خود کاربر `/start` بزند."
        )

async def name_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await respond_allowed_or_blocked(update, context):
        return
    args = command_arguments(update)
    if args:
        uid = int(update.effective_chat.id)
        profile = get_profile(uid)
        profile["name"] = " ".join(args).strip()
        save_data()
        await update.message.reply_text("✅ نامت تنظیم شد.")
        await update.message.reply_text(
            profile_summary_text(uid),
            reply_markup=settings_keyboard(uid),
        )
    else:
        context.chat_data["awaiting_name"] = True
        await update.message.reply_text("اسم دلخواهت را بفرست ✏️")

async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await respond_allowed_or_blocked(update, context):
        return
    await update.message.reply_text("یک دسته‌بندی انتخاب کن:", reply_markup=category_keyboard())

async def tone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await respond_allowed_or_blocked(update, context):
        return
    await update.message.reply_text("یک لحن انتخاب کن:", reply_markup=tone_keyboard())

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    h, m = get_send_time()
    now = now_local()
    await update.message.reply_text(
        f"⏰ ساعت تنظیم‌شده ارسال روزانه: {h:02d}:{m:02d}\n"
        f"الان: {now.hour:02d}:{now.minute:02d} به وقت {get_timezone_name()}"
    )

async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند ساعت را تغییر دهد.")
        return

    args = command_arguments(update)
    if not args:
        await update.message.reply_text("usage:/settime 08:30")
        return

    parsed = parse_hhmm(args[0])
    if parsed is None:
        await update.message.reply_text("❌ فرمت اشتباه. درست: HH:MM، مثلاً 08:30")
        return

    h, m = parsed
    DATA["settings"]["send_time"] = f"{h:02d}:{m:02d}"
    save_data()
    await update.message.reply_text(f"⏰ ساعت ارسال به {h:02d}:{m:02d} تغییر کرد.")

# ----------------------------------------------------------------------------

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ شما ادمین این ربات نیستید.")
        return
    await update.message.reply_text(ADMIN_USAGE_TEXT)

async def addfriend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند دوست اضافه کند.")
        return

    args = command_arguments(update)
    if not args:
        await update.message.reply_text("usage:/addfriend 123456789 نام دلخواه")
        return

    target = parse_positive_int(args[0])
    if target is None:
        await update.message.reply_text("❌ شناسه دوست را عدد صحیح وارد کن.\nمثال: `/addfriend 123456789 عشقم`")
        return

    name = " ".join(args[1:]).strip()
    ensure_subscription(target)
    if name:
        profile = get_profile(target)
        profile["name"] = name
        save_data()

    try:
        await send_one_message(context.bot, target)
        await update.message.reply_text(f"✅ شناسه {target} به لیست اضافه شد و پیام فوری برایش ارسال شد.")
    except Exception as exc:
        logger.error("Adding friend and initial send failed: %s", exc)
        await update.message.reply_text(
            f"✅ شناسه {target} به لیست اضافه شد، اما پیام فوری ارسال نشد.\n"
            "مطمئن شو آن کاربر حداقل یک‌بار به ربات `/start` بزند؛ بعد دوباره تست بفرست."
        )

async def removefriend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند حذف کند.")
        return

    args = command_arguments(update)
    if not args:
        await update.message.reply_text("usage:/removefriend 123456789")
        return

    target = parse_positive_int(args[0])
    if target is None:
        await update.message.reply_text("❌ شناسه را عدد وارد کن.")
        return

    if target == uid:
        await update.message.reply_text("⚠️ ادمین نمی‌تواند خودش را از پنل به این شکل حذف کند؛ می‌تواند /mute کند.")
        return

    uid_str = get_uid_key(target)
    if uid_str in DATA["users"] and isinstance(DATA["users"].get(uid_str), dict):
        del DATA["users"][uid_str]
        save_data()
        await update.message.reply_text(f"❌ شناسه {target} از لیست حذف شد.")
    else:
        await update.message.reply_text("این کاربر در لیست نبود.")

async def friends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند ببیند.")
        return

    lines = ["👥 لیست دوستان/دریافت‌کنندگان:\n"]
    users = DATA.get("users", {})
    if not users:
        lines.append("هنوز کسی اضافه نشده.")

    for key in sorted(users.keys(), key=lambda x: int(x)):
        profile = normalize_profile(users.get(key, {}))
        subscribed = bool(profile.get("subscribed"))
        muted = bool(profile.get("muted"))
        name = profile.get("name") or "—"
        category = CATEGORY_LABELS.get(profile.get("category"), "—")
        tone = TONE_LABELS.get(profile.get("tone"), "—")
        role = "👑" if is_admin(int(key)) else "🌷"
        status = "قطع" if (subscribed and muted) else ("فعال" if subscribed else "عضو نیست")
        lines.append(f"{role} `{key}` | {name} | {category} | {tone} | {status}")

    await update.message.reply_text("\n".join(lines))

async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند نام دوست را تغییر دهد.")
        return

    args = command_arguments(update)
    if not args:
        await update.message.reply_text("usage:/setname 123456789 نام دلخواه")
        return

    target = parse_positive_int(args[0])
    if target is None:
        await update.message.reply_text("❌ شناسه را عدد وارد کن.")
        return
    name = " ".join(args[1:]).strip()
    ensure_subscription(target) if not get_profile(target).get("subscribed") else None
    profile = get_profile(target)
    profile["muted"] = False
    profile["subscribed"] = True
    profile["name"] = name or DEFAULT_NAME
    save_data()
    await update.message.reply_text(f"✅ نام شناسه {target} تنظیم شد: {profile['name']}")

async def setcategory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند دسته‌بندی کاربر دیگر را تغییر دهد.")
        return

    args = command_arguments(update)
    if not args:
        await update.message.reply_text(
            "usage:/setcategory 123456789 شماره\n"
            "1=عاشقانه، 2=امیدوارکننده، 3=صبح‌بخیر، 4=خوب‌شب، 5=ترکیبی"
        )
        return

    target = parse_positive_int(args[0])
    if target is None:
        await update.message.reply_text("❌ شناسه معتبر نیست.")
        return

    if len(args) > 1:
        chosen = choose_category(args[1], target, 12)
    else:
        await update.message.reply_text(
            "1️⃣ عاشقانه\n2️⃣ امیدوارکننده\n3️⃣ صبح‌بخیر\n4️⃣ خوب‌شب\n5️⃣ ترکیبی\n"
            "مثال: `/setcategory 123456789 1`"
        )
        return

    ensure_subscription(target)
    profile = get_profile(target)
    profile["category"] = chosen
    profile["muted"] = False
    save_data()
    await update.message.reply_text(f"✅ دسته‌بندی {target} به {CATEGORY_LABELS.get(chosen, chosen)} تغییر کرد.")

async def settone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = int(update.effective_chat.id)
    if not is_admin(uid):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند لحن کاربر دیگر را تغییر دهد.")
        return

    args = command_arguments(update)
    if not args:
        await update.message.reply_text("usage:/settone 123456789 شماره")
        return

    target = parse_positive_int(args[0])
    if target is None:
        await update.message.reply_text("❌ شناسه معتبر نیست.")
        return

    if len(args) > 1:
        chosen = choose_tone(args[1], target)
    else:
        await update.message.reply_text(
            "1️⃣ صمیمی\n2️⃣ شاعرانه\n3️⃣ رسمی\n4️⃣ کوتاهی\n"
            "مثال: `/settone 123456789 2`"
        )
        return

    ensure_subscription(target)
    profile = get_profile(target)
    profile["tone"] = chosen
    profile["muted"] = False
    save_data()
    await update.message.reply_text(f"✅ لحن پیام {target} به {TONE_LABELS.get(chosen, chosen)} تغییر کرد.")

# ----------------------------------------------------------------------------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    uid = int(query.from_user.id)

    if not can_operate_profile(uid):
        await query.edit_message_text("🚫 شما به این بخش دسترسی ندارید. به ادمین بگو: `/addfriend شناسه تو`")
        return

    data = str(query.data or "")

    if data == "settings:back":
        await query.edit_message_text(profile_summary_text(uid), reply_markup=settings_keyboard(uid))
        return

    if data == "settings:category":
        await query.edit_message_text("یک دسته برای پیام روزانه انتخاب کن:", reply_markup=category_keyboard())
        return

    if data == "settings:tone":
        await query.edit_message_text("یک لحن انتخاب کن:", reply_markup=tone_keyboard())
        return

    if data == "settings:name":
        context.chat_data["awaiting_name"] = True
        await query.edit_message_text("✏️ اسم دلخواه خودت را بفرست، بدون دستور:")
        return

    if data == "settings:status":
        await query.edit_message_text(profile_summary_text(uid), reply_markup=settings_keyboard(uid))
        return

    if data == "settings:id":
        await query.edit_message_text(
            f"شناسه چت شما: `{uid}`\nاین را برای ادمین بفرست تا با `/addfriend` اضافه کند.",
            reply_markup=None,
        )
        return

    if data == "settings:mute":
        profile = get_profile(uid)
        profile["muted"] = True
        save_data()
        await query.edit_message_text(profile_summary_text(uid), reply_markup=settings_keyboard(uid))
        return

    if data == "settings:unmute":
        profile = get_profile(uid)
        profile["muted"] = False
        save_data()
        await query.edit_message_text(profile_summary_text(uid), reply_markup=settings_keyboard(uid))
        return

    if data == "settings:unsubscribe":
        if is_admin(uid):
            await query.edit_message_text("⚠️ به‌عنوان ادمین، فقط گزینه /mute پیشنهاد می‌شود.")
            return
        uid_str = get_uid_key(uid)
        if uid_str in DATA["users"]:
            del DATA["users"][uid_str]
            save_data()
        await query.edit_message_text(
            "❌ اشتراک شما حذف شد.\nاگر دوست بودید دوباره /start؛ اگر نه، بگو برای ادمین /addfriend."
        )
        return

    if data.startswith("set_category:"):
        value = data.split(":", 1)[1]
        chosen = choose_category(value, uid, now_local().hour)
        profile = get_profile(uid)
        profile["category"] = chosen
        save_data()
        await query.edit_message_text(
            f"✅ دسته‌بندی پیام شما به `{CATEGORY_LABELS.get(chosen, chosen)}` تغییر کرد.\n\n" + profile_summary_text(uid),
            reply_markup=None,
        )
        await query.message.reply_text(
            "برای انتخاب گزینه دیگر:\n" + profile_summary_text(uid),
            reply_markup=settings_keyboard(uid),
        )
        return

    if data.startswith("set_tone:"):
        value = data.split(":", 1)[1]
        chosen = choose_tone(value, uid)
        profile = get_profile(uid)
        profile["tone"] = chosen
        save_data()
        await query.edit_message_text(
            f"✅ لحن پیام شما به `{TONE_LABELS.get(chosen, chosen)}` تغییر کرد.\n\n" + profile_summary_text(uid),
            reply_markup=None,
        )
        await query.message.reply_text(
            "برای انتخاب گزینه دیگر:\n" + profile_summary_text(uid),
            reply_markup=settings_keyboard(uid),
        )
        return

    if data == "admin:panel":
        if is_admin(uid):
            await query.edit_message_text(
                "برای مدیریت دوست‌ها از دستورات /addfriend، /setname، /setcategory و /friends استفاده کن.\n\n" + ADMIN_USAGE_TEXT
            )
        else:
            await query.edit_message_text("⛔ فقط ادمین می‌تواند پنل را ببیند.")
        return

    # Unknown callback.
    await query.edit_message_text(profile_summary_text(uid), reply_markup=settings_keyboard(uid))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    uid = int(update.effective_chat.id)

    if context.chat_data.get("awaiting_name"):
        name = (update.message.text or "").strip()
        profile = get_profile(uid)
        if name:
            profile["name"] = name[:80]
            save_data()
            await update.message.reply_text(
                f"✅ نامت به `{profile['name']}` تنظیم شد.\n\n" + profile_summary_text(uid),
                reply_markup=settings_keyboard(uid),
            )
        else:
            await update.message.reply_text("✴️ لطفاً یک نام معتبر بفرست.")
        context.chat_data.pop("awaiting_name", None)
        return

    # Ignore plain texts that are not expected. This avoids weird answers.
    return

# ----------------------------------------------------------------------------

async def daily_job_callback(context: ContextTypes.DEFAULT_TYPE):
    now = now_local()
    h, m = get_send_time()
    if not (now.hour > h or (now.hour == h and now.minute >= m)):
        return

    today = now.date().isoformat()
    bot = context.bot
    users = DATA.get("users", {})

    for uid_str in list(users.keys()):
        profile = users.get(uid_str)
        if not isinstance(profile, dict):
            continue

        try:
            target = int(uid_str)
        except Exception:
            continue

        # Only subscribed users receive automatic daily messages.
        if not bool(profile.get("subscribed", False)):
            continue

        # Admin/friend can mute themselves. Do not send to admin unless subscribed.
        if bool(profile.get("muted", True)):
            continue

        if profile.get("last_sent_day") == today:
            continue

        try:
            await send_one_message(bot, target)
            profile["last_sent_day"] = today
            save_data()
            logger.info("Daily message sent to %s", target)
        except Exception as exc:
            # Mark today as attempted and avoid spamming every 30 seconds.
            profile["last_sent_day"] = today
            save_data()
            logger.warning("Daily message failed for %s: %s", target, exc)

# ----------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception, context updated: %s", str(context.error))

# ----------------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN env is missing; exiting.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("name", name_command))
    application.add_handler(CommandHandler("category", category_command))
    application.add_handler(CommandHandler("tone", tone_command))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("settime", settime_command))

    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("addfriend", addfriend_command))
    application.add_handler(CommandHandler("removefriend", removefriend_command))
    application.add_handler(CommandHandler("friends", friends_command))
    application.add_handler(CommandHandler("setname", setname_command))
    application.add_handler(CommandHandler("setcategory", setcategory_command))
    application.add_handler(CommandHandler("settone", settone_command))
    application.add_handler(CommandHandler("ping", start_command))

    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_error_handler(error_handler)

    job_queue = getattr(application, "job_queue", None)
    if job_queue is None:
        logger.warning("Job queue is unavailable; daily scheduling is disabled. Install with python-telegram-bot[job-queue].")
    else:
        job_queue.run_repeating(callback=daily_job_callback, interval=30, first=1)
        logger.info("Daily schedule job is registered.")

    logger.info("Bot polling starting ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
