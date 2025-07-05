import os
import re
import asyncio
from telethon import TelegramClient
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_CHANNEL = os.getenv("CHANNEL_ID")
AMAZON_TAG = os.getenv("AMAZON_TAG")

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def extract_amazon_link(text):
    pattern = r"(https?://(?:www\.)?(?:amzn\.to|amazon\.[a-z\.]{2,6})/[^\s]+)"
    match = re.search(pattern, text)
    if match:
        link = match.group(1)
        return append_affiliate_tag(link)
    return None

def append_affiliate_tag(url):
    if "tag=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}tag={AMAZON_TAG}"

async def fetch_last_amazon_message():
    async for message in client.iter_messages(SOURCE_CHANNEL, limit=10):
        if message.text and extract_amazon_link(message.text):
            return {
                "text": message.text,
                "photo": message.photo,
                "id": message.id
            }
    return None

async def forward_offer():
    deal = await fetch_last_amazon_message()
    if not deal:
        return

    link = extract_amazon_link(deal["text"])
    if not link:
        return

    caption = f"{deal['text']}\n{link} #hunterITA"

    if deal["photo"]:
        await client.send_file(TARGET_CHANNEL, deal["photo"], caption=caption)
    else:
        await client.send_message(TARGET_CHANNEL, caption)

async def daily_report():
    now = datetime.now().strftime("%Y-%m-%d")
    await client.send_message(TARGET_CHANNEL, f"📊 Report #hunterITA {now}: offerte pubblicate oggi.")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Rome")
    scheduler.add_job(forward_offer, 'cron', hour='8-23', minute='0,30')
    scheduler.add_job(daily_report, 'cron', hour=23, minute=30)
    scheduler.start()
    print("Bot in esecuzione...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
