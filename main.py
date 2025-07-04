
import logging
import os
import re
import time
from datetime import datetime
from telegram import Bot, InputMediaPhoto
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TAG = "amazonhunter0a-21"

bot = Bot(token=TOKEN)
published_today = []

def replace_affiliate_link(text):
    amazon_links = re.findall(r'(https?://[^\s]+)', text)
    for link in amazon_links:
        if "amazon" in link:
            if "tag=" in link:
                new_link = re.sub(r'tag=[^&\s]+', f'tag={TAG}', link)
            elif "?" in link:
                new_link = link + f"&tag={TAG}"
            else:
                new_link = link + f"?tag={TAG}"
            text = text.replace(link, new_link)
    return text + " #hunterITA"

def handler(update, context: CallbackContext):
    if update.channel_post and "amazon" in update.channel_post.text.lower():
        now = datetime.now()
        if 8 <= now.hour <= 23:
            text = replace_affiliate_link(update.channel_post.text)
            published_today.append(1)
            context.bot.send_message(chat_id=CHANNEL_ID, text=text)
            if update.channel_post.photo:
                context.bot.send_photo(chat_id=CHANNEL_ID, photo=update.channel_post.photo[-1].file_id)

def send_report(context: CallbackContext):
    context.bot.send_message(chat_id=CHANNEL_ID, text=f"🧾 Report giornaliero: {len(published_today)} offerte pubblicate oggi. #hunterITA")
    published_today.clear()

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.channel, handler))
    updater.job_queue.run_daily(send_report, time=datetime.strptime("23:30", "%H:%M").time())
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
