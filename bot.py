import os
import time
import requests
import random
from io import BytesIO
from threading import Thread
from flask import Flask, request, jsonify
from PIL import Image
from deep_translator import GoogleTranslator
import schedule

TELEGRAM_BOT_TOKEN = os.getenv("ELECTRICHKA_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ELECTRICHKA_CHANNEL_ID")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("[CRITICAL] ❌ Отсутствуют переменные: ELECTRICHKA_BOT_TOKEN или ELECTRICHKA_CHANNEL_ID", flush=True)
    exit(1)

def load_captions():
    if os.path.exists("captions3.txt"):
        with open("captions3.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if lines:
                return lines
    return ["🚆 Электричка уже тронулась — прыгай в поток идей!"]

FIRMA_SIGNATURES = load_captions()
HASHTAGS = ["#философия", "#юмор", "#цитата", "#мотивация", "#мысли"]
CATEGORIES = ["жизнь", "счастье", "мотивация", "юмор", "философия"]
LOGO_PATH = "logo.png"

def get_quote():
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=10)
        res.raise_for_status()
        data = res.json()[0]
        return data.get('q', 'Цитата недоступна'), data.get('a', '')
    except Exception as e:
        print(f"[ERROR] Цитата: {e}", flush=True)
        return "Цитата недоступна", ""

def translate_quote(text):
    try:
        return GoogleTranslator(source='en', target='ru').translate(text)
    except Exception as e:
        print(f"[ERROR] Перевод: {e}", flush=True)
        return text

def get_image():
    try:
        url = f"https://picsum.photos/800/600?random={int(time.time())}"
        img_bytes = requests.get(url, timeout=10).content
        image = Image.open(BytesIO(img_bytes)).convert("RGBA")
        return overlay_logo(image)
    except Exception as e:
        print(f"[ERROR] Изображение: {e}", flush=True)
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
        h_size = int((base_width / logo.width) * logo.height)
        logo = logo.resize((base_width, h_size), Image.LANCZOS)
        pos = (image.width - logo.width - 10, image.height - logo.height - 10)
        image.paste(logo, pos, logo)
        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output
    except Exception as e:
        print(f"[ERROR] Логотип: {e}", flush=True)
        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

def send_post(quote, author, image_bytes):
    if not image_bytes or image_bytes.getbuffer().nbytes == 0:
        print("[WARN] Нет изображения", flush=True)
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        firma = random.choice(FIRMA_SIGNATURES)
        text = f"[{random.choice(CATEGORIES).upper()}] {quote}\n— {author}\n{firma}\n{' '.join(random.sample(HASHTAGS, 2))}"
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": text},
            files={"photo": ("post.png", image_bytes, "image/png")},
            timeout=15
        )
        if resp.status_code == 200:
            print("[✅] Пост отправлен успешно", flush=True)
        else:
            print(f"[❌] Ошибка Telegram: {resp.status_code} {resp.text}", flush=True)
    except Exception as e:
        print(f"[❌] Исключение при отправке: {e}", flush=True)

def job_post():
    print("[🔄] Запуск задачи постинга...", flush=True)
    quote, author = get_quote()
    quote_ru = translate_quote(quote)
    image = get_image()
    if image is None:
        print("[WARN] Пропуск поста: изображение не загружено", flush=True)
        return
    send_post(f"{quote} ({quote_ru})", author, image)

app = Flask(__name__)

@app.route('/')
def home():
    return "🚆 Электричка работает."

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return jsonify({"ok": True})

    message = update["message"]
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()

    if not ADMIN_CHAT_ID or str(chat_id) != str(ADMIN_CHAT_ID):
        print(f"[DEBUG] Команда от неадмина: {chat_id}", flush=True)
        return jsonify({"ok": True})

    def send_reply(text):
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text}
            )
        except Exception as e:
            print(f"[ERROR] Не удалось отправить ответ: {e}", flush=True)

    if text == "/post_now":
        print(f"[INFO] Получена команда /post_now от {chat_id}", flush=True)
        Thread(target=job_post).start()
        send_reply("✅ Пост запущен!")
    elif text == "/status":
        send_reply("🟢 Электричка в пути!")

    return jsonify({"ok": True})

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

def ensure_webhook():
    if not WEBHOOK_URL:
        print("[WARN] WEBHOOK_URL не задан — команды недоступны", flush=True)
        return
    full_url = f"{WEBHOOK_URL.rstrip('/')}/webhook"
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
        json={"url": full_url}
    )
    print(f"[INFO] Webhook response: {resp.json()}", flush=True)

ensure_webhook()

schedule.every(3).hours.do(job_post)

def run_scheduler():
    print("[⏰] Планировщик запущен: пост каждые 3 часа", flush=True)
    while True:
        schedule.run_pending()
        time.sleep(30)

Thread(target=run_scheduler, daemon=True).start()

print("[🚀] Отправка первого поста...", flush=True)
job_post()

print("[🟢] Бот готов к работе.", flush=True)
while True:
    time.sleep(60)
