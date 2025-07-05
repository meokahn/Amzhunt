import asyncio
import os
import re
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION_NAME = os.getenv("TG_SESSION", "anon")
SOURCE_CHANNEL = os.getenv("TG_SOURCE_CHANNEL")
DEST_CHANNEL = os.getenv("TG_DEST_CHANNEL")
AFFILIATE_TAG = os.getenv("AMAZON_TAG", "amazonhunter0a-21")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def extract_amazon_link(text):
    match = re.search(r"(https?://[^\s]*amazon[^\s]*)", text)
    if match:
        url = match.group(1)
        if "tag=" not in url:
            if "?" in url:
                url += f"&tag={AFFILIATE_TAG}"
            else:
                url += f"?tag={AFFILIATE_TAG}"
        return url
    return None

async def fetch_last_valid_post():
    async with client:
        history = await client(GetHistoryRequest(
            peer=SOURCE_CHANNEL,
            limit=10,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        for message in history.messages:
            if message.message:
                link = extract_amazon_link(message.message)
                if link:
                    return message, link
    return None, None

async def post_deal():
    await client.start()
    message, link = await fetch_last_valid_post()
    if not message:
        return

    caption = f"{message.message}\n\n🔗 {link} #hunterITA"
    file = None

    if isinstance(message.media, MessageMediaPhoto):
        file = await client.download_media(message.media)

    await client.send_file(DEST_CHANNEL, file if file else None, caption=caption)
    await client.disconnect()

async def send_report():
    now = datetime.now()
    if now.hour == 23 and now.minute >= 30:
        await client.start()
        await client.send_message(DEST_CHANNEL, f"📊 Report: offerte pubblicate oggi #hunterITA")
        await client.disconnect()

async def scheduler():
    while True:
        now = datetime.now()
        if 8 <= now.hour <= 23 and now.minute % 30 == 0:
            await post_deal()
            await send_report()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler())