import os
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncpg
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest


# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Tehran")
TIMEZONE = ZoneInfo(TIMEZONE_NAME)

SEND_HOUR = int(os.getenv("SEND_HOUR", "9"))
SEND_MINUTE = int(os.getenv("SEND_MINUTE", "0"))

PORT = int(os.getenv("PORT", "8080"))

if not BOT_TOKEN:
    raise ValueError("متغیر BOT_TOKEN در Railway تنظیم نشده است.")

if not DATABASE_URL:
    raise ValueError("متغیر DATABASE_URL در Railway تنظیم نشده است.")


# =========================================================
# پیام‌های عاشقانه
# =========================================================

LOVE_MESSAGES = [
    "تو قشنگ‌ترین اتفاقی هستی که زندگی به من هدیه داده است 🤍",
    "کنار تو حتی سکوت هم شبیه یک شعر عاشقانه است 🎶❤️",
    "هر صبح که بیدار می‌شوم، از اینکه تو را در زندگی‌ام دارم لبخند می‌زنم ☀️😊",
    "دوست داشتنت برای من انتخاب نیست؛ زیباترین بخش وجود من است 💖",
    "تو دلیل خیلی از لبخندهای بی‌دلیل من هستی 🌸",
    "با تو ساده‌ترین لحظه‌ها هم تبدیل به خاطره‌ای ماندگار می‌شوند ✨",
    "در میان تمام آدم‌های دنیا، قلب من فقط تو را بلد است 💌",
    "هر بار که به تو فکر می‌کنم، دنیا کمی زیباتر می‌شود 🌍💞",
    "تو همان آرامشی هستی که همیشه دنبالش می‌گشتم 🕊️",
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


# =========================================================
# دیتابیس
# =========================================================

pool: asyncpg.Pool | None = None


async def init_database():
    global pool

    database_url = DATABASE_URL.replace(
        "postgres://",
        "postgresql://"
    )

    pool = await asyncpg.create_pool(
        dsn=database_url,
        min_size=1,
        max_size=5
    )

    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await connection.execute("""
            CREATE TABLE IF NOT EXISTS sent_messages (
                user_id BIGINT,
                message_date DATE,
                PRIMARY KEY (user_id, message_date)
            );
        """)


async def add_user(user_id: int, first_name: str):
    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO users (user_id, first_name, is_active)
            VALUES ($1, $2, TRUE)
            ON CONFLICT (user_id)
            DO UPDATE SET
                first_name = EXCLUDED.first_name,
                is_active = TRUE;
        """, user_id, first_name)


async def deactivate_user(user_id: int):
    async with pool.acquire() as connection:
        await connection.execute("""
            UPDATE users
            SET is_active = FALSE
            WHERE user_id = $1;
        """, user_id)


async def get_active_users():
    async with pool.acquire() as connection:
        rows = await connection.fetch("""
            SELECT user_id
            FROM users
            WHERE is_active = TRUE;
        """)

        return [row["user_id"] for row in rows]


async def was_message_sent(user_id: int, message_date):
    async with pool.acquire() as connection:
        result = await connection.fetchval("""
            SELECT EXISTS(
                SELECT 1
                FROM sent_messages
                WHERE user_id = $1
                AND message_date = $2
            );
        """, user_id, message_date)

        return result


async def save_sent_message(user_id: int, message_date):
    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO sent_messages (user_id, message_date)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING;
        """, user_id, message_date)


# =========================================================
# ظاهر بات
# =========================================================

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💌 پیام امروز"),
                KeyboardButton(text="❤️ عضویت"),
            ],
            [
                KeyboardButton(text="🔕 لغو عضویت"),
                KeyboardButton(text="ℹ️ راهنما"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❤️ فعال‌سازی پیام روزانه",
                    callback_data="subscribe"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔕 لغو دریافت پیام",
                    callback_data="unsubscribe"
                )
            ]
        ]
    )


def get_today_message():
    today = datetime.now(TIMEZONE).date()
    message_index = today.toordinal() % len(LOVE_MESSAGES)
    return LOVE_MESSAGES[message_index]


def formatted_message():
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y/%m/%d")

    return (
        "💌 <b>پیام عاشقانه امروز</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"✨ {get_today_message()}\n\n"
        "━━━━━━━━━━━━━━\n"
        "🌹 <i>هر روز، یک پیام برای لبخند تو</i>\n"
        f"📅 {today}"
    )


# =========================================================
# ساخت بات
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================================================
# دستورات و پیام‌های کاربران
# =========================================================

@dp.message(CommandStart())
async def start_handler(message: Message):
    await add_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name or "دوست عزیز"
    )

    await message.answer(
        f"سلام {message.from_user.first_name or 'عزیزم'} 🌹\n\n"
        "به بات پیام‌های عاشقانه خوش آمدی 💌\n\n"
        "از این به بعد هر روز یک پیام زیبا و عاشقانه برایت می‌فرستم ❤️",
        reply_markup=main_keyboard()
    )

    await message.answer(
        "مدیریت دریافت پیام‌ها:",
        reply_markup=inline_keyboard()
    )


@dp.message(Command("now"))
async def now_handler(message: Message):
    await message.answer(
        formatted_message(),
        reply_markup=main_keyboard()
    )


@dp.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    await add_user(
        message.from_user.id,
        message.from_user.first_name or "دوست عزیز"
    )

    await message.answer(
        "عضویتت با موفقیت فعال شد ❤️\n"
        f"هر روز ساعت {SEND_HOUR:02d}:{SEND_MINUTE:02d} پیام دریافت می‌کنی 💌",
        reply_markup=main_keyboard()
    )


@dp.message(Command("unsubscribe"))
async def unsubscribe_handler(message: Message):
    await deactivate_user(message.from_user.id)

    await message.answer(
        "دریافت پیام‌های روزانه متوقف شد 🔕",
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "💌 پیام امروز")
async def today_handler(message: Message):
    await message.answer(
        formatted_message(),
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "❤️ عضویت")
async def subscribe_button_handler(message: Message):
    await add_user(
        message.from_user.id,
        message.from_user.first_name or "دوست عزیز"
    )

    await message.answer(
        "عالیه! دریافت پیام‌های عاشقانه برایت فعال شد 💖",
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "🔕 لغو عضویت")
async def unsubscribe_button_handler(message: Message):
    await deactivate_user(message.from_user.id)

    await message.answer(
        "دریافت پیام‌های روزانه لغو شد 🔕",
        reply_markup=main_keyboard()
    )


@dp.message(F.text == "ℹ️ راهنما")
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ <b>راهنمای بات</b>\n\n"
        "💌 پیام امروز: نمایش پیام عاشقانه امروز\n"
        "❤️ عضویت: فعال‌سازی پیام‌های روزانه\n"
        "🔕 لغو عضویت: توقف پیام‌ها\n"
        "/now - نمایش پیام امروز\n"
        "/subscribe - فعال‌سازی عضویت\n"
        "/unsubscribe - لغو عضویت\n\n"
        f"⏰ زمان ارسال: ساعت {SEND_HOUR:02d}:{SEND_MINUTE:02d} "
        f"به وقت {TIMEZONE_NAME}",
        reply_markup=main_keyboard()
    )


# =========================================================
# دکمه‌های شیشه‌ای
# =========================================================

@dp.callback_query(F.data == "subscribe")
async def subscribe_callback(callback: CallbackQuery):
    await add_user(
        callback.from_user.id,
        callback.from_user.first_name or "دوست عزیز"
    )

    await callback.answer("عضویت فعال شد ❤️")

    await callback.message.answer(
        "دریافت پیام‌های عاشقانه برایت فعال شد 💌",
        reply_markup=main_keyboard()
    )


@dp.callback_query(F.data == "unsubscribe")
async def unsubscribe_callback(callback: CallbackQuery):
    await deactivate_user(callback.from_user.id)

    await callback.answer("عضویت لغو شد 🔕")

    await callback.message.answer(
        "دریافت پیام‌های روزانه متوقف شد 🔕",
        reply_markup=main_keyboard()
    )


# =========================================================
# ارسال پیام روزانه
# =========================================================

async def send_daily_messages():
    today = datetime.now(TIMEZONE).date()
    message_text = formatted_message()

    users = await get_active_users()

    logging.info(
        "شروع ارسال پیام روزانه برای %s کاربر",
        len(users)
    )

    for user_id in users:
        if await was_message_sent(user_id, today):
            continue

        try:
            await bot.send_message(
                chat_id=user_id,
                text=message_text
            )

            await save_sent_message(user_id, today)

            # رعایت محدودیت‌های تلگرام
            await asyncio.sleep(0.05)

        except TelegramForbiddenError:
            # کاربر بات را بلاک کرده است
            await deactivate_user(user_id)

        except TelegramBadRequest as error:
            logging.warning(
                "خطای تلگرام برای کاربر %s: %s",
                user_id,
                error
            )

        except Exception as error:
            logging.exception(
                "خطای ناشناخته برای کاربر %s: %s",
                user_id,
                error
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

        wait_seconds = (next_send - now).total_seconds()

        logging.info(
            "ارسال بعدی: %s",
            next_send.strftime("%Y-%m-%d %H:%M:%S")
        )

        await asyncio.sleep(wait_seconds)

        try:
            await send_daily_messages()
        except Exception:
            logging.exception("خطا در زمان‌بندی ارسال روزانه")


# =========================================================
# Health Check برای Railway
# =========================================================

async def health_check(request):
    return web.Response(
        text="Love Telegram Bot is running ✅",
        status=200
    )


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT
    )

    await site.start()

    logging.info("Health server started on port %s", PORT)


# =========================================================
# اجرای اصلی
# =========================================================

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    await init_database()
    await start_health_server()

    # حذف webhook قبلی برای اجرای polling
    await bot.delete_webhook(drop_pending_updates=True)

    scheduler_task = asyncio.create_task(
        daily_scheduler()
    )

    logging.info("Bot started successfully.")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()

        if pool:
            await pool.close()

        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
