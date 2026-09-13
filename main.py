# -*- coding: utf-8 -*-
import logging
import os
import sys
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID_RAW = os.environ.get("CHAT_ID", "").strip()
TIMEZONE_NAME = os.environ.get("TIMEZONE", "Asia/Tehran")
SEND_TIME = os.environ.get("SEND_TIME", "08:00")

try:
    TZ = ZoneInfo(TIMEZONE_NAME)
except Exception:
    logger.warning(f"Invalid TIMEZONE: {TIMEZONE_NAME}. Falling back to UTC.")
    TZ = timezone.utc

def parse_time(send_time: str) -> tuple[int, int]:
    try:
        h_str, m_str = send_time.split(":")
        hour = int(h_str)
        minute = int(m_str)

        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError

        return hour, minute
    except Exception:
        logger.warning("Invalid SEND_TIME format. Expected HH:MM. Using 08:00.")
        return 8, 0

def parse_chat_id(chat_id_raw: str):
    if not chat_id_raw:
        return None

    # If numeric, convert to int. If @username, keep as string.
    if chat_id_raw.lstrip("-").isdigit():
        return int(chat_id_raw)

    return chat_id_raw

HOUR, MINUTE = parse_time(SEND_TIME)
CHAT_ID = parse_chat_id(CHAT_ID_RAW)
DAILY_TIME = dtime(hour=HOUR, minute=MINUTE, tzinfo=TZ)

MESSAGES = [
    "صبح بخیر عزیزم! امیدوارم امروزت با آرامش، لبخند و نورِ خوب شروع بشه. ☀️🌸",
    "سلام به قشنگ‌ترین انرژیِ زندگی! امروز یه فرصت تازه‌ست؛ با خودت مهربون و پر‌امید باش. 🌼",
    "صبح بخیر! یادت نره چقدر ارزشمندی؛ حتی اگه امروز همه‌چیز عالی نباشه، من بهت ایمان دارم. 💖",
    "سلام! امیدوارم امروزت مثل چشمات روشن و مثل قلبت گرم باشه. ☕✨",
    "صبح بخیر عزیزم! هر نفس، یه شروع دوباره‌ست؛ امروز فقط یه قدم کوچک برای خودت بردار. 🌱",
    "سلام به مهربون‌ترین دوستِ دنیا! امروزت پر از اتفاق‌های کوچیک و قشنگی باشه که لبخندت کنه. 😊",
    "صبح بخیر! بذار امروز، یه روزِ امید و شوق باشه؛ تو لایق بهترین‌هایی. 🕊️",
    "سلام عزیزم! اگر یه روز سخت داری، یادت باشه آفتاب بعد از شب میاد؛ امروزت آروم باشه. 🌅",
    "صبح بخیر! لبخندت رو دریغ نکن؛ تو به این دنیا و آدم‌های اطرافت نور می‌دی. 🌟",
    "سلام! امروز یه صفحه‌ی تازه‌ست؛ با قدرت، مهربونی و امید شروعش کن. 🔥",
    "صبح بخیر عزیزم! امیدوارم امروزت آن‌قدر خوب باشه که شب با آرامش بخوابی. 🌙",
    "سلام به دلِ گرمِ من! هر روز یه دلیل جدید برای شکرگزاری و امید می‌آره؛ امروز تو هم دلیلش باش. ❤️",
    "صبح بخیر! یادت باشه ارزش تو ثابت نیست؛ تو با هر تلاش، قشنگ‌تر و قوی‌تر می‌شی. 💪",
    "سلام! امیدوارم امروز، قلبت رو به خوبی‌ها باز کنی و همه‌چیز جاش درست بشه. 🌈",
    "صبح بخیر عزیزم! آرزوم برای امروزت: آرامش، سلامتی، شادی و یه اتفاق خوبِ کوچک. 🍃",
    "سلام به مهربون‌ترین! امروزت پر از انگیزه و پر از عشقِ خودت باشه؛ تو واقعاً خاصه. ✨",
    "صبح بخیر! حتی اگه روزهای قبل سخت بوده، امروز می‌تونی دوباره قوی باشی. بهت ایمان دارم. 🦋",
    "سلام! امیدوارم امروزت پر از نور، امید و لبخندهای واقعی باشه؛ نه فقط ظاهرِ خنده. 😊",
    "صبح بخیر عزیزم! یه نفس عمیق بکش و آروم شروع کن؛ من اینجام و برات انرژی می‌فرستم. 🤍",
    "سلام به قلبِ بزرگ! امروزت پر‌برکت، پر از مهربونی و پر از امید به آینده باشه. 🌇",
    "صبح بخیر! تو لایق یه روز آروم و زیبا هستی؛ امروز فقط برای خودت تلاش کن. 🎯",
    "سلام عزیزم! امروزت می‌تونه اون روزی باشه که بهش فکر می‌کنی؛ با امید، اول صبح. 🌻",
    "صبح بخیر! امیدوارم امروزت پر از حسِ خوبِ «امکان» باشه؛ همه‌چیز ممکنه، از همین صبح. 🔑",
    "سلام! یادت نره چقدر دوست‌داشتنی و قوی هستی؛ امروز هم برای خودت می‌درخشی. 🌞",
    "صبح بخیر عزیزم! اگر خسته‌ای، مهربون باش با خودت؛ استراحت هم یه نوع پیشرفت باشه. ☕",
    "سلام به انرژیِ مثبت! امروزت پر از موفقیت‌های کوچیک و لبخندهای بزرگ باشه. 👣",
    "صبح بخیر! هر لحظه‌ی امروزت رو مثل یه هدیه ببین و با عشق زندگی کن. 🎁",
    "سلام عزیزم! امیدوارم امروزت به‌قدری خوب باشه که یادآوری کنه چرا باید امیدوار بود. 🌷",
    "صبح بخیر! تو نه‌فقط ارزشمندی، بلکه می‌تونی امروز یه روزِ خوب برای خودت بسازی. 🛠️",
    "سلام! قلبت رو پر از امید کن؛ حتی اگه یه روز آروم و ساده هم باشه. 🕯️",
    "صبح بخیر عزیزم! آرزوم برای امروزت: آرامشِ عمیق، شادیِ واقعی و آینده‌ای روشن‌تر. 🌠",
]

def get_daily_message() -> str:
    """
    یک پیام روزانه انتخاب می‌کند.
    با date.toordinal() اگر ربات ری‌استارت شود هم همان روز همان پیام انتخاب می‌شود.
    """
    today = datetime.now(TZ).date()
    index = today.toordinal() % len(MESSAGES)
    return MESSAGES[index]

async def send_good_morning(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not CHAT_ID:
        logger.warning("CHAT_ID is not set. Scheduled job did nothing.")
        return

    text = get_daily_message()

    try:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=text,
        )
        logger.info(f"Good morning message sent to chat_id={CHAT_ID}")
    except Exception as exc:
        logger.error(f"Failed to send message: {exc}", exc_info=True)

async def post_init(application: Application) -> None:
    if CHAT_ID is None:
        logger.warning(
            "CHAT_ID not found. Ask your friend to send /start then /id to the bot, "
            "then put that ID in Railway environment variable CHAT_ID."
        )

    if application.job_queue is None:
        logger.warning(
            "JobQueue is not enabled. Add dependency: python-telegram-bot[job-queue]"
        )
        return

    application.job_queue.run_daily(
        callback=send_good_morning,
        time=DAILY_TIME,
        days=(0, 1, 2, 3, 4, 5, 6),
        name="daily-good-morning",
        replace_existing=True,
    )

    logger.info(
        f"Daily message scheduled at {SEND_TIME} ({TIMEZONE_NAME})."
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "سلام! 🌼 ربات پیام صبح‌بخیر عاشقانه و امیدوارکننده فعاله.\n\n"
        "برای دیدن شناسه چت خودت، /id بفرست."
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"شناسه چت شما این است:\n\n{chat_id}\n\n"
        "این عدد را در Railway داخل متغیر CHAT_ID بگذار."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Unhandled exception caused by update {update}", exc_info=context.error)

def main():
    if not BOT_TOKEN:
        logging.critical("The BOT_TOKEN environment variable is required.")
        sys.exit(1)

    # در نسخه ۲۱.۴ این متد وجود دارد، اگر نبود کد زیر حذف می‌کند
    try:
        builder = Application.builder().token(BOT_TOKEN)
        if hasattr(builder, "job_queue_enabled"):
            builder.job_queue_enabled(True)
    except Exception:
        builder = Application.builder().token(BOT_TOKEN)

    application = builder.build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_error_handler(error_handler)

    # برای استفاده از JobQueue اگر فعال بود
    if application.job_queue is not None:
        logging.info("JobQueue active, waiting for scheduled time.")
    else:
        logging.info("JobQueue disabled in builder, continuing normally.")

    application.run_polling()

if __name__ == "__main__":
    main()
