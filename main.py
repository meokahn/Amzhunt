
import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
import re

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variabili ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Es: @amazonhunterITA
TG_API_ID = int(os.getenv("TG_API_ID"))
TG_API_HASH = os.getenv("TG_API_HASH")
TG_SESSION = os.getenv("TG_SESSION")
SOURCE_CHANNEL = "scontierrati"

# Variabili di stato
MESSAGGI_GIA_INVIATI = set()
CONTEGGIO_GIORNALIERO = 0

# Estrai link affiliato e immagine
async def estrai_info(msg):
    links = re.findall(r'(https?://[^\s]+)', msg.message)
    amazon_links = [l for l in links if re.search(r'amzn\.(to|com|eu)|amazon\.', l)]
    if not amazon_links:
        return None, None

    link = amazon_links[0]
    if "?tag=" not in link:
        if "?" in link:
            link_aff = link + "&tag=amazonhunter0a-21"
        else:
            link_aff = link + "?tag=amazonhunter0a-21"
    else:
        link_aff = link

    testo = msg.message.replace(link, link_aff) + "\n\n#hunterITA"
    immagine = None
    if isinstance(msg.media, MessageMediaPhoto):
        immagine = await msg.download_media()
    return testo, immagine

# Invia messaggio
async def invia_messaggio(bot, testo, immagine):
    global CONTEGGIO_GIORNALIERO
    try:
        if immagine:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=immagine, caption=testo, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=testo, parse_mode=ParseMode.HTML)
        logger.info("✅ Inviato: " + testo[:40])
        CONTEGGIO_GIORNALIERO += 1
    except Exception as e:
        logger.error(f"❌ Errore invio: {e}")

# Controllo e invio offerte
async def controlla_offerte():
    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient(TG_SESSION, TG_API_ID, TG_API_HASH)
    await client.start()
    async for msg in client.iter_messages(SOURCE_CHANNEL, limit=10):
        if msg.message and "amazon" in msg.message.lower() and msg.id not in MESSAGGI_GIA_INVIATI:
            testo, immagine = await estrai_info(msg)
            if testo:
                await invia_messaggio(bot, testo, immagine)
                MESSAGGI_GIA_INVIATI.add(msg.id)
    await client.disconnect()

# Invia report giornaliero
async def invia_report():
    bot = Bot(token=BOT_TOKEN)
    report = f"📊 Report giornaliero Amazon Hunter\nOfferte pubblicate: {CONTEGGIO_GIORNALIERO}\n#hunterITA"
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=report, parse_mode=ParseMode.HTML)
        logger.info("✅ Report inviato")
    except Exception as e:
        logger.error(f"❌ Errore report: {e}")

# Esecuzione schedulata
async def scheduler():
    while True:
        ora = datetime.now()
        if 8 <= ora.hour <= 23 and ora.minute in [0, 30]:
            await controlla_offerte()
        if ora.hour == 23 and ora.minute == 30:
            await invia_report()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler())
