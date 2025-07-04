import logging
import os
from telegram import Bot
from telegram.constants import ParseMode
import asyncio

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@amazonhunterITA"  # Il tuo canale Telegram

# Verifica presenza variabili d'ambiente
if not BOT_TOKEN or not CHANNEL_ID:
    logger.error("Variabili d'ambiente mancanti!")
    raise ValueError("BOT_TOKEN e CHANNEL_ID devono essere configurati")

# Funzione per inviare messaggi
async def invia_messaggio(bot: Bot, testo: str, immagine_url: str = None):
    try:
        if immagine_url:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=immagine_url,
                caption=testo,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=testo,
                parse_mode=ParseMode.HTML
            )
        logger.info("Messaggio inviato con successo!")
    except Exception as e:
        logger.error(f"Errore nell'invio del messaggio: {e}")

# Funzione principale
async def main():
    try:
        bot = Bot(token=BOT_TOKEN)
        link_affiliato = "https://amzn.to/3Gc5ciC?tag=amazonhunter0a-21"
        
        testo = f"""🎯 Offerta Amazon!

🔗 <a href="{link_affiliato}">CLICCA QUI PER L'OFFERTA</a>

#hunterITA"""

        immagine = "https://m.media-amazon.com/images/I/61dHwru7D5L._AC_SL1500_.jpg"
        await invia_messaggio(bot, testo, immagine)
        
    except Exception as e:
        logger.exception(f"Errore durante l'esecuzione: {e}")

# Avvio bot
if __name__ == "__main__":
    asyncio.run(main())
