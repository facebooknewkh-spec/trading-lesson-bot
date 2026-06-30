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
WEB_SECRET = os.getenv('WEB_SECRET', 'change_me_123')

# Profile settings (editable via web)
ADMIN_NAME = os.getenv('ADMIN_NAME', 'CHEATZ')
ADMIN_AVATAR_URL = os.getenv('ADMIN_AVATAR_URL', 'https://i.imgur.com/HeGEEbu.png')
LESSONS_SENT_TODAY = 0
TOTAL_SENT_ALL_TIME = 0

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

# ------- Web Server with Trading Dashboard + PWA -------
class WebHandler(BaseHTTPRequestHandler):
    admin_name = ADMIN_NAME
    admin_avatar = ADMIN_AVATAR_URL
    lessons_today = LESSONS_SENT_TODAY
    total_sent = TOTAL_SENT_ALL_TIME

    def _render_dashboard(self, message=""):
        html = f"""<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- PWA Meta Tags -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Trading Bot">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="{WebHandler.admin_avatar}">
    <title>📊 Trading Bot Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0b0f1c;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
            background-image: radial-gradient(circle at 30% 40%, #1a2b4c 0%, #0b0f1c 60%);
            -webkit-tap-highlight-color: transparent;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            animation: fadeIn 0.5s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(20, 30, 48, 0.9);
            padding: 15px 25px;
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(0, 200, 255, 0.1);
            backdrop-filter: blur(5px);
        }}
        .logo {{
            font-size: 1.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .status-badge {{
            background: #00c853;
            color: #000;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(0,200,83,0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(0,200,83,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(0,200,83,0); }}
        }}
        .profile-card {{
            background: rgba(25, 35, 55, 0.8);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(8px);
            transition: transform 0.2s;
        }}
        .profile-card:hover {{ transform: translateY(-2px); }}
        .avatar {{
            width: 90px;
            height: 90px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #00d2ff;
            box-shadow: 0 0 15px #00d2ff88;
        }}
        .profile-info h2 {{
            font-size: 1.8rem;
            color: #fff;
            margin-bottom: 5px;
        }}
        .profile-info .title {{
            color: #00d2ff;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.9rem;
        }}
        .edit-profile {{
            margin-top: 10px;
            display: inline-flex;
            gap: 10px;
        }}
        .btn-edit {{
            background: transparent;
            border: 1px solid #00d2ff;
            color: #00d2ff;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .btn-edit:hover {{
            background: #00d2ff22;
            box-shadow: 0 0 12px #00d2ff66;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }}
        .stat-box {{
            background: rgba(20, 30, 48, 0.9);
            padding: 20px;
            border-radius: 14px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(5px);
        }}
        .stat-value {{
            font-size: 2.2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .stat-label {{
            color: #aaa;
            margin-top: 5px;
            font-size: 0.9rem;
        }}
        .chart-container {{
            background: rgba(20, 30, 48, 0.9);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
        }}
        .chart-title {{
            font-weight: bold;
            margin-bottom: 15px;
            color: #ccc;
        }}
        .chart {{
            height: 80px;
            position: relative;
        }}
        .chart-line {{
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, #00d2ff, #00c853, #ffeb3b, #ff5252);
            animation: chartMove 3s infinite alternate ease-in-out;
        }}
        @keyframes chartMove {{
            0% {{ transform: scaleY(0.5); }}
            100% {{ transform: scaleY(1.5); }}
        }}
        .candles {{
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            height: 100%;
            margin-top: 10px;
        }}
        .candle {{
            width: 8px;
            background: #00c853;
            animation: candleFlicker 2s infinite alternate;
        }}
        @keyframes candleFlicker {{
            0% {{ height: 30%; }}
            100% {{ height: 80%; }}
        }}
        .trigger-section {{
            text-align: center;
            margin-bottom: 25px;
        }}
        .btn-trigger {{
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            color: white;
            border: none;
            padding: 14px 30px;
            font-size: 1.1rem;
            border-radius: 30px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
            letter-spacing: 0.5px;
        }}
        .btn-trigger:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 210, 255, 0.5);
        }}
        .message {{
            background: #00c85322;
            border: 1px solid #00c853;
            color: #00c853;
            padding: 12px;
            border-radius: 10px;
            margin-top: 15px;
            text-align: center;
            animation: fadeIn 0.5s;
        }}
        .edit-form {{
            background: rgba(20, 30, 48, 0.95);
            border: 1px solid #00d2ff44;
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
            animation: fadeIn 0.3s;
        }}
        .edit-form input {{
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            border-radius: 8px;
            border: 1px solid #3a7bd5;
            background: #0b0f1c;
            color: #fff;
            outline: none;
        }}
        .edit-form .btn-save {{
            background: #00c853;
            border: none;
            padding: 10px 25px;
            border-radius: 20px;
            color: #000;
            font-weight: bold;
            cursor: pointer;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 0.8rem;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo">📈 Trading Bot</div>
        <div class="status-badge">● Live</div>
    </div>
    <div class="profile-card">
        <img class="avatar" src="{WebHandler.admin_avatar}" alt="Admin" id="avatar-img">
        <div class="profile-info">
            <h2 id="admin-name">{WebHandler.admin_name}</h2>
            <div class="title">Head Trader & Developer</div>
            <button class="btn-edit" onclick="toggleEdit()">✎ កែប្រែ Profile</button>
        </div>
    </div>
    <div class="edit-form" id="edit-form">
        <form method="POST" action="/update-profile">
            <input type="hidden" name="secret" value="{WEB_SECRET}">
            <label>ឈ្មោះ Admin</label>
            <input type="text" name="name" value="{WebHandler.admin_name}" required>
            <label>URL រូបតំណាង</label>
            <input type="url" name="avatar" value="{WebHandler.admin_avatar}" required>
            <button type="submit" class="btn-save">💾 រក្សាទុក</button>
        </form>
    </div>
    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-value">{WebHandler.lessons_today}</div>
            <div class="stat-label">មេរៀនថ្ងៃនេះ</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{WebHandler.total_sent}</div>
            <div class="stat-label">សរុបទាំងអស់</div>
        </div>
    </div>
    <div class="chart-container">
        <div class="chart-title">📊 តារាង Trading (ចលនា)</div>
        <div class="chart">
            <div class="chart-line"></div>
            <div class="candles">
                <div class="candle" style="animation-delay:0s;"></div>
                <div class="candle" style="animation-delay:0.2s; background:#ff5252;"></div>
                <div class="candle" style="animation-delay:0.4s;"></div>
                <div class="candle" style="animation-delay:0.6s; background:#ff5252;"></div>
                <div class="candle" style="animation-delay:0.8s;"></div>
                <div class="candle" style="animation-delay:1s; background:#ffeb3b;"></div>
            </div>
        </div>
    </div>
    <div class="trigger-section">
        <form method="POST" action="/trigger">
            <input type="hidden" name="secret" value="{WEB_SECRET}">
            <button type="submit" class="btn-trigger">📨 បោះមេរៀនទាំង 30 ឥឡូវនេះ</button>
        </form>
        {message}
    </div>
    <div class="footer">Trading Lesson Bot v2.0 | Powered by Render & Python</div>
</div>
<script>
    // Register service worker for PWA offline support
    if ('serviceWorker' in navigator) {{
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('SW registered', reg))
            .catch(err => console.log('SW failed', err));
    }}
    function toggleEdit() {{
        var f = document.getElementById('edit-form');
        f.style.display = f.style.display === 'block' ? 'none' : 'block';
    }}
</script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _serve_manifest(self):
        manifest = {
            "name": "Trading Bot Dashboard",
            "short_name": "TradingBot",
            "description": "Control your Telegram Trading Bot",
            "start_url": "/admin",
            "display": "standalone",
            "background_color": "#0b0f1c",
            "theme_color": "#00d2ff",
            "icons": [
                {
                    "src": WebHandler.admin_avatar,
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": WebHandler.admin_avatar,
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        data = json.dumps(manifest)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "max-age=3600")
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))

    def _serve_sw(self):
        sw_js = """
const CACHE_NAME = 'trading-bot-v1';
const urlsToCache = [
  '/admin',
  '/'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
"""
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript")
        self.send_header("Cache-Control", "max-age=86400")
        self.end_headers()
        self.wfile.write(sw_js.encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ["/", "/admin"]:
            self._render_dashboard()
        elif path == "/manifest.json":
            self._serve_manifest()
        elif path == "/sw.js":
            self._serve_sw()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length else ""
        params = parse_qs(post_data)
        secret = params.get('secret', [''])[0]

        if self.path == "/trigger":
            if secret != WEB_SECRET:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
            threading.Thread(target=self._trigger_send).start()
            self._render_dashboard('<div class="message">🚀 កំពុងបោះមេរៀនទាំង 30... សូមពិនិត្យ Telegram Group</div>')

        elif self.path == "/update-profile":
            if secret != WEB_SECRET:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
            new_name = params.get('name', [''])[0].strip()
            new_avatar = params.get('avatar', [''])[0].strip()
            if new_name:
                WebHandler.admin_name = new_name
            if new_avatar:
                WebHandler.admin_avatar = new_avatar
            # Redirect back to dashboard
            self.send_response(302)
            self.send_header("Location", "/admin")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _trigger_send(self):
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
    logger.info(f"🌐 Trading Dashboard at https://your-url.onrender.com/admin")
    server.serve_forever()

# ------- Telegram Command /send -------
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_USER_ID and str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("⛔ អ្នកមិនមានសិទ្ធិប្រើពាក្យបញ្ជានេះទេ។")
        return

    await update.message.reply_text("🚀 កំពុងចាប់ផ្ដើមបោះមេរៀនទាំង 30...")
    await _do_send_all(context.bot)
    await update.message.reply_text("🏁 បញ្ចប់ការបោះមេរៀនទាំង 30")

async def _do_send_all(bot: Bot):
    global LESSONS_SENT_TODAY, TOTAL_SENT_ALL_TIME
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
    LESSONS_SENT_TODAY += 1
    TOTAL_SENT_ALL_TIME += 1
    WebHandler.lessons_today = LESSONS_SENT_TODAY
    WebHandler.total_sent = TOTAL_SENT_ALL_TIME

# ------- Scheduled Task -------
async def scheduled_send_all(bot: Bot):
    logger.info("🚀 កាលវិភាគ៖ បោះមេរៀនទាំង 30")
    await _do_send_all(bot)
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
    global LESSONS_SENT_TODAY, TOTAL_SENT_ALL_TIME
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        logger.error("❌ BOT_TOKEN ឬ GROUP_CHAT_ID មិនបានកំណត់!")
        return

    # Start web server
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