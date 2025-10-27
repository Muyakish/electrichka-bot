import os
import time
import requests
from threading import Thread
from flask import Flask
from io import BytesIO
from googletrans import Translator
import logging
import random
import traceback
from PIL import Image

# ------------------- Настройка логов -------------------
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------- Flask сервер -------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "🚆 Электричка работает."

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

# ------------------- Настройки бота -------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ваш_токен_бота")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "ваш_чат_id")
POST_INTERVAL = 3 * 60 * 60  # каждые 3 часа
FIRMA_SIGNATURE = "— Ваши мысли с Электричкой 🚆"

translator = Translator()
HASHTAGS = ["#философия", "#юмор", "#цитата", "#мотивация", "#мысли"]
CATEGORIES = ["жизнь", "счастье", "мотивация", "юмор", "философия"]

LOGO_PATH = "logo.png"  # поместить файл логотипа рядом с ботом

# ------------------- Функции -------------------
def get_quote():
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=10)
        data = res.json()[0]
        quote = data.get('q', 'Цитата недоступна')
        author = data.get('a', '')
        return quote, author
    except Exception as e:
        logging.error(f"Ошибка получения цитаты: {e}")
        return "Цитата недоступна", ""

def translate_quote(text):
    try:
        return translator.translate(text, dest='ru').text
    except Exception as e:
        logging.error(f"Ошибка перевода: {e}")
        return text

def get_image():
    try:
        url = f"https://picsum.photos/800/600?random={int(time.time())}"
        img_bytes = requests.get(url, timeout=10).content
        image = Image.open(BytesIO(img_bytes)).convert("RGBA")
        return overlay_logo(image)
    except Exception as e:
        logging.error(f"Ошибка получения изображения: {e}")
        return None

def overlay_logo(image):
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        # масштабирование логотипа пропорционально
        base_width = int(image.width * 0.15)
        w_percent = (base_width / float(logo.width))
        h_size = int((float(logo.height) * float(w_percent)))
        logo = logo.resize((base_width, h_size), Image.ANTIALIAS)

        # позиция в правом нижнем углу
        position = (image.width - logo.width - 10, image.height - logo.height - 10)
        image.paste(logo, position, logo)
        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output
    except Exception as e:
        logging.error(f"Ошибка наложения логотипа: {e}")
        return None

def check_telegram():
    try:
        res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=10)
        return res.status_code == 200
    except Exception as e:
        logging.error(f"Ошибка проверки Telegram API: {e}")
        return False

def send_post(quote, author, image_bytes):
    if image_bytes is None:
        logging.warning("Нет изображения, пост не отправлен")
        return
    hashtags = " ".join(random.sample(HASHTAGS, k=2))
    category = random.choice(CATEGORIES)
    text = f"[{category.upper()}] {quote}\n— {author}\n{FIRMA_SIGNATURE}\n{hashtags}"
    if not check_telegram():
        logging.error("Telegram API недоступен, пост не отправлен")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": text},
            files={"photo": image_bytes},
            timeout=15
        )
        logging.info("Пост отправлен успешно")
    except Exception as e:
        logging.error(f"Ошибка отправки: {traceback.format_exc()}")

def post_cycle():
    while True:
        try:
            quote, author = get_quote()
            quote_ru = translate_quote(quote)
            image_bytes = get_image()
            send_post(f"{quote} ({quote_ru})", author, image_bytes)
            time.sleep(POST_INTERVAL)
        except Exception as e:
            logging.error(f"Ошибка в цикле постинга: {traceback.format_exc()}")
            time.sleep(60)

# ------------------- Запуск цикла -------------------
Thread(target=post_cycle, daemon=True).start()

# ------------------- Главный цикл -------------------
while True:
    time.sleep(60)
