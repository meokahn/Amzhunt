
import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
import re

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variabili ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TG_API_ID = int(os.getenv("TG_API_ID"))
TG_API_HASH = os.getenv("TG_API_HASH")
TG_SESSION = os.getenv("TG_SESSION")
SOURCE_CHANNEL = "scontierrati"
TRACKING_ID = "amazonhunter0a-21"

# Stato
MESSAGGI_INVIATI = set()
OFFERTE_OGGI = 0

# Estrazione e trasformazione
async def estrai_dati(msg):
    links = re.findall(r'(https?://[^\s]+)', msg.message or "")
    amazon_links = [l for l in links if re.search(r'amzn\.(to|com|eu)|amazon\.', l)]
    if not amazon_links:
        return None, None
    link = amazon_links[0]
    if "?tag=" not in link:
        link_aff = link + ("&" if "?" in link else "?") + f"tag={TRACKING_ID}"
    else:
        link_aff = link
    testo = msg.message.replace(link, link_aff) + "\n\n#hunterITA"
    immagine = None
    if isinstance(msg.media, MessageMediaPhoto):
        immagine = await msg.download_media()
    return testo, immagine

# Invio messaggio
async def invia(bot, testo, immagine):
    global OFFERTE_OGGI
    try:
        if immagine:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=immagine, caption=testo, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=testo, parse_mode=ParseMode.HTML)
        OFFERTE_OGGI += 1
        logger.info("✅ Inviato messaggio.")
    except Exception as e:
        logger.error(f"Errore invio messaggio: {e}")

# Controllo offerte
async def controlla():
    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient(TG_SESSION, TG_API_ID, TG_API_HASH)
    await client.start()
    async for msg in client.iter_messages(SOURCE_CHANNEL, limit=10):
        if msg.message and "amazon" in msg.message.lower() and msg.id not in MESSAGGI_INVIATI:
            testo, immagine = await estrai_dati(msg)
            if testo:
                await invia(bot, testo, immagine)
                MESSAGGI_INVIATI.add(msg.id)
    await client.disconnect()

# Invio report alle 23:30
async def report():
    bot = Bot(token=BOT_TOKEN)
    testo = f"📊 Report Amazon Hunter\nOfferte pubblicate oggi: {OFFERTE_OGGI}\n#hunterITA"
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=testto, parse_mode=ParseMode.HTML)
        logger.info("✅ Report inviato.")
    except Exception as e:
        logger.error(f"Errore report: {e}")

# Schedulazione ogni 30 min tra 08 e 23 + report 23:30
async def scheduler():
    while True:
        ora = datetime.now()
        if 8 <= ora.hour <= 23 and ora.minute in [0, 30]:
            await controlla()
        if ora.hour == 23 and ora.minute == 30:
            await report()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler())
