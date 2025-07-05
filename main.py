
import os
import asyncio
import logging
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configurazioni
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SOURCE_URL = "https://t.me/scontierrati"

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Funzione per ottenere messaggi da @scontierrati
def fetch_amazon_deals():
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        if response.status_code != 200:
            logger.error("Errore nel recupero della pagina: %s", response.status_code)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        messages = soup.select("div.tgme_widget_message_text")
        photos = soup.select("a.tgme_widget_message_photo_wrap")
        
        for msg, photo_tag in zip(messages[::-1], photos[::-1]):  # Ultimo messaggio in cima
            text = msg.get_text()
            match = re.search(r"(https://(?:www\.)?amzn\.[a-z]{2,3}(?:\.[a-z]{2})?/[a-zA-Z0-9\-_/%?=]+)", text)
            if match:
                url = match.group(1)
                if "amazon" in url:
                    img_url = photo_tag["style"].split("url('")[1].split("')")[0]
                    return {
                        "text": text,
                        "image": img_url.replace("https://telegram", "https://tlgrm") if "telegram" in img_url else img_url,
                        "url": url
                    }
        return None

    except Exception as e:
        logger.exception("Errore durante lo scraping")
        return None

# Funzione per inviare l'offerta su Telegram
async def post_deal():
    bot = Bot(token=BOT_TOKEN)
    deal = fetch_amazon_deals()
    if deal:
        try:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=deal["image"],
                caption=f"{deal['text']}

#hunterITA
{deal['url'].split('?')[0]}?tag=amazonhunter0a-21"
            )
            logger.info("Offerta pubblicata")
        except TelegramError as e:
            logger.error("Errore Telegram: %s", e)
    else:
        logger.info("Nessuna nuova offerta trovata.")

# Scheduler
async def scheduler():
    sched = AsyncIOScheduler(timezone="Europe/Rome")
    sched.add_job(post_deal, "cron", hour="8-23", minute="0,30")
    sched.add_job(send_report, "cron", hour=23, minute=30)
    sched.start()
    logger.info("Scheduler avviato")
    while True:
        await asyncio.sleep(3600)

# Report giornaliero
async def send_report():
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text="✅ Report 23:30: offerte pubblicate con successo. #hunterITA")
        logger.info("Report inviato")
    except TelegramError as e:
        logger.error("Errore Telegram nel report: %s", e)

# Avvio
if __name__ == "__main__":
    asyncio.run(scheduler())
