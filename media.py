import io
import os
import logging
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ContentType
from aiogram import Router
from requests_oauthlib import OAuth1
import asyncio

# Load env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TW_CONSUMER_KEY = os.getenv("TW_CONSUMER_KEY")
TW_CONSUMER_SECRET = os.getenv("TW_CONSUMER_SECRET")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
router = Router()

# Twitter OAuth
twitter_auth = OAuth1(TW_CONSUMER_KEY, TW_CONSUMER_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)
TWITTER_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"

def upload_to_twitter(file_bytes: bytes, mime_type="image/png"):
    total_bytes = len(file_bytes)
    # INIT
    r = requests.post(
        TWITTER_UPLOAD_URL,
        data={"command": "INIT", "total_bytes": str(total_bytes), "media_type": mime_type},
        auth=twitter_auth
    )
    r.raise_for_status()
    media_id = r.json()["media_id_string"]
    # APPEND
    r = requests.post(
        TWITTER_UPLOAD_URL,
        data={"command": "APPEND", "media_id": media_id, "segment_index": "0"},
        files={"media": file_bytes},
        auth=twitter_auth
    )
    r.raise_for_status()
    # FINALIZE
    r = requests.post(
        TWITTER_UPLOAD_URL,
        data={"command": "FINALIZE", "media_id": media_id},
        auth=twitter_auth
    )
    r.raise_for_status()
    return media_id

@router.message(F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT, ContentType.AUDIO}))
@router.message(F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT, ContentType.AUDIO}))
async def handle_media(message: types.Message):
    file_obj = None
    mime_type = "image/png"

    # Determine file
    if message.photo:
        file_obj = await bot.get_file(message.photo[-1].file_id)
        mime_type = "image/png"
    elif message.video:
        file_obj = await bot.get_file(message.video.file_id)
        mime_type = message.video.mime_type or "video/mp4"
    elif message.document:
        file_obj = await bot.get_file(message.document.file_id)
        mime_type = message.document.mime_type or "application/octet-stream"
    elif message.audio:
        file_obj = await bot.get_file(message.audio.file_id)
        mime_type = message.audio.mime_type or "audio/mpeg"

    if not file_obj:
        await message.answer("No supported media found.")
        return

    # Download into BytesIO and extract bytes
    bio = await bot.download_file(file_obj.file_path)
    file_bytes = bio.getvalue() if isinstance(bio, io.BytesIO) else bio

    # Upload to Twitter
    try:
        media_id = upload_to_twitter(file_bytes, mime_type)
        await message.answer(f"Twitter Media ID: {media_id}")
    except Exception as e:
        await message.answer(f"Error uploading to Twitter: {e}")

dp.include_router(router)

async def main():
    print("Bot running. Listening for media...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




