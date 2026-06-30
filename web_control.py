#!/usr/bin/env python3
"""
Web Interface សម្រាប់បញ្ជា Bot Trading Lesson
"""

import asyncio
import os
from flask import Flask, render_template_string, redirect, url_for
from dotenv import load_dotenv
from lessons_data import LESSONS, TOTAL_LESSONS
from telegram import Bot
from telegram.constants import ParseMode
import time
import threading

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
TOPIC_ID = os.getenv('TOPIC_ID')

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Control Panel</title>
    <meta charset="UTF-8">
</head>
<body style="font-family: sans-serif; padding: 20px;">
    <h1>📚 Trading Lesson Bot Control</h1>
    <p>ចុចប៊ូតុងខាងក្រោមដើម្បីបោះមេរៀនទាំង 30 ទៅកាន់ Channel/Group</p>
    <a href="/send" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">បោះមេរៀន 30</a>
    <p style="margin-top: 20px;">ស្ថានភាព: <span id="status">រង់ចាំ</span></p>
</body>
</html>
"""

def send_all_lessons_sync():
    """មុខងារសម្រាប់ផ្ញើមេរៀន (សមកាលកម្ម)"""
    async def _send():
        bot = Bot(token=BOT_TOKEN)
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
                print(f"✅ បានបញ្ជូនមេរៀនទី {lesson['id']}")
                await asyncio.sleep(3)  # ការពារ flood
            except Exception as e:
                print(f"❌ កំហុស {lesson['id']}: {e}")
        print("បញ្ចប់ការបោះមេរៀន")
    asyncio.run(_send())

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send')
def send():
    # រត់ការផ្ញើក្នុង thread ដើម្បីកុំឲ្យរាំងស្ទះ web server
    threading.Thread(target=send_all_lessons_sync).start()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # ដំណើរការ Web Server នៅ localhost ច្រក 5000
    app.run(host='127.0.0.1', port=5000, debug=True)