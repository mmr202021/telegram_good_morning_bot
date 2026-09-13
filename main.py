import os
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


# -----------------------------
# تنظیمات اصلی
# -----------------------------

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError(
        "توکن بات پیدا نشد. ابتدا متغیر BOT_TOKEN را تنظیم کنید."
    )

TIMEZONE = ZoneInfo("Asia/Tehran")

# ساعت ارسال پیام روزانه
SEND_HOUR = 9
SEND_MINUTE = 0

DATABASE_NAME = "love_bot.db"


# -----------------------------
# پیام‌های عاشقانه
# -----------------------------

LOVE_MESSAGES = [
    "تو قشنگ‌ترین اتفاقی هستی که زندگی به من هدیه داده است 🤍",
    "کنار تو حتی سکوت هم شبیه یک شعر عاشقانه است 🎶❤️",
    "هر صبح که بیدار می‌شوم، از اینکه تو را در زندگی‌ام دارم لبخند می‌زنم ☀️😊",
    "دوست داشتنت برای من انتخاب نیست؛ زیباترین بخش وجود من است 💖",
    "اگر عشق یک خانه باشد، من دوست دارم همیشه در قلب تو زندگی کنم 🏡❤️",
    "تو دلیل خیلی از لبخندهای بی‌دلیل من هستی 🌸",
    "با تو ساده‌ترین لحظه‌ها هم تبدیل به خاطره‌ای ماندگار می‌شوند ✨",
    "در میان تمام آدم‌های دنیا، قلب من فقط تو را بلد است 💌",
    "هر بار که به تو فکر می‌کنم، دنیا کمی زیباتر می‌شود 🌍💞",
    "تو همان آرامشی هستی که همیشه دنبالش می‌گشتم 🕊️",
    "عشق یعنی کسی باشد که حتی در سخت‌ترین روزها، دلت بخواهد کنارش بمانی 🤍",
    "من تو را نه فقط برای امروز، بلکه برای تمام فرداهایم می‌خواهم 🌹",
    "بودنت کنار من، زیباترین دلیل برای ادامه دادن است 🌟",
    "گاهی فقط دیدن نامت روی صفحه کافی است تا تمام خستگی‌هایم ناپدید شوند 📱❤️",
    "تو برای من فقط یک نفر نیستی؛ تمام دنیای منی 🌎💗",
    "اگر دوباره به دنیا بیایم، باز هم تو را انتخاب می‌کنم 💍",
    "قلب من با شنیدن صدای تو، آرام‌ترین موسیقی دنیا را می‌شنود 🎵",
    "دوستت دارم؛ کوتاه‌ترین جمله‌ای که عمیق‌ترین احساس من را بیان می‌کند ❤️",
    "عشق من به تو هر روز تازه‌تر، عمیق‌تر و زیباتر می‌شود 🌷",
    "در کنار تو، آینده دیگر ترسناک نیست؛ چون می‌دانم با هم هستیم 🤝💕",
    "تو همان معجزه‌ای هستی که زندگی من را از معمولی بودن نجات داد ✨",
    "هر لحظه با تو، یک دلیل تازه برای عاشق‌تر شدن دارم 😍",
    "لبخندت برای من شبیه طلوع خورشید بعد از یک شب طولانی است 🌅",
    "من به بودن تو افتخار می‌کنم و هر روز بیشتر از قبل دوستت دارم 💝",
]


# -----------------------------
# ساخت دیتابیس
# -----------------------------

def init_database():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            is_active INTEGER DEFAULT 1,
            joined_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_messages (
            user_id INTEGER,
            message_date TEXT,
            PRIMARY KEY (user_id, message_date)
        )
    """)

    connection.commit()
    connection.close()


def add_user(user_id: int, first_name: str):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (user_id, first_name, is_active, joined_at)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            is_active = 1
    """, (
        user_id,
        first_name,
        datetime.now(TIMEZONE).isoformat()
    ))

    connection.commit()
    connection.close()


def deactivate_user(user_id: int):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE users SET is_active = 0 WHERE user_id = ?",
        (user_id,)
    )

    connection.commit()
    connection.close()


def get_active_users():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT user_id FROM users WHERE is_active = 1"
    )

    users = [row[0] for row in cursor.fetchall()]
    connection.close()

    return users


def message_was_sent(user_id: int, message_date: str) -> bool:
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1 FROM sent_messages
        WHERE user_id = ? AND message_date = ?
    """, (user_id, message_date))

    result = cursor.fetchone()
    connection.close()

    return result is not None


def save_sent_message(user_id: int, message_date: str):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO sent_messages
        (user_id, message_date)
        VALUES (?, ?)
    """, (user_id, message_date))

    connection.commit()
    connection.close()


# -----------------------------
# ظاهر و دکمه‌های بات
# -----------------------------

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💌 پیام امروز"),
                KeyboardButton(text="❤️ عضویت در پیام‌ها"),
            ],
            [
                KeyboardButton(text="🔕 لغو دریافت پیام‌ها"),
                KeyboardButton(text="ℹ️ راهنما"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❤️ دریافت پیام‌های روزانه",
                    callback_data="subscribe"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔕 لغو دریافت پیام‌ها",
                    callback_data="unsubscribe"
                )
            ],
        ]
    )


def get_daily_message():
    today = datetime.now(TIMEZONE).date()
    index = today.toordinal() % len(LOVE_MESSAGES)
    return LOVE_MESSAGES[index]


def format_love_message():
    today = datetime.now(TIMEZONE).strftime("%Y/%m/%d")
    message = get_daily_message()

    return (
        f"💌 <b>پیام عاشقانه امروز</b>\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"✨ {message}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌹 <i>هر روز با یک جمله، قلبت را گرم نگه دار</i>\n"
        f"📅 {today}"
    )


# -----------------------------
# ساخت بات
# -----------------------------

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# -----------------------------
# دستورات کاربران
# -----------------------------

@dp.message(CommandStart())
async def start_handler(message: Message):
    add_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name or "دوست عزیز"
    )

    await message.answer(
        f"سلام {message.from_user.first_name or 'عزیزم'} 🌹\n\n"
        "به بات پیام‌های عاشقانه خوش آمدی 💌\n\n"
        "از این به بعد هر روز یک پیام زیبا و عاشقانه برایت ارسال می‌کنم ❤️",
        reply_markup=main_keyboard()
    )

    await message.answer(
        "از دکمه‌های زیر می‌توانی استفاده کنی:",
        reply_markup=subscription_keyboard()
    )


@dp.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    add_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name or "دوست عزیز"
    )

    await message.answer(
        "عضویتت با موفقیت انجام شد ❤️\n"
        "هر روز یک پیام عاشقانه برایت ارسال می‌کنم 💌",
        reply_markup=main_keyboard()
    )


@dp.message(Command("unsubscribe"))
async def unsubscribe_handler(message: Message):
    deactivate_user(message.from_user.id)

    await message.answer(
        "دریافت پیام‌های روزانه متوقف شد 🔕\n"
        "هر زمان خواستی، دوباره روی «عضویت در پیام‌ها» بزن ❤️",
        reply_markup=main_keyboard()
    )


@dp.message(Command("now"))
async def now_handler(message: Message):
    await message.answer(
        format_love_message(),
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "💌 پیام امروز")
async def today_message_handler(message: Message):
    await message.answer(
        format_love_message(),
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "❤️ عضویت در پیام‌ها")
async def subscribe_button_handler(message: Message):
    add_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name or "دوست عزیز"
    )

    await message.answer(
        "عالیه! از این به بعد هر روز پیام عاشقانه دریافت می‌کنی 💖",
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "🔕 لغو دریافت پیام‌ها")
async def unsubscribe_button_handler(message: Message):
    deactivate_user(message.from_user.id)

    await message.answer(
        "دریافت پیام‌ها لغو شد 🔕\n"
        "هر زمان خواستی دوباره عضو شو 🌹",
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "ℹ️ راهنما")
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ <b>راهنمای بات</b>\n\n"
        "💌 پیام امروز: نمایش پیام عاشقانه امروز\n"
        "❤️ عضویت در پیام‌ها: فعال‌سازی پیام‌های روزانه\n"
        "🔕 لغو دریافت پیام‌ها: توقف پیام‌های روزانه\n\n"
        "⏰ زمان ارسال روزانه: ساعت ۹ صبح به وقت تهران",
        reply_markup=main_keyboard()
    )


# -----------------------------
# دکمه‌های شیشه‌ای
# -----------------------------

@dp.callback_query(F.data == "subscribe")
async def subscribe_callback(callback: CallbackQuery):
    add_user(
        user_id=callback.from_user.id,
        first_name=callback.from_user.first_name or "دوست عزیز"
    )

    await callback.answer("عضویت با موفقیت انجام شد ❤️")

    await callback.message.answer(
        "از این به بعد هر روز یک پیام عاشقانه برایت می‌فرستم 💌",
        reply_markup=main_keyboard()
    )


@dp.callback_query(F.data == "unsubscribe")
async def unsubscribe_callback(callback: CallbackQuery):
    deactivate_user(callback.from_user.id)

    await callback.answer("دریافت پیام‌ها متوقف شد 🔕")

    await callback.message.answer(
        "دریافت پیام‌های روزانه لغو شد 🔕",
        reply_markup=main_keyboard()
    )


# -----------------------------
# ارسال پیام روزانه
# -----------------------------

async def send_daily_messages():
    today = datetime.now(TIMEZONE).date().isoformat()
    text = format_love_message()

    users = get_active_users()

    for user_id in users:
        if message_was_sent(user_id, today):
            continue

        try:
            await bot.send_message(
                chat_id=user_id,
                text=text
            )

            save_sent_message(user_id, today)

            # فاصله کوتاه برای جلوگیری از فشار زیاد روی API تلگرام
            await asyncio.sleep(0.05)

        except Exception as error:
            logging.warning(
                f"ارسال پیام به کاربر {user_id} ناموفق بود: {error}"
            )


async def daily_scheduler():
    while True:
        now = datetime.now(TIMEZONE)

        next_send = now.replace(
            hour=SEND_HOUR,
            minute=SEND_MINUTE,
            second=0,
            microsecond=0
        )

        if next_send <= now:
            next_send += timedelta(days=1)

        seconds_until_send = (next_send - now).total_seconds()

        logging.info(
            f"پیام بعدی در {next_send.strftime('%Y-%m-%d %H:%M')} ارسال می‌شود."
        )

        await asyncio.sleep(seconds_until_send)
        await send_daily_messages()


# -----------------------------
# اجرای برنامه
# -----------------------------

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    init_database()

    await bot.delete_webhook(drop_pending_updates=True)

    scheduler_task = asyncio.create_task(
        daily_scheduler()
    )

    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("بات متوقف شد.")
