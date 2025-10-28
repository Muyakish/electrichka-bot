import os
import time
import requests
import logging
import random
from io import BytesIO
from threading import Thread
from flask import Flask
from PIL import Image
from deep_translator import GoogleTranslator
import schedule

# ------------------- Настройка логов -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Логи также будут в stdout → видны в Render Logs

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
TELEGRAM_BOT_TOKEN = os.getenv("ELECTRICHKA_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ELECTRICHKA_CHANNEL_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("[CRITICAL] Отсутствуют переменные: ELECTRICHKA_BOT_TOKEN или ELECTRICHKA_CHANNEL_ID", flush=True)
    exit(1)

POST_INTERVAL_HOURS = int(os.getenv("POST_INTERVAL_HOURS", "3"))
FIRMA_SIGNATURE = "— Ваши мысли с Электричкой 🚆"

HASHTAGS = ["#философия", "#юмор", "#цитата", "#мотивация", "#мысли"]
CATEGORIES = ["жизнь", "счастье", "мотивация", "юмор", "философия"]

LOGO_PATH = "logo.png"

# ------------------- Функции -------------------
def get_quote():
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=10)
        res.raise_for_status()
        data = res.json()[0]
        quote = data.get('q', 'Цитата недоступна')
        author = data.get('a', '')
        return quote, author
    except Exception as e:
        print(f"[ERROR] Ошибка получения цитаты: {e}", flush=True)
        return "Цитата недоступна", ""

def translate_quote(text):
    try:
        return GoogleTranslator(source='en', target='ru').translate(text)
    except Exception as e:
        print(f"[ERROR] Ошибка перевода: {e}", flush=True)
        return text

def get_image():
    try:
        url = f"https://picsum.photos/800/600?random={int(time.time())}"
        img_bytes = requests.get(url, timeout=10).content
        image = Image.open(BytesIO(img_bytes)).convert("RGBA")
        return overlay_logo(image)
    except Exception as e:
        print(f"[ERROR] Ошибка получения изображения: {e}", flush=True)
        return None

def overlay_logo(image):
    try:
        if not os.path.exists(LOGO_PATH):
            output = BytesIO()
            image.save(output, format="PNG")
            output.seek(0)
            return output

        logo = Image.open(LOGO_PATH).convert("RGBA")
        base_width = int(image.width * 0.15)
        w_percent = base_width / float(logo.width)
        h_size = int(float(logo.height) * w_percent)
        logo = logo.resize((base_width, h_size), Image.LANCZOS)
        position = (image.width - logo.width - 10, image.height - logo.height - 10)
        image.paste(logo, position, logo)

        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output
    except Exception as e:
        print(f"[ERROR] Ошибка наложения логотипа: {e}", flush=True)
        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

def check_telegram():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        res = requests.get(url, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[ERROR] Ошибка проверки Telegram API: {e}", flush=True)
        return False

def send_post(quote, author, image_bytes):
    if image_bytes is None:
        print("[WARN] Нет изображения, пост не отправлен", flush=True)
        return

    hashtags = " ".join(random.sample(HASHTAGS, k=2))
    category = random.choice(CATEGORIES)
    text = f"[{category.upper()}] {quote}\n— {author}\n{FIRMA_SIGNATURE}\n{hashtags}"

    if not check_telegram():
        print("[ERROR] Telegram API недоступен, пост не отправлен", flush=True)
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": text},
            files={"photo": ("image.png", image_bytes, "image/png")},
            timeout=15
        )
        if response.status_code == 200:
            print("[INFO] Пост отправлен успешно", flush=True)
        else:
            print(f"[ERROR] Ошибка отправки: {response.status_code} {response.text}", flush=True)
    except Exception as e:
        print(f"[ERROR] Исключение при отправке: {e}", flush=True)

def job_post():
    try:
        print("[INFO] Запуск задачи постинга...", flush=True)
        quote, author = get_quote()
        quote_ru = translate_quote(quote)
        image_bytes = get_image()
        full_quote = f"{quote} ({quote_ru})"
        send_post(full_quote, author, image_bytes)
    except Exception as e:
        print(f"[CRITICAL] Необработанная ошибка в job_post: {e}", flush=True)

# ------------------- Планировщик -------------------
schedule.every(POST_INTERVAL_HOURS).hours.do(job_post)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)

Thread(target=run_scheduler, daemon=True).start()

# ------------------- Первый пост сразу при запуске -------------------
print("[INFO] Отправка первого поста немедленно...", flush=True)
job_post()

print("[INFO] Бот запущен. Ожидание следующих задач...", flush=True)

# ------------------- Главный цикл -------------------
while True:
    time.sleep(60)
