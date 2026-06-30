#!/usr/bin/env python3
"""
Telegram Bot - បោះមេរៀន 30 រៀងរាល់ព្រឹក 07:00
មាន Command /send និង Web Control Panel នៅ /admin
"""

import asyncio
import logging
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import threading
import time

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import schedule

from lessons_data import LESSONS, TOTAL_LESSONS

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
TOPIC_ID = os.getenv('TOPIC_ID')
SEND_TIME = os.getenv('SEND_TIME', '07:00')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
# Secret key for web access (change to something strong)
WEB_SECRET = os.getenv('WEB_SECRET', 'change_me_123')

PORT = int(os.environ.get('PORT', 10000))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ------- Web Server with Control Panel -------
class WebHandler(BaseHTTPRequestHandler):
    # Simple HTML template
    def _serve_html(self, message=""):
        html = f"""
        <!DOCTYPE html>
        <html lang="km">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📚 Trading Bot Control</title>
            <style>
                body {{ font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                h1 {{ color: #333; }}
                .status {{ background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                button {{ background: #1976d2; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; }}
                button:hover {{ background: #1565c0; }}
                .msg {{ margin-top: 20px; color: green; font-weight: bold; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>🤖 Telegram Bot Control</h1>
            <div class="status">
                <p>✅ Bot កំពុងដំណើរការ</p>
                <p>📅 កាលវិភាគផ្ញើប្រចាំថ្ងៃ: {SEND_TIME}</p>
            </div>
            <form method="POST" action="/trigger">
                <input type="hidden" name="secret" value="{WEB_SECRET}">
                <button type="submit">📨 បោះមេរៀនទាំង 30 ឥឡូវនេះ</button>
            </form>
            {message}
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/admin":
            self._serve_html()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/trigger":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            secret = params.get('secret', [''])[0]

            if secret != WEB_SECRET:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return

            # Trigger sending in a separate thread to avoid blocking
            threading.Thread(target=self._trigger_send).start()
            self._serve_html('<div class="msg">🚀 កំពុងបោះមេរៀនទាំង 30... សូមពិនិត្យ Telegram Group</div>')
        else:
            self.send_response(404)
            self.end_headers()

    def _trigger_send(self):
        """Run the async send function using a new event loop in this thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot = Bot(token=BOT_TOKEN)
            loop.run_until_complete(scheduled_send_all(bot))
            logger.info("Web trigger: បញ្ចប់ការបោះមេរៀន")
        except Exception as e:
            logger.error(f"Web trigger error: {e}")
        finally:
            loop.close()

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), WebHandler)
    logger.info(f"🌐 Web panel available at http://your-render-url.onrender.com/admin")
    server.serve_forever()

# ------- Telegram Command /send -------
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ------- Scheduled Task -------
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

    # Start web server with control panel
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Telegram bot
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("send", send_command))
    await application.initialize()
    await application.start()
    logger.info("🤖 Bot បានចាប់ផ្ដើម ហើយកំពុងស្ដាប់ /send")

    bot = Bot(token=BOT_TOKEN)
    schedule_thread = threading.Thread(target=run_schedule, args=(bot,), daemon=True)
    schedule_thread.start()

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