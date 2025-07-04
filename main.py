import logging
from telegram import Bot, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime
import asyncio
import re
import os

# Config
SOURCE_CHANNEL = "-1001822360895"  # @scontierrati
TARGET_CHANNEL = "@amazonhunterITA"
AMAZON_TAG = "amazonhunter0a-21"
ACTIVE_HOURS = range(8, 24)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estrai link Amazon e aggiorna il tag affiliato
def extract_amazon_links(text):
    links = re.findall(r"(https://(?:www\.)?amzn\.to/\S+|https://www\.amazon\.it/\S+)", text)
    updated = []
    for link in links:
        if "tag=" in link:
            link = re.sub(r"tag=[^&\s]+", f"tag={AMAZON_TAG}", link)
        else:
            sep = "&" if "?" in link else "?"
            link = f"{link}{sep}tag={AMAZON_TAG}"
        updated.append(link)
    return updated

# Funzione di inoltro
async def forward_message(update, context):
    now = datetime.now().hour
    if now not in ACTIVE_HOURS:
        return

    message = update.channel_post
    if not message or not message.text:
        return

    links = extract_amazon_links(message.text)
    if not links:
        return

    new_text = re.sub(r"https://\S+", "", message.text)
    new_text = new_text.strip() + f"\n\n{links[0]}\n#hunterITA"

    # Invia con immagine se disponibile
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        await context.bot.send_photo(chat_id=TARGET_CHANNEL, photo=photo_file_id, caption=new_text[:1024])
    else:
        await context.bot.send_message(chat_id=TARGET_CHANNEL, text=new_text[:4096])

async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.ALL, forward_message))
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
