import os
import re
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telethon.tl.types import MessageMediaPhoto
from telethon.tl.functions.messages import GetMessagesRequest

load_dotenv()

# Variabili di ambiente
api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
session = os.getenv("TG_SESSION_NAME")
channel_source = os.getenv("TG_CHANNEL_SOURCE")
channel_target = os.getenv("TG_CHANNEL_TARGET")
affiliate_tag = os.getenv("AMAZON_TAG")

client = TelegramClient(session, api_id, api_hash)
scheduler = AsyncIOScheduler()

posted_today = []  # Tracciamento offerte per report 23:30

# Funzione per modificare link con tag affiliato
def convert_link(original_url):
    return re.sub(r"(amazon\.[a-z.]+/[\w\-%]+/[\w\d]+)(\?.*?)?(?=\s|$)", 
                  rf"\1?tag={affiliate_tag}", original_url)

# Estrai immagine dal messaggio
async def get_image(message):
    if message.media and isinstance(message.media, MessageMediaPhoto):
        msg = await client(GetMessagesRequest(id=[message.id], peer=channel_source))
        media_msg = msg.messages[0]
        return await client.download_media(media_msg.media)
    return None

# Estrai e pubblica offerte valide
async def check_new_deals():
    async for message in client.iter_messages(channel_source, limit=10):
        if not message.text:
            continue

        # Cerca link Amazon (anche abbreviati tipo amzn.to)
        if re.search(r"(amazon\.[a-z.]+|amzn\.to)/", message.text):
            image_path = await get_image(message)
            modified_text = convert_link(message.text)

            await client.send_file(
                entity=channel_target,
                file=image_path if image_path else None,
                caption=f"{modified_text}\n\n#hunterITA"
            )
            posted_today.append(datetime.now().strftime("%H:%M"))

# Report giornaliero alle 23:30
async def send_daily_report():
    count = len(posted_today)
    await client.send_message(
        entity=channel_target,
        message=f"📊 Report Amazon Hunter ITA – Oggi pubblicate {count} offerte.\n#hunterITA"
    )
    posted_today.clear()

# Avvio scheduler
async def start_bot():
    scheduler.add_job(check_new_deals, "cron", minute="0,30", hour="8-23")
    scheduler.add_job(send_daily_report, "cron", hour=23, minute=30)
    scheduler.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(client.start())
    loop.create_task(start_bot())
    loop.run_forever()
