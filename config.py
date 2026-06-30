import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
SEND_TIME = os.getenv('SEND_TIME', '09:00')
SEND_MODE = os.getenv('SEND_MODE', 'both')

CRYPTO_PAIRS = [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'ADA/USDT'
]

FOREX_PAIRS = [
    'EUR/USD',
    'GBP/USD',
    'USD/JPY',
    'AUD/USD',
    'USD/CHF'
]

TIMEFRAMES = {
    'daily': '1d',
    '4h': '4h',
    '1h': '1h'
}

MAX_SIGNALS_PER_MARKET = 5