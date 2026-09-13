# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

# تلاش برای بارگذاری متغیرهای محیطی (برای اجرا در لوکال)، در Railway نیازی نیست
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# تلاش برای دریافت منطقه زمانی
try:
    from zoneinfo import ZoneInfo
    ZoneInfo = ZoneInfo
except ImportError:
    ZoneInfo = None

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# تنظیمات لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# خواندن متغیرهای محیطی
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID_RAW = os.environ.get("CHAT_ID", "").strip()
TIMEZONE_NAME = os.environ.get("TIMEZONE", "Asia/Tehran")
SEND_TIME = os.environ.get("SEND_TIME", "08:00")

# --- توابع کمکی ---

def get_tz():
    """دریافت آبجکت منطقه زمانی، با فیلد به UTC اگر غیرمعتبر باشد"""
    if ZoneInfo:
        try:
            return ZoneInfo(TIMEZONE_NAME)
        except Exception:
            logger.warning(f"Invalid TIMEZONE {TIMEZONE_NAME}, fallback to UTC.")
            return timezone.utc
    else:
        logger.warning("zoneinfo module not found, using UTC.")
        return timezone.utc

def parse_time(time_str):
    """تبدیل رشته HH:MM به ساعت و دقیقه"""
    try:
        h, m = map(int, time_str.split(":"))
        if 0 <= h < 24 and 0 <= m < 60:
            return h, m
        raise ValueError
    except Exception:
        logger.warning("Invalid SEND_TIME format. Using 08:00")
        return 8, 0

def parse_chat_id(chat_id_str):
    """تبدیل چت آی‌دی به نوع مناسب (Int یا String)"""
    if not chat_id_str:
        return None
    if chat_id_str.lstrip("-").isdigit():
        return int(chat_id_str)
    return chat_id_str

# تبدیل متغیرهای خام به مقادیر قابل استفاده
TZ = get_tz()
SEND_HOUR, SEND_MINUTE = parse_time(SEND_TIME)
CHAT_ID = parse_chat_id(CHAT_ID_RAW)

# --- لیست پیام‌ها ---
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

def get_daily_message(index=None):
    """انتخاب پیام روزانه"""
    import random
    if index is not None:
        return MESSAGES[index % len(MESSAGES)]
    return random.choice(MESSAGES)

# --- هندلرهای تلگرام ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "سلام! 🌼 ربات صبح‌بخیر عشق فعال است.\n\n"
        "برای تست یا گرفتن شناسه چت برای تنظیمات Railway، دستور /id را بفرست."
    )
    await update.message.reply_text(msg)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"شناسه چت شما:\n{chat_id}\n\n"
        "این عدد را در Railway متغیر CHAT_ID قرار دهید."
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """یک پیام آزمایشی ارسال می‌کند"""
    if CHAT_ID:
        try:
            text = get_daily_message()
            await context.bot.send_message(chat_id=CHAT_ID, text=text)
            await update.message.reply_text("پیام تستی ارسال شد ✅")
        except Exception as e:
            await update.message.reply_text(f"خطا در ارسال: {e}")
    else:
        await update.message.reply_text("CHAT_ID تنظیم نشده است!")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}")

# --- سیستم زمان‌بندی دستی (بدون JobQueue) ---

async def daily_sender_loop(application):
    """
    این تابع در پس‌زمینه اجرا می‌شود و بررسی می‌کند که 
    آیا ساعت مقرر رسیده است یا خیر.
    """
    if not CHAT_ID:
        logger.warning("CHAT_ID is not set. Daily sender thread stopped or idle.")
        while True:
            await asyncio.sleep(60)
        return

    last_sent_date = None
    logger.info(f"Daily sender started. Target time: {SEND_HOUR}:{SEND_MINUTE:02d} {TIMEZONE_NAME}")

    while True:
        try:
            now = datetime.now(TZ)
            today_str = now.date().isoformat()
            current_date_obj = now
            
            # شرایط ارسال:
            # ۱. ساعت فعلی >= ساعت مقرر
            # ۲. امروز هنوز پیامی ارسال نشده است
            
            if now.hour >= SEND_HOUR and now.minute >= SEND_MINUTE or (now.hour > SEND_HOUR):
                # اگر دقیقه کوچکتر است ولی ساعت بزرگتر، باز هم باید برود (شرط بالا کمی ساده است، بهتر است دقیق چک کنیم)
                pass
            
            # منطق دقیق‌تر:
            is_time_to_send = False
            if now.hour > SEND_HOUR:
                is_time_to_send = True
            elif now.hour == SEND_HOUR and now.minute >= SEND_MINUTE:
                is_time_to_send = True

            if is_time_to_send and last_sent_date != today_str:
                try:
                    # اگر دقیقاً روی دقیقه تنظیم شده باشد، ممکن است چند بار در همان دقیقه فراخوانی نشود،
                    # ولی چون last_sent_date آپدیت می‌شود، فقط یک بار در روز ارسال می‌گردد.
                    
                    text = get_daily_message()
                    await application.bot.send_message(
                        chat_id=CHAT_ID,
                        text=text
                    )
                    logger.info(f"Message sent at {now.strftime('%H:%M')}")
                    last_sent_date = today_str
                    # برای اطمینان که در همان دقیقه دوباره چک نشود، کمی صبر می‌کنیم
                    await asyncio.sleep(61)
                    continue
                    
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    last_sent_date = None # تلاش مجدد در دور بعد
                    await asyncio.sleep(60)
            else:
                # اگر زمان نزدیک است، هر دقیقه چک کن، اگر دور است، هر ۱۰ دقیقه چک کن
                time_until_next_trigger = None
                if now.hour < SEND_HOUR or (now.hour == SEND_HOUR and now.minute < SEND_MINUTE):
                    time_until_send = timedelta(hours=SEND_HOUR - now.hour, minutes=SEND_MINUTE - now.minute)
                    time_until_next_trigger = time_until_send.total_seconds()
                
                sleep_time = 60 if (time_until_next_trigger and time_until_next_trigger < 60*60*2) else 60*10
                await asyncio.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Error in daily sender loop: {e}")
            await asyncio.sleep(10)

def main():
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN environment variable is required!")
        sys.exit(1)
    
    logger.info("Starting Telegram Bot...")
    
    # ساخت اپلیکیشن بدون فعال‌سازی JobQueue
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_error_handler(error_handler)
    
    # اجرای حلقه زمان‌بندی در یک تسک جداگانه
    async def start_background_tasks(app):
        # ایجاد تسک برای فرستنده پیام
        app.bot_data['daily_sender'] = asyncio.create_task(daily_sender_loop(app))
        logger.info("Background daily sender task created.")

    # استفاده از post_init برای شروع تسک‌ها قبل از شروع polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        post_init=start_background_tasks
    )

if __name__ == "__main__":
    # برای اطمینان از پایداری در برخی محیط‌ها
    try:
        main()
    except Exception as e:
        logger.error(e)
