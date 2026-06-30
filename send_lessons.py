#!/usr/bin/env python3
"""
ស្គ្រីបដោយដៃ - បោះមេរៀនទាំង 30 (គ្រប់គ្រង HTML Error & Flood Control)
"""

import asyncio
import os
import re
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode
from lessons_data import LESSONS, TOTAL_LESSONS

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
TOPIC_ID = os.getenv('TOPIC_ID')

DELAY_BETWEEN_MESSAGES = 3  # វិនាទី

def clean_html_tags(text):
    """លុបស្លាក HTML មិនត្រឹមត្រូវ (ដូចជា <>) ចេញ"""
    text = re.sub(r'<>', '', text)
    return text

async def send_all_lessons():
    bot = Bot(token=BOT_TOKEN)
    for lesson in LESSONS:
        lesson_id = lesson['id']
        try:
            header = f"📚 <b>មេរៀន Trading</b>\n"
            header += f"📂 ប្រភេទ: <b>{lesson['category']}</b>\n"
            header += f"📝 មេរៀនទី {lesson['id']}/{TOTAL_LESSONS}\n"
            header += "━" * 35 + "\n\n"
            content = clean_html_tags(lesson['content'])
            message = header + content

            kwargs = {
                'chat_id': GROUP_CHAT_ID,
                'text': message,
                'parse_mode': ParseMode.HTML
            }
            if TOPIC_ID:
                kwargs['message_thread_id'] = int(TOPIC_ID)

            await bot.send_message(**kwargs)
            print(f"✅ មេរៀនទី {lesson_id}")
        except Exception as e:
            err_msg = str(e)
            if "Can't parse entities" in err_msg:
                print(f"⚠️ មេរៀនទី {lesson_id}: HTML មិនត្រឹមត្រូវ ផ្ញើជា Plain Text")
                try:
                    kwargs['parse_mode'] = None
                    await bot.send_message(**kwargs)
                    print(f"✅ មេរៀនទី {lesson_id} (Plain Text)")
                except Exception as e2:
                    print(f"❌ បរាជ័យមេរៀនទី {lesson_id}: {e2}")
            elif "Flood control" in err_msg:
                wait_time = 30
                match = re.search(r'Retry in (\d+) seconds', err_msg)
                if match:
                    wait_time = int(match.group(1)) + 1
                print(f"⏳ Flood control – រង់ចាំ {wait_time} វិនាទី...")
                await asyncio.sleep(wait_time)
                try:
                    await bot.send_message(**kwargs)
                    print(f"✅ មេរៀនទី {lesson_id} (ក្រោយរង់ចាំ)")
                except Exception as e3:
                    print(f"❌ បរាជ័យមេរៀនទី {lesson_id}: {e3}")
            else:
                print(f"❌ បរាជ័យមេរៀនទី {lesson_id}: {e}")

        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)

if __name__ == "__main__":
    asyncio.run(send_all_lessons())
    print("🏁 បញ្ចប់ការបោះមេរៀនទាំង 30")