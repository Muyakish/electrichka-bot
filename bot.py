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

# ------------------- Настройки бота -------------------
TELEGRAM_BOT_TOKEN = os.getenv("ELECTRICHKA_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ELECTRICHKA_CHANNEL_ID")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # Твой Telegram ID

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("[CRITICAL] ❌ Отсутствуют переменные: ELECTRICHKA_BOT_TOKEN или ELECTRICHKA_CHANNEL_ID", flush=True)
    exit(1)

# Список фирменных подписей
FIRMA_SIGNATURES = [
    "🚆 Электричка уже тронулась — прыгай в поток идей!",
    "🌿 Даже розетка устала, а ты всё ещё заряжаешь вдохновение.",
    "💡 Иногда свет включается не в комнате, а в голове.",
    "🔥 Искра внутри важнее молнии снаружи.",
    "🌙 Покой приходит, когда перестаёшь искать розетку.",
    "☕ Мозг требует перезагрузки, душа — подзарядки.",
    "🎭 Жизнь — театр, а я пассажир без билета.",
    "🐢 Не спеши, поезд идей всё равно не уйдёт без тебя.",
    "🌅 Вдохновение не приходит по расписанию, но электричка — да.",
    "🧩 Каждый пост — ещё один кусочек электрического мира.",
    "🎧 Иногда нужно просто послушать тишину на рельсах мысли.",
    "🚉 Следующая станция — смысл. Не проспи.",
    "📡 Душа ловит Wi-Fi от Вселенной.",
    "🎈 Пусть мысли летят быстрее поездов.",
    "🕰 Время идёт, но электричка подождёт.",
    "🚦 Красный — стой. Зелёный — твори.",
    "🛤 Мы все едем по своим рельсам — важно не сошёл ли ты с пути.",
    "📷 Жизнь — кадр, вдохновение — выдержка.",
    "⚙️ Каждый сбой системы — шанс обновиться.",
    "🌌 Даже звёзды знают расписание своего сияния.",
    "☁️ Мечты — это облака, электричка идей идёт сквозь них.",
    "🎢 Мысли петляют, как рельсы в метель.",
    "🍃 Отпусти всё ненужное — пусть упадёт на шпалы.",
    "📚 Каждый день — билет без возврата.",
    "🚀 Иногда, чтобы поехать вперёд, нужно чуть-чуть сойти с рельс.",
    "🌕 Ночь — не тьма, а время для подсветки идей.",
    "✨ Искра вдохновения всегда с задержкой, но приходит.",
    "🌊 Поток мыслей — наше электричество.",
    "🪞 В отражении окна виден ты — пассажир времени.",
    "🪫 Даже разряженная душа может давать свет.",
    "📍 Мы не теряем путь — просто делаем остановку.",
    "🎡 Идеи кружатся, как вагоны в голове.",
    "🪶 Лёгкость приходит, когда перестаёшь держаться за поручни.",
    "🧭 Вдохновение не ищут — на него садятся, как на поезд.",
    "📦 Скука — это багаж без ручки.",
    "🌠 В каждом посте — искра от контактного провода.",
    "💭 Мысли текут по рельсам подсознания.",
    "🎇 Мир — это станция пересадки идей.",
    "🚧 Иногда нужно закрыть перегон, чтобы отремонтировать мечты.",
    "📻 Вселенная шепчет в динамиках твоей головы.",
    "🧘‍♂️ Покой — это тоже движение, просто внутреннее.",
    "📖 Каждый день — новая станция смысла.",
    "🕊 Свобода — это когда едешь без конечной.",
    "🎬 Каждый кадр вдохновения — билет в вечность.",
    "🎨 Творчество — график без расписания.",
    "🚴 Даже стоя на месте, можно ехать внутри.",
    "⚡ Искра к искре — и уже светло.",
    "🪄 Идеи не исчезают — они просто пересаживаются на другой маршрут.",
    "🎰 Жизнь — это случайность с элементами расписания.",
    "🌤 Иногда лучше опоздать, чем уехать не туда.",
    "🧤 Не бойся холодных дней — вдохновение всё равно греет.",
    "🛞 Колёса судьбы всегда по рельсам выбора.",
    "🎒 Каждый опыт — багаж идей.",
    "🪙 Ценность мысли — в пути, а не в пункте назначения.",
    "🧠 Мозг как двигатель: иногда греется, но едет.",
    "🎢 Жизнь — это аттракцион с пересадками.",
    "🕹 Управляй своим маршрутом.",
    "🎶 Каждый пост — это музыка контактной сети.",
    "🚋 Идеи едут трамваем сознания.",
    "🕯 Даже одна мысль способна осветить тоннель.",
    "🧵 Мысли — это провода между сердцем и разумом.",
    "🪴 Растут не только растения — растут идеи.",
    "🛠 Исправь шпалу — и путь станет ровным.",
    "📸 Момент вдохновения — не улови, почувствуй.",
    "📞 Услышь звонок судьбы — твой поезд прибыл.",
    "🧊 Иногда нужно замереть, чтобы растопить старые страхи.",
    "🪁 Ветер перемен дует в окно купе души.",
    "🚨 Светофор вдохновения всегда мигает жёлтым.",
    "🧲 Притягивай только нужное.",
    "🎁 Каждый день — новый вагон подарков.",
    "🧳 Чем меньше багажа, тем быстрее электричка.",
    "🚪 Новые идеи не входят в закрытые двери.",
    "🔋 Заряжайся от мелочей.",
    "💫 Мысли — как искры, не дай им погаснуть.",
    "📆 Вчера был черновик, сегодня — публикация.",
    "🧩 Каждый день — кусочек вдохновенного пазла.",
    "🚿 Смой усталость, оставь только свет.",
    "🏁 Не важно, где конец пути — важно, что ты в пути.",
    "🎠 Вдохновение — круговое движение.",
    "🎗 Даже остановка — часть маршрута.",
    "🎯 Вдохновение точно попадёт в цель, если дать ему шанс.",
    "🎏 Пусть ветер несёт твои идеи дальше станции.",
    "🎻 Душа звучит, когда ты на своей частоте.",
    "🎺 Музыка мыслей громче шума мира.",
    "🚲 Вдохновение не требует топлива, только движения.",
    "🛸 Иногда идеи прилетают не по расписанию.",
    "📯 Услышь сигнал — пора в путь.",
    "🪶 Пусть лёгкость станет маршрутом.",
    "🕊 Каждый день — билет без возврата."
]

HASHTAGS = ["#философия", "#юмор", "#цитата", "#мотивация", "#мысли"]
CATEGORIES = ["жизнь", "счастье", "мотивация", "юмор", "философия"]
LOGO_PATH = "logo.png"

# ------------------- Функции -------------------
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
        print("[WARN] Нет изображения для отправки", flush=True)
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

# ------------------- Flask сервер и Webhook -------------------
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

    # Только админ может управлять
    if not ADMIN_CHAT_ID or chat_id != ADMIN_CHAT_ID:
        return jsonify({"ok": True})

    if text == "/post_now":
        Thread(target=job_post).start()
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "✅ Пост запущен!"}
        )
    elif text == "/status":
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "🟢 Электричка в пути!"}
        )
    return jsonify({"ok": True})

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Запуск Flask в фоне
Thread(target=run_flask, daemon=True).start()

# Установка webhook
def set_webhook():
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    if not WEBHOOK_URL:
        print("[WARN] WEBHOOK_URL не задан — команды недоступны", flush=True)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    resp = requests.post(url, json={"url": f"{WEBHOOK_URL}/webhook"})
    print(f"[INFO] Webhook response: {resp.json()}", flush=True)

set_webhook()

# ------------------- Планировщик -------------------
schedule.every(3).hours.do(job_post)

def run_scheduler():
    print("[⏰] Планировщик запущен: пост каждые 3 часа", flush=True)
    while True:
        schedule.run_pending()
        time.sleep(30)

Thread(target=run_scheduler, daemon=True).start()

# ------------------- Первый пост сразу -------------------
print("[🚀] Отправка первого поста...", flush=True)
job_post()

# ------------------- Главный цикл -------------------
print("[🟢] Бот работает. Ждём команды или по расписанию...", flush=True)
while True:
    time.sleep(60)
