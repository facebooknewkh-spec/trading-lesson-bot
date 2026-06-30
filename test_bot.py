import requests
from config import BOT_TOKEN, GROUP_CHAT_ID

def test_send():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_CHAT_ID,
        "text": "🧪 តេស្តផ្ញើសារ"
    }
    resp = requests.post(url, json=payload)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
    if resp.status_code == 200:
        print("✅ Bot អាចផ្ញើសារទៅ Group បាន!")
    else:
        print("❌ មានកំហុស។ សូមពិនិត្យ GROUP_CHAT_ID និងការបន្ថែម Bot ចូល Group")

test_send()