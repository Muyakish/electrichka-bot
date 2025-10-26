import os
import random
import time
import requests
import telebot
from dotenv import load_dotenv
from googletrans import Translator

load_dotenv()

BOT_TOKEN = os.getenv("ELECTRICHKA_BOT_TOKEN")
CHANNEL_ID = os.getenv("ELECTRICHKA_CHANNEL_ID")
ADMIN_ID = int(os.getenv("ELECTRICHKA_ADMIN_ID", "0"))
CAPTIONS_FILE = os.getenv("ELECTRICHKA_CAPTIONS_FILE", "captions3.txt")

bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()

def get_quote():
    """Получаем случайную цитату"""
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=10)
        data = res.json()[0]
        original = f"💭 {data['q']}\n— {data['a']}"
        translated = translator.translate(data["q"], src="en", dest="ru").text
        return f"{original}\n\n💬 {translated}"
    except Exception as e:
        print("⚠️ Ошибка получения цитаты:", e)
        with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
            return random.choice(f.readlines()).strip()

def get_image():
    """Случайное изображение"""
    return f"https://picsum.photos/800/800?random={random.randint(1, 10000)}"

def get_signature():
    """Рандомная подпись из captions3.txt"""
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f if x.strip()]
    return random.choice(lines)

def post_to_channel():
    quote = get_quote()
    image_url = get_image()
    signature = get_signature()
    message = f"{quote}\n\n{signature}"
    bot.send_photo(CHANNEL_ID, image_url, caption=message)
    print("✅ Пост опубликован")

# Основной цикл
while True:
    try:
        post_to_channel()
        time.sleep(3 * 60 * 60)  # каждые 3 часа
    except Exception as e:
        print("⚠️ Ошибка цикла:", e)
        try:
            bot.send_message(ADMIN_ID, f"⚠️ Ошибка: {e}")
        except Exception:
            pass
        time.sleep(60)
