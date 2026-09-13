# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.error import InvalidToken, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
)

# ----------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except Exception:
    ZoneInfo = None
    HAS_ZONEINFO = False

# ----------------------------

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------------------------

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID_ENV = int_filter(os.environ.get("ADMIN_ID", "").strip()) if "ADMIN_ID" in os.environ else None

TIMEZONE_NAME = os.environ.get("TIMEZONE", "Asia/Tehran").strip() or "Asia/Tehran"
SEND_TIME = os.environ.get("SEND_TIME", "08:30").strip() or "08:30"

DATA_DIR_RAW = os.environ.get("DATA_DIR", "").strip() or "data"
DATA_DIR = Path(DATA_DIR_RAW)
DATA_FILE = DATA_DIR / "bot_data.json"

DISABLE_PHOTOS_RAW = os.environ.get("DISABLE_PHOTOS", "").strip().lower()
DISABLE_PHOTOS = DISABLE_PHOTOS_RAW in {"1", "true", "yes", "on"}

# Sticker ids اختیاری‌ان
STICKER_IDS = {
    "welcome": os.environ.get("STICKER_ID_WELCOME", "").strip(),
    "romantic": os.environ.get("STICKER_ID_ROMANTIC", "").strip(),
    "hope": os.environ.get("STICKER_ID_HOPE", "").strip(),
    "morning": os.environ.get("STICKER_ID_MORNING", "").strip(),
    "night": os.environ.get("STICKER_ID_NIGHT", "").strip(),
    "mixed": os.environ.get("STICKER_ID_MIXED", "").strip(),
}

WELCOME_PHOTO_URL_DEFAULT = "https://picsum.photos/seed/goodmorning/1200/600"
WELCOME_PHOTO_URL = os.environ.get("WELCOME_PHOTO_URL", "").strip() or WELCOME_PHOTO_URL_DEFAULT

PHOTOS = {
    "romantic": os.environ.get("PHOTO_URL_ROMANTIC", "").strip() or "https://picsum.photos/seed/love/1200/600",
    "hope": os.environ.get("PHOTO_URL_HOPE", "").strip() or "https://picsum.photos/seed/hope/1200/600",
    "morning": os.environ.get("PHOTO_URL_MORNING", "").strip() or "https://picsum.photos/seed/morning/1200/600",
    "night": os.environ.get("PHOTO_URL_NIGHT", "").strip() or "https://picsum.photos/seed/night/1200/600",
    "mixed": os.environ.get("PHOTO_URL_MIXED", "").strip() or "https://picsum.photos/seed/mixed/1200/600",
}

# ----------------------------

DEFAULT_NAME = "عزیزم"
DEFAULT_CATEGORY = "mixed"
DEFAULT_TONE = "friendly"

REAL_CATEGORIES = ["romantic", "hope", "morning", "night"]

CATEGORY_TO_LABEL = {
    "romantic": "عاشقانه",
    "hope": "امیدوارکننده",
    "morning": "صبح‌بخیر",
    "night": "خوب‌شب",
    "mixed": "ترکیبی",
}
CATEGORY_LABEL_TO = {v: k for k, v in CATEGORY_TO_LABEL.items()}

CATEGORY_OPTIONS = [
    (1, "عاشقانه", "romantic"),
    (2, "امیدوارکننده", "hope"),
    (3, "صبح‌بخیر", "morning"),
    (4, "خوب‌شب", "night"),
    (5, "ترکیبی", "mixed"),
]

TONE_TO_LABEL = {
    "friendly": "صمیمی",
    "poetic": "شاعرانه",
    "formal": "رسمی",
    "short": "کوتاهِ خودمونی",
}
TONE_LABEL_TO = {v: k for k, v in TONE_TO_LABEL.items()}

TONE_OPTIONS = [
    (1, "صمیمی", "friendly"),
    (2, "شاعرانه", "poetic"),
    (3, "رسمی", "formal"),
    (4, "کوتاهِ خودمونی", "short"),
]

# ----------------------------

MESSAGES = {
    "romantic": {
        "friendly": [
            "صبح بخیر {NAME} عزیزم 💛 امیدوارم امروزت پر از آرامش و لبخند باشه.",
            "سلام {NAME} جان! تو یکی از قشنگ‌ترین دلایلِ روزهای خوبِ منی، امروزت هم درخشان باشه ✨",
            "{NAME} عزیزم، صبحت بخیر! امروز با عشق و امید شروع می‌شه ❤️",
            "سلام به {NAME} مهربون! امیدوارم الان یه لبخندِ واقعی رو لبت باشه 🌸",
            "صبح بخیر {NAME}! یادت نره چقدر دوست‌داشتنی و قشنگی 🌷",
        ],
        "poetic": [
            "صبح تو بخیر، {NAME}؛ تو مثل نوری که بر روز من تابیده، بی‌نهایتی 🌹",
            "سلام به {NAME} جان؛ هر صبح دلم با یادِ تو بیدار می‌شود 🌙💖",
            "{NAME} عزیزم، آفتاب به احترامِ نام‌ت طلوع می‌کند؛ امروزت عاشقانه باد.",
            "صبح توتو باور کن، {NAME}؛ تو قشنگ‌ترین شعرِ ناخوانده‌ی زندگی منی 💫",
            "{NAME} جان، تو آرامشی که بی‌صدی بر دلم می‌آید؛ صبحت به‌قشنگیِ تو 💍",
        ],
        "formal": {0},
        "formal": [
            "صبح بخیر؛ آرزومندم امروز برای شما سرشار از آرامش و شادی باشد. 💼",
            "سلام؛ قدردانِ حضورِ ارزشمندِ {NAME} گرامی هستم؛ روزتان درخشان باد.",
            "{NAME} عزیز، صبح بخیر؛ برایتان روزی موفق و دلنشین آرزو می‌کنم.",
            "سلام و عرض ادب؛ امید است امروز برای شما به‌خوبیِ انتظارِ ما از آینده باشد.",
            "صبح‌تان بخیر؛ آرزومند به شما، {NAME} عزیز، روزی سرشار از مهربانی.",
        ],
        "short": [
            "صبح، {NAME} 💛",
            "سلام {NAME} ☀️",
            "{NAME} عزیز ❤️",
            "امروز برای {NAME} خوبه ✨",
            "{NAME}، لبخند تو همه چیه 😊",
        ],
    },

    "hope": {
        "friendly": [
            "صبح بخیر {NAME}! یادت نره هر روز یه شانس تازه‌ست؛ من بهت ایمان دارم 💪",
            "سلام {NAME} جان؛ امروزت پر از امید باشه و هر در بسته‌ای سرانجام باز می‌شه 🔓✨",
            "{NAME} عزیز، اگر خسته‌ای فقط یه نفس عمیق بکش و دوباره ادامه بده؛ تو قوی‌تر از چیزی‌ای که فکر می‌کنی.",
            "صبح بخیر {NAME}! یه قدم کوچیک امروز، فردا بزرگ می‌شه؛ من همراهتم 🌱",
            "سلام به {NAME} با انرژی! امروزت پر از حس‌های خوبه؛ تو می‌تونی 🌈",
        ],
        "poetic": [
            "صبح تو بخیر {NAME}؛ روزهای سخت از میان مه می‌روند و صبر، شکوفه می‌زند 🌦️",
            "سلام به {NAME} جان؛ امید، چراغی است در دست‌های بی‌قرار؛ امروز آن را روشن بدار.",
            "{NAME} عزیزم، فردا می‌آید، حتی اگر امروز دیر بیاید؛ تو به فردا ایمان بیاور.",
            "روزت به امیدِ تو روشن، {NAME}؛ صبر، صبح است که می‌رسد 🌄",
            "{NAME} جان، حتی در سخت‌ترین لحظه، نور از لای ابرها سرک می‌کشد؛ تو همان نوری.",
        ],
        "formal": [
            "صبح بخیر؛ امیدوارم امروز سرشار از آرامش، موفقیت و افق‌های روشن باشد.",
            "سلام؛ باورِ من بر پایداری و امید شما استوار است؛ روزتان درخشان باد.",
            "{NAME} گرامی، روزِ شما به خیر؛ گشایش و امید در تمامِ مسیرها آرزو دارم.",
            "روز بخیر؛ هر گام، حتی کوچک، شما را به آینده‌ای روشن نزدیک‌تر می‌کند.",
            "سلام {NAME} گرامی؛ برایتان روزه‌ای پر از برکت و امید آرزو می‌کنم.",
        ],
        "short": [
            "امید، {NAME} ✨",
            "قوی باش {NAME} 💪",
            "امروز، فردا می‌شه 🌱",
            "{NAME}، ادامه بده!",
            "فردا بهتر از دیروزه {NAME} 🌼",
        ],
    },

    "morning": {
        "friendly": [
            "صبح بخیر {NAME} ☀️ قهوه‌ات داغ، دلت آروم.",
            "سلام {NAME}! امروز رو مثل یه هدیه باز کن 🎁",
            "صبح قشنگ به {NAME} مهربون 🌼",
            "{NAME} جان، صحت بخیر! لبخندت هم مثل خورشید باشه 🌞",
            "سلام صبح‌بخیر {NAME}! امروزت خوش‌رنگ باشه ✨",
        ],
        "poetic": [
            "صبح بخیر {NAME}؛ خورشید برای تو برآمد، و تو برای آرامش 🌅",
            "سلام به {NAME} جان؛ صبح، نامِ تو را می‌خواند.",
            "صبحِ تو بخیر، {NAME}؛ روزت پر از نسیم‌های مهربان 🍂",
            "{NAME} عزیز، صبح از پنجره‌ات وارد شد؛ جایش را باز کن.",
            "پنجره باز می‌شود و صبح، {NAME} را می‌خواند؛ بیدار شو و بدرخش 🌸",
        ],
        "formal": [
            "صبح بخیر؛ روزتان سرشار از آرامش و بهره‌وری.",
            "سلام؛ برایتان صبحی روشن‌تر از دیروز آرزو می‌کنم.",
            "{NAME} گرامی، صبح‌تان بخیر؛ روزتان مفید و ارزشمند باد.",
            "روز به خیر؛ امید است آغازِ امروز، سرآغازِ بهتر باشد.",
            "صبح‌تان به نیکی، {NAME} عزیز.",
        ],
        "short": [
            "صبح، {NAME} ☕",
            "صبح بخیر {NAME} ✨",
            "روز {NAME} خوب",
            "سلام، {NAME} 🌻",
            "امروز {NAME}، شروع تازه 🌱",
        ],
    },

    "night": {
        "friendly": [
            "شبِ {NAME} آروم 🌙؛ یادت باشه هر روزی که تموم شد، یه پیروزیه.",
            "خوب شب {NAME} عزیز؛ خسته نباشی، فردا دوباره قشنگ‌تر شروع می‌شه ✨",
            "شبت بخیر {NAME}، امیدوارم خواب‌های خوش‌رنگ ببینی ⭐",
            "شب، {NAME} جان؛ همه‌چیز همون‌طور که باید تموم شد و تو عالی بودی 😌",
            "خوب‌شب عزیزم {NAME}؛ فردا دوباره بهت انرژی می‌دم 💖",
        ],
        "poetic": [
            "شب به خیر {NAME}؛ ماه به پشت‌بامِ تو رسیده و ستاره‌ها برایت نگهبان‌اند 🌌",
            "خوب شبِ {NAME}؛ روز با تمامِ آفتابش آرام می‌گیرد و امید برای فردا باقی است.",
            "شب، {NAME} جان، آرامش دارد؛ تو هم آرام شو.",
            "تو بخواب {NAME}؛ صبح از راه می‌آید و تو را روشن می‌کند 🌃",
            "ستاره‌ها برای {NAME} می‌درخشند؛ آرام بگیر و فردا را بسپار به نور.",
        ],
        "formal": [
            "شب بخیر؛ امیدوارم خوابی آرام و فردایی پرانرژی داشته باشید.",
            "شبتان بخیر {NAME} گرامی؛ آرامشِ شب در آسایشِ فردا.",
            "با آرزوی آرامش، فردایی روشن به شما باشد.",
            "شب‌تان به خیر؛ امید است فردا برای شما بهتر از دیروز باشد.",
            "شبتان آرام، {NAME} گرامی.",
        ],
        "short": [
            "شب بخیر {NAME} 🌙",
            "خوب شب عزیز 💖",
            "فردا، {NAME} ✨",
            "بخواب آرام، {NAME} 💤",
            "شبِ {NAME} خوب 🌠",
        ],
    },
}

# fix accidental typo-safe fallback
for cat in MESSAGES:
    for tone_key in ["friendly", "poetic", "formal", "short"]:
        MESSAGES[cat].setdefault(tone_key, ["صبح بخیر {NAME} عزیزم 💛"])

# ----------------------------

def int_filter(value: str):
    value = (value or "").strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None

def looks_int(value: str):
    value = (value or "").strip()
    return value[1:].isdigit() if value.startswith("-") and len(value) > 1 else value.isdigit()

def get_tz(name: str):
    name = (name or TIMEZONE_NAME).strip() or TIMEZONE_NAME
    if HAS_ZONEINFO:
        try:
            return ZoneInfo(name)
        except Exception:
            logger.warning(f"Invalid timezone: {name}, fallback to UTC")
            return timezone.utc
    # fallback without zoneinfo
    return timezone.utc

def current_timezone():
    tz_name = data.get("settings", {}).get("timezone") or TIMEZONE_NAME
    return get_tz(tz_name)

def parse_time(time_str: str):
    try:
        h, m = time_str.strip().split(":", 1)
        hour = int(h)
        minute = int(m)
        if 0 <= hour < 24 and 0 <= minute < 60:
            return hour, minute
    except Exception:
        pass
    logger.warning(f"Invalid SEND_TIME '{time_str}', fallback 08:30")
    return 8, 30

def get_target_minutes():
    raw = data.get("settings", {}).get("send_time") or SEND_TIME
    return parse_time(raw)

def is_time_passed(now: datetime):
    h, m = get_target_minutes()
    return now.hour > h or (now.hour == h and now.minute >= m)

def now_and_passed():
    tz = current_timezone()
    now = datetime.now(tz)
    return now, is_time_passed(now)

def resolve_category(value):
    value = str(value or "").strip()
    if looks_int(value):
        idx = int(value)
        for i, lbl, key in CATEGORY_OPTIONS:
            if idx == i:
                return key
        return None
    low = value.lower()
    if low in CATEGORY_TO_LABEL:
        return low
    if value in CATEGORY_LABEL_TO:
        return CATEGORY_LABEL_TO[value]
    return None

def resolve_tone(value):
    value = str(value or "").strip()
    if looks_int(value):
        idx = int(value)
        for i, lbl, key in TONE_OPTIONS:
            if idx == i:
                return key
        return None
    low = value.lower()
    if low in TONE_TO_LABEL:
        return low
    if value in TONE_LABEL_TO:
        return TONE_LABEL_TO[value]
    return None

def effective_muted_uid(profile: dict, uid_str: str):
    muted = bool(profile.get("muted", False))
    admin_id = data.get("admin_id")
    if admin_id is not None and str(admin_id) == uid_str:
        if not bool(profile.get("manual_unmuted", False)) and not muted:
            muted = False
        # For admin, if profile is missing manual_unmuted then treat as muted
        if "manual_unmuted" not in profile:
            muted = True
    return muted

def get_sticker_id(category: str):
    cat = (category or "").strip()
    if STICKER_IDS.get(cat, "").strip():
        return STICKER_IDS[cat].strip()
    if STICKER_IDS.get("mixed", "").strip():
        return STICKER_IDS["mixed"].strip()
    return ""

def get_photo_url(category: str):
    if DISABLE_PHOTOS:
        return ""
    cat = (category or "").strip()
    return PHOTOS.get(cat, PHOTOS.get("mixed", ""))

def normalize_profile(profile: dict, uid: int):
    out = {
        "name": str(profile.get("name") or "").strip(),
        "category": resolve_category(profile.get("category")) or DEFAULT_CATEGORY,
        "tone": resolve_tone(profile.get("tone")) or DEFAULT_TONE,
        "muted": bool(profile.get("muted", False)),
        "manual_unmuted": bool(profile.get("manual_unmuted", False)),
        "last_sent_date": profile.get("last_sent_date") if isinstance(profile.get("last_sent_date"), str) else None,
    }
    return out

def build_default_profile(uid: int, name: str = "", muted: bool = False):
    now, passed = now_and_passed()
    last_date = None
    if passed and not muted:
        last_date = now.date().isoformat()

    profile = {
        "name": name or "",
        "category": DEFAULT_CATEGORY,
        "tone": DEFAULT_TONE,
        "muted": muted,
        "manual_unmuted": False,
        "last_sent_date": last_date,
    }
    return profile

# ----------------------------

def atomic_write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(obj)
    Path.replace(tmp, path)

def load_data():
    default = {
        "admin_id": None,
        "users": {},
        "settings": {
            "send_time": SEND_TIME,
            "timezone": TIMEZONE_NAME,
        },
    }

    if ADMIN_ID_ENV is not None:
        default["admin_id"] = ADMIN_ID_ENV

    path = DATA_FILE
    if path.exists():
        try:
            import json
            with path.open("r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {path}: {e}")
            obj = default

        if not isinstance(obj, dict):
            obj = default

        users = obj.get("users") if isinstance(obj.get("users"), dict) else {}
        norm_users = {}
        for uid_str, profile in users.items():
            try:
                uid_int = int(uid_str)
            except Exception:
                continue
            if profile is None or not isinstance(profile, dict):
                profile = {}
            norm_users[uid_str] = normalize_profile(profile, uid_int)

        settings = obj.get("settings") if isinstance(obj.get("settings"), dict) else {}
        settings.setdefault("send_time", SEND_TIME)
        settings.setdefault("timezone", TIMEZONE_NAME)

        admin_id = obj.get("admin_id")
        if admin_id is not None:
            try:
                admin_id = int(admin_id)
            except Exception:
                admin_id = None

        if ADMIN_ID_ENV is not None:
            admin_id = ADMIN_ID_ENV
        if admin_id is None:
            admin_id = None

        obj["users"] = norm_users
        obj["settings"] = settings
        obj["admin_id"] = admin_id

        # if there is no admin but env exists already handled above

        return obj

    return default

def save_data():
    try:
        import json
        atomic_write(DATA_FILE, json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error(f"Could not save data: {e}")

data = load_data()

def ensure_loaded_data():
    users = data.get("users", {})
    need_save = False
    for uid_str in list(users.keys()):
        try:
            uid = int(uid_str)
        except Exception:
            users.pop(uid_str, None)
            need_save = True
            continue
        norm = normalize_profile(users.get(uid_str, {}), uid)
        prev = users.get(uid_str)
        if prev != norm:
            users[uid_str] = norm
            need_save = True
    if need_save:
        save_data()

ensure_loaded_data()

# ----------------------------

async def deliver_text(bot, chat_id, text: str, sticker_id: str = "", photo_url: str = ""):
    text = str(text or "").strip()
    if not text:
        return
    chat_id = int(chat_id)

    sticker_id = (sticker_id or "").strip()
    photo_url = (photo_url or "").strip()

    if sticker_id:
        try:
            await bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
            await bot.send_message(chat_id=chat_id, text=text)
            return
        except TelegramError:
            pass

    if photo_url and len(text) <= 900:
        try:
            await bot.send_photo(chat_id=chat_id, photo=photo_url, caption=text)
            return
        except TelegramError:
            pass

    await bot.send_message(chat_id=chat_id, text=text)

async def send_admin_notice(bot, text: str):
    admin_id = data.get("admin_id")
    if not admin_id:
        return
    try:
        await deliver_text(bot, int(admin_id), text)
    except Exception:
        pass

async def send_long_message(bot, chat_id, text: str):
    chat_id = int(chat_id)
    text = str(text or "").strip()
    if not text:
        return
    if len(text) <= 3500:
        await bot.send_message(chat_id=chat_id, text=text)
        return
    for i in range(0, len(text), 3500):
        await bot.send_message(chat_id=chat_id, text=text[i:i+3500])

# ----------------------------

def is_admin(uid) -> bool:
    admin_id = data.get("admin_id")
    return admin_id is not None and int(uid) == int(admin_id)

def get_or_create_profile(target_uid) -> dict:
    uid_str = str(int(target_uid))
    profile = data.get("users", {}).get(uid_str)
    if profile is None:
        admin_id = data.get("admin_id")
        default_muted = (admin_id is not None and int(admin_id) == int(target_uid))
        profile = build_default_profile(int(target_uid), muted=default_muted)
        data["users"][uid_str] = profile
        save_data()
    else:
        data["users"][uid_str] = normalize_profile(profile, int(target_uid))
        save_data()
    return data["users"][uid_str]

def get_or_create_current_profile(update: Update, claim_admin: bool = False) -> dict:
    uid = int(update.effective_chat.id)
    uid_str = str(uid)
    admin_id = data.get("admin_id")

    if claim_admin and admin_id is None:
        data["admin_id"] = uid

    if uid_str not in data["users"]:
        default_muted = (data.get("admin_id") is not None and int(data.get("admin_id")) == uid)
        if claim_admin and admin_id is None:
            default_muted = True
        data["users"][uid_str] = build_default_profile(uid, muted=default_muted)
    else:
        data["users"][uid_str] = normalize_profile(data["users"][uid_str], uid)

    profile = data["users"][uid_str]

    # Claim admin manually: if this command was claimed, make sure admin not receiving by default
    if claim_admin and is_admin(uid):
        if not bool(profile.get("manual_unmuted")):
            profile["muted"] = True
        profile["manual_unmuted"] = False if ADMIN_ID_ENV is not None else not bool(profile.get("manual_unmuted", False))

    save_data()
    return profile

# ----------------------------

def category_label(cat):
    return CATEGORY_TO_LABEL.get(cat, cat or "")

def tone_label(tone):
    return TONE_TO_LABEL.get(tone, tone or "")

def profile_text(uid: int, profile: dict):
    admin_id = data.get("admin_id")
    uid_str = str(uid)
    muted = effective_muted_uid(profile, uid_str)

    name = profile.get("name") or DEFAULT_NAME
    cat = resolve_category(profile.get("category")) or DEFAULT_CATEGORY
    tone = resolve_tone(profile.get("tone")) or DEFAULT_TONE
    last_date = profile.get("last_sent_date") or "هنوز ارسال نشده"

    lines = [
        f"🆔 شناسه چت: `{uid}`",
        f"👤 نام: {name}",
        f"💫 دسته‌بندی: {category_label(cat)}",
        f"🗣️ لحن: {tone_label(tone)}",
        f"📩 وضعیت پیام روزانه: {'قطع 🔕' if muted else 'فعال ✅'}",
        f"🌸 آخرین پیام: {last_date}",
    ]
    if admin_id is not None and uid == int(admin_id):
        lines.insert(0, "👑 شما ادمین این ربات هستید.")
    return "\n".join(lines)

def help_text():
    text = (
"📘 راهنمای دستورات:\n\n"
"/id - نمایش شناسه چت شما\n"
"/start - فعال‌سازی و خوش‌آمد\n"
"/help - همین راهنما\n"
"/settings - منوی تنظیمات\n"
"/mute - قطع پیام روزانه\n"
"/unmute - وصل کردن دوباره\n"
"/unsubscribe - حذف شدن از لیست\n"
"/name [اسم] - تغییر اسم نمایشی\n"
"/category - انتخاب دسته‌بندی پیام\n"
"/tone - انتخاب لحن پیام\n"
"/time - نمایش ساعت فعلی ارسال\n"
"/test - ارسال فوری یک پیام تستی\n\n\n"
"👑 دستورات ادمین:\n"
"/admin - پنل ادمین و افزودن دوست\n"
"/addfriend CHAT_ID [نام] - افزودن دوست به لیست\n"
"/removefriend CHAT_ID - حذف دوست از لیست\n"
"/friends - لیست دوستان\n"
"/mutefriend CHAT_ID - قطع پیام دوست با اجازه ادمین\n\n\n"
"/settime HH:MM - تغییر ساعت ارسال\n"
"/setname CHAT_ID [اسم] - تغییر اسم دوست\n"
"/setcategory CHAT_ID [شماره/نام] - تنظیم دسته دوست\n"
"/settone CHAT_ID [شماره/نام] - تنظیم لحن دوست\n\n\n"
"/settime - فقط ادمین\n"
    )
    return text

def settings_text(uid: int, profile: dict):
    base = profile_text(uid, profile) + "\n\n"
    base += "برای انتخاب، فقط شماره گزینه زیر را بنویس:\n"
    base += "1️⃣ تغییر نام من\n"
    base += "2️⃣ تغییر دسته‌بندی پیام\n"
    base += "3️⃣ تغییر لحن پیام\n"
    base += "4️⃣ قطع پیام روزانه\n"
    base += "5️⃣ وصل کردن دوباره\n"
    base += "6️⃣ حذف اشتراک\n"
    base += "7️⃣ بازگشت/لغو\n"
    if is_admin(uid):
        base += "\n🛠️ ابزار ادمین:\n"
        base += "8️⃣ لیست دوستان\n"
        base += "9️⃣ افزودن دوست\n"
        base += "🔟 حذف دوست\n"
        base += "⏰ نمایش زمان ارسالی\n"
    base += "\n"
    return base

def add_user_text() -> str:
    return "برای افزودن دوست، این قالب رو بفرست:\n`/addfriend 123456789 عشقم`\nیا فقط عدد آیدی دوستت رو بنویس."

def remove_user_text() -> str:
    return "برای حذف دوست، آیدی چت دوستت رو بنویس."

def category_menu_text() -> str:
    lines = ["دسته‌بندی پیام‌ها رو انتخاب کن:"]
    for idx, label, val in CATEGORY_OPTIONS:
        lines.append(f"{idx}️⃣ {label}")
    lines.append("")
    lines.append("می‌تونی اسم دقیق دسته رو هم تایپ کنی")
    return "\n".join(lines)

def tone_menu_text() -> str:
    lines = ["لحن پیام‌ها رو انتخاب کن:"]
    for idx, label, val in TONE_OPTIONS:
        lines.append(f"{idx}️⃣ {label}")
    return "\n".join(lines)

def admin_text(uid: int):
    panel = (
"👑 پنل ادمین\n"
f"شناسه ادمین فعلی: `{uid}`\n\n"
"دستور اصلی:\n"
"/addfriend CHAT_ID [نام]  → افزودن دوست و فعال کردن پیام\n\n"
"مدیریت دوست:\n"
"/mutefriend CHAT_ID → قطع پیام روزانه دوست\n"
"/unmutefriend CHAT_ID → وصل کردن پیام روزانه دوست\n"
" /unsubscribe CHAT_ID → حذف دوست\n"
"/friends → نمایش لیست دوستان\n"
"/setname CHAT_ID [name] → تنظیم اسم دوست\n"
"/setcategory CHAT_ID [number/or name] → تنظیم دسته‌بندی دوست\n"
"/settone CHAT_ID [number/or name] → تنظیم لحن دوست\n"
"/test CHAT_ID → تست فوری پیام برای یک دوست\n\n"
"تنظیمات:\n"
"/settime HH:MM → تغییر ساعت ارسال روزانه\n"
"/time → نمایش زمان فعلی\n\n"
"نکته:\n"
"اگر دوستت تا الان ربات را باز نکرده، ممکن است پیام دریافت کند یا خطای Forbidden دریافت شود؛ در این صورت لازم است یک بار خود کاربر `/start` بزند."
    )
    return panel

def get_friends_text():
    lines = ["👥 لیست دوستان:\n"]
    users = data.get("users", {})
    if not users:
        lines.append("هنوز دوستی اضافه نشده.\n\nبرای افزودن: /addfriend 123456789 نام دوست")

    admin_id = data.get("admin_id")
    for idx, uid_str in enumerate(sorted(users.keys(), key=lambda x: int(x))):
        uid = int(uid_str)
        profile = normalize_profile(users.get(uid_str, {}), uid)
        name = profile.get("name") or DEFAULT_NAME
        cat = resolve_category(profile.get("category")) or DEFAULT_CATEGORY
        tone = resolve_tone(profile.get("tone")) or DEFAULT_TONE
        muted = effective_muted_uid(profile, uid_str)
        role = "👑" if admin_id is not None and int(admin_id) == uid else "🌼"
        lines.append(f"{role} `{uid}` — {name} | {category_label(cat)} | {tone_label(tone)} | {'قطع 🔕' if muted else 'فعال ✅'}")
    return "\n".join(lines)

# ----------------------------

def build_message_for_uid(uid: int) -> dict:
    today = current_timezone().today().isoformat()
    uid_str = str(uid)
    prof = data.get("users", {}).get(uid_str)
    if prof is None:
        prof = build_default_profile(uid, muted=False)
        data["users"][uid_str] = prof

    profile = normalize_profile(prof, uid)

    cat_raw = profile.get("category")
    cat_value = resolve_category(cat_raw) or DEFAULT_CATEGORY

    tone_value = resolve_tone(profile.get("tone")) or DEFAULT_TONE

    if cat_value == "mixed":
        rng_cat = random.Random(f"{today}|mixed|{uid}")
        real_cat = rng_cat.choice(REAL_CATEGORIES)
    else:
        real_cat = cat_value if cat_value in MESSAGES else "mixed"

    tone_data = MESSAGES.get(real_cat, {})
    templates = tone_data.get(tone_value) or tone_data.get("friendly") or templates if False else None
    if not templates:
        templates = MESSAGES.get("mixed", {}).get("friendly") or []
    if not templates:
        templates = ["صبح بخیر {NAME} عزیزم 💛"]

    seed = f"{today}|{uid}|{real_cat}|{tone_value}"
    choice_rng = random.Random(seed)
    template = choice_rng.choice(templates)

    name = profile.get("name") or DEFAULT_NAME
    text = template.replace("{NAME}", name)

    sticker_id = get_sticker_id(real_cat)
    photo_url = get_photo_url(real_cat)

    return {
        "uid": uid,
        "text": text,
        "sticker": sticker_id,
        "photo": photo_url,
    }

def build_test_text_for_uid(uid: int) -> dict:
    msg = build_message_for_uid(uid)
    prefix = ""
    if msg.get("text").startswith("شب"):
        prefix = "🌙 تست شب\n"
    elif "عاشقانه" not in data.get("users", {}).get(str(uid), {}).get("category", "").lower():
        pass
    msg["text"] = f"🧪 {msg['text']}" + ""
    return msg

# ----------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_menu(context)
    uid = int(update.effective_chat.id)
    first_name = update.effective_user.first_name or ""
    claim = False
    if data.get("admin_id") is None:
        claim = True

    profile = get_or_create_current_profile(update, claim_admin=claim)

    if is_admin(uid):
        text = (
            f"سلام {first_name} عزیز 👑\n"
            "ربات صبح‌بخیر عاشقانه/امیدوارکننده آماده است.\n\n"
            "برای اضافه کردن دوستت:\n"
            "/addfriend 123456789 نام دوست\n"
            "/friends\n"
            "/help\n"
        )
        await send_long_message(context.bot, uid, text)
    else:
        text = (
            f"❤️ سلام {first_name} عزیزم\n"
            "از امروز هر صبح پیام‌های پرامید و عشق‌میز برات می‌فرستم ✨\n\n"
            "برای تنظیمات: /settings\n"
            "برای دستورات: /help"
        )
        sticker_id = STICKER_IDS.get("welcome", "")
        photo_url = WELCOME_PHOTO_URL if not DISABLE_PHOTOS else ""
        try:
            if not DISABLE_PHOTOS or sticker_id:
                await deliver_text(
                    context.bot,
                    uid,
                    text,
                    sticker_id=sticker_id,
                    photo_url=photo_url,
                )
            else:
                await send_long_message(context.bot, uid, text)
        except Exception:
            await send_long_message(context.bot, uid, text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 راهنمای دستورات:\n\n"
        "/start  → فعال‌سازی و منوی تنظیمات\n"
        "/id     → نمایش شناسه چت شما\n"
        "/name   → (به‌زودی) تنظیم نام\n"
        "/category → انتخاب دسته‌بندی پیام\n"
        "/tone   → انتخاب لحن پیام\n"
        "/test   → ارسال یک پیام فوری\n"
        "/status → نمایش وضعیت فعلی\n"
        "/mute   → قطع پیام روزانه\n"
        "/unmute → برقراری مجدد\n"
        "/admin  → پنل ادمین (افزودن دوست)\n"
    )
    await update.message.reply_text(text)
