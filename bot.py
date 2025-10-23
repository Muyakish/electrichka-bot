import os
import random
import requests
import asyncio
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from telegram import Bot
from telegram.constants import ParseMode

# === НАСТРОЙКИ ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

# --- Получаем цитату ---
async def get_quote():
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=15)
        if response.status_code == 200:
            data = response.json()[0]
            quote = data["q"]
            author = data["a"]
            return f"{quote}\n— {author}"
        else:
            print(f"Ошибка цитаты: код {response.status_code}")
    except Exception as e:
        print("Ошибка цитаты:", e)
    return None


# --- Перевод цитаты ---
async def translate_quote(quote_text):
    try:
        result = GoogleTranslator(source='en', target='ru').translate(quote_text)
        return result
    except Exception as e:
        print("Ошибка перевода:", e)
        return None


# --- Получаем случайную картинку ---
async def get_image_url():
    width = random.choice([800, 1000, 1200])
    height = random.choice([600, 800])
    return f"https://picsum.photos/{width}/{height}"


# --- Публикуем пост ---
async def publish_post():
    print("🚀 Публикация нового поста...")

    quote = await get_quote()
    if not quote:
        print("⚠️ Не удалось получить цитату.")
        return

    translated = await translate_quote(quote)
    if not translated:
        print("⚠️ Не удалось перевести цитату.")
        return

    image_url = await get_image_url()

    post_text = (
        f"🇬🇧 {quote}\n\n"
        f"🇷🇺 {translated}\n\n"
        f"#философия #юмор #электричка"
    )

    try:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=image_url,
            caption=post_text,
            parse_mode=ParseMode.HTML,
        )
        print("✅ Пост опубликован успешно!")
    except Exception as e:
        print("❌ Ошибка публикации:", e)


# --- Планировщик каждые 3 часа ---
async def scheduler():
    while True:
        await publish_post()
        print("🕒 Следующий пост через 3 часа...")
        await asyncio.sleep(3 * 60 * 60)  # 3 часа


async def main():
    print("🤖 Электричка 5.0 запущена — авто-постинг каждые 3 часа.")
    await scheduler()


if __name__ == "__main__":
    asyncio.run(main())
