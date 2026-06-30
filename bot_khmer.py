#!/usr/bin/env python3
"""
Telegram Bot - បោះមេរៀន 30 រៀងរាល់ព្រឹក 07:00 និងមាន Command /send
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import schedule
import time
import threading

from lessons_data import LESSONS, TOTAL_LESSONS

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
TOPIC_ID = os.getenv('TOPIC_ID')
SEND_TIME = os.getenv('SEND_TIME', '07:00')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')  # លេខ User ID របស់អ្នក

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ------- មុខងារ Command /send -------
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ពេល Admin ផ្ញើ /send, បោះមេរៀនទាំង 30 ភ្លាមៗ"""
    user_id = update.effective_user.id
    if ADMIN_USER_ID and str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("⛔ អ្នកមិនមានសិទ្ធិប្រើពាក្យបញ្ជានេះទេ។")
        return

    await update.message.reply_text("🚀 កំពុងចាប់ផ្ដើមបោះមេរៀនទាំង 30...")
    for lesson in LESSONS:
        try:
            header = f"📚 <b>មេរៀន Trading</b>\n"
            header += f"📂 ប្រភេទ: <b>{lesson['category']}</b>\n"
            header += f"📝 មេរៀនទី {lesson['id']}/{TOTAL_LESSONS}\n"
            header += "━" * 35 + "\n\n"
            message = header + lesson['content']

            kwargs = {
                'chat_id': GROUP_CHAT_ID,
                'text': message,
                'parse_mode': ParseMode.HTML
            }
            if TOPIC_ID:
                kwargs['message_thread_id'] = int(TOPIC_ID)

            await context.bot.send_message(**kwargs)
            logger.info(f"✅ បានបញ្ជូនមេរៀនទី {lesson['id']}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"❌ កំហុសមេរៀនទី {lesson['id']}: {e}")
    await update.message.reply_text("🏁 បញ្ចប់ការបោះមេរៀនទាំង 30")

# ------- មុខងារ Scheduled Task -------
async def scheduled_send_all(bot: Bot):
    logger.info("🚀 កាលវិភាគ៖ បោះមេរៀនទាំង 30")
    for lesson in LESSONS:
        try:
            header = f"📚 <b>មេរៀន Trading</b>\n"
            header += f"📂 ប្រភេទ: <b>{lesson['category']}</b>\n"
            header += f"📝 មេរៀនទី {lesson['id']}/{TOTAL_LESSONS}\n"
            header += "━" * 35 + "\n\n"
            message = header + lesson['content']

            kwargs = {
                'chat_id': GROUP_CHAT_ID,
                'text': message,
                'parse_mode': ParseMode.HTML
            }
            if TOPIC_ID:
                kwargs['message_thread_id'] = int(TOPIC_ID)

            await bot.send_message(**kwargs)
            logger.info(f"✅ បានបញ្ជូនមេរៀនទី {lesson['id']}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"❌ កំហុសមេរៀនទី {lesson['id']}: {e}")
    logger.info("🏁 កាលវិភាគបញ្ចប់")

def run_schedule(bot: Bot):
    schedule.every().day.at(SEND_TIME).do(
        lambda: asyncio.run(scheduled_send_all(bot))
    )
    logger.info(f"⏰ កាលវិភាគត្រូវបានកំណត់នៅម៉ោង {SEND_TIME}")
    while True:
        schedule.run_pending()
        time.sleep(30)

async def main():
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        logger.error("❌ BOT_TOKEN ឬ GROUP_CHAT_ID មិនបានកំណត់!")
        return

    # កម្មវិធី Telegram Bot (ស្ដាប់ Command)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("send", send_command))
    await application.initialize()
    await application.start()
    logger.info("🤖 Bot បានចាប់ផ្ដើម ហើយកំពុងស្ដាប់ /send")

    # បង្កើត Bot instance សម្រាប់កាលវិភាគ
    bot = Bot(token=BOT_TOKEN)

    # ចាប់ផ្ដើមកាលវិភាគក្នុង Thread ដាច់ដោយឡែក
    schedule_thread = threading.Thread(target=run_schedule, args=(bot,), daemon=True)
    schedule_thread.start()

    # រង់ចាំសញ្ញាបិទ (Ctrl+C)
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await application.stop()
        logger.info("Bot បានបញ្ឈប់")

if __name__ == "__main__":
    asyncio.run(main())