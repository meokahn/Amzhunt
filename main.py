import os
import re
import asyncio
from datetime import datetime
import logging
import pytz

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Bot
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- Configurazione del logging ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Caricamento variabili d'ambiente ---
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_SOURCE = os.getenv("CHANNEL_SOURCE")
CHANNEL_TARGET = os.getenv("CHANNEL_TARGET")
AMAZON_TAG = os.getenv("AMAZON_TAG")

# --- Variabili globali per il tracking ---
posted_message_ids = set()
daily_posts_counter = 0

async def check_and_post_deals():
    """Controlla i nuovi messaggi, li modifica e li pubblica."""
    global daily_posts_counter

    rome_tz = pytz.timezone("Europe/Rome")
    now = datetime.now(rome_tz)
    
    if not 8 <= now.hour < 23:
        logger.info(f"Fuori orario in Italia ({now.strftime('%H:%M')}). Salto il controllo.")
        return

    logger.info(f"Avvio controllo su {CHANNEL_SOURCE} (Ora italiana: {now.strftime('%H:%M')})...")
    bot = Bot(token=BOT_TOKEN)

    # --- NUOVO BLOCCO DI CONNESSIONE MANUALE ---
    # 1. Inizializza il client SENZA sessione
    client = TelegramClient(None, API_ID, API_HASH)
    # 2. Assegna la sessione manualmente dalla stringa
    client.session = StringSession(SESSION_STRING)
    
    try:
        logger.info("Connessione manuale del client Telethon...")
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("ERRORE: La SESSION_STRING non è valida o è scaduta. Rigenerala.")
            await client.disconnect()
            return
        
        logger.info("Client connesso con successo. Recupero messaggi...")
        messages = await client.get_messages(CHANNEL_SOURCE, limit=20)

        for message in reversed(messages):
            if not message or not message.text or message.id in posted_message_ids:
                continue

            amazon_link_match = re.search(r"(https?://(?:www\.)?(?:amzn\.to|amazon\.[a-z\.]+)[^\s]+)", message.text)

            if amazon_link_match:
                original_link = amazon_link_match.group(0)
                cleaned_link = original_link.split('?')[0]
                affiliate_link = f"{cleaned_link}?tag={AMAZON_TAG}"
                new_text = message.text.replace(original_link, affiliate_link)
                final_text = f"{new_text}\n\n#hunterITA"
                
                logger.info(f"Trovata offerta con link: {affiliate_link}")

                try:
                    if message.photo:
                        await bot.send_photo(
                            chat_id=CHANNEL_TARGET, photo=message.photo.file_id,
                            caption=final_text, parse_mode=ParseMode.HTML
                        )
                    else:
                        await bot.send_message(
                            chat_id=CHANNEL_TARGET, text=final_text,
                            parse_mode=ParseMode.HTML, disable_web_page_preview=False
                        )
                    
                    logger.info(f"Offerta {message.id} pubblicata su {CHANNEL_TARGET}.")
                    posted_message_ids.add(message.id)
                    daily_posts_counter += 1
                    await asyncio.sleep(3)

                except Exception as e:
                    logger.error(f"Errore invio messaggio {message.id}: {e}")

    except Exception as e:
        logger.error(f"Errore generale nel blocco Telethon: {e}", exc_info=True)
    finally:
        if client.is_connected():
            await client.disconnect()
        logger.info("Client disconnesso.")
    # --- FINE BLOCCO MANUALE ---

async def send_daily_report():
    # ... il resto della funzione non cambia ...
    global daily_posts_counter
    bot = Bot(token=BOT_TOKEN)
    report_message = f"📊 **Report Giornaliero** 📊\n\nOfferte pubblicate oggi: **{daily_posts_counter}**"
    await bot.send_message(chat_id=CHANNEL_TARGET, text=report_message, parse_mode=ParseMode.MARKDOWN)
    logger.info("Report giornaliero inviato.")
    daily_posts_counter = 0

if __name__ == "__main__":
    if not all([API_ID, API_HASH, SESSION_STRING, BOT_TOKEN, CHANNEL_SOURCE, CHANNEL_TARGET, AMAZON_TAG]):
        logger.critical("Una o più variabili d'ambiente non sono state impostate. Uscita.")
        exit()

    scheduler = AsyncIOScheduler(timezone="Europe/Rome")
    scheduler.add_job(check_and_post_deals, 'interval', minutes=30)
    scheduler.add_job(send_daily_report, 'cron', hour=23, minute=30)

    logger.info("Scheduler avviato. Il bot è operativo.")
    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot fermato.")

