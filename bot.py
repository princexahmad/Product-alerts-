from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from database import SessionLocal, User, Product
from scraper import get_price_and_stock
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
import os
import threading

# Environment
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is missing in environment variables")

# Scheduler & Executor
scheduler = BackgroundScheduler()
executor = ThreadPoolExecutor(max_workers=3)

# Start Command
def start(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.chat_id == chat_id).first()
    if not user:
        user = User(chat_id=chat_id, name=update.effective_user.first_name)
        db.add(user)
        db.commit()
    db.close()

    keyboard = [[KeyboardButton("🛒 My Alerts")]]
    update.message.reply_text(
        "👋 हेलो! कोई Amazon/Flipkart URL भेजें और मैं आपको Price Drop या In-Stock की तुरंत जानकारी दूंगा!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# Handle Messages
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.effective_user.id
    db = SessionLocal()

    if "amazon.in" in text or "flipkart.com" in text:
        product = db.query(Product).filter(Product.url == text).first()
        if not product:
            data = get_price_and_stock(text)
            if data:
                name = text.split("/")[-1].replace("-", " ").title()[:50]
                product = Product(
                    url=text,
                    name=name,
                    last_price=data.get('price') or 0,
                    last_stock=data.get('in_stock'),
                    created_by=chat_id,
                    alert_when_instock=True
                )
                db.add(product)
                db.commit()
                update.message.reply_text(f"✅ ट्रैकिंग शुरू! मैं आपको अपडेट भेजूंगा।")
            else:
                update.message.reply_text("❌ URL लोड नहीं हो सका। कृपया फिर भेजें।")
        else:
            update.message.reply_text("⚠️ यह प्रोडक्ट पहले से ट्रैक हो रहा है।")
    elif text == "🛒 My Alerts":
        products = db.query(Product).filter(Product.created_by == chat_id).all()
        if not products:
            update.message.reply_text("📦 आपने कोई प्रोडक्ट नहीं ट्रैक किया।")
        else:
            msg = "🔔 आपके ट्रैक्ड प्रोडक्ट:\n\n"
            for p in products:
                status = "✅ In Stock" if p.last_stock else "❌ Out"
                msg += f"🛒 {p.name}\n💰 ₹{p.last_price} | {status}\n🔗 {p.url}\n\n"
            update.message.reply_text(msg)
    else:
        update.message.reply_text("कृपया Amazon/Flipkart का URL भेजें।")
    db.close()

# Background Check (1 product)
def check_single_product(product):
    db = SessionLocal()
    try:
        data = get_price_and_stock(product.url)
        if data:
            changes = []
            old_price = product.last_price
            new_price = data['price']

            if new_price and new_price < old_price * 0.97 and new_price > 0:
                changes.append(f"💰 Price Drop! ₹{old_price} → ₹{new_price}")
                product.last_price = new_price

            if data['in_stock'] and not product.last_stock:
                changes.append(f"📦 In Stock! '{product.name}' अब उपलब्ध है!")
                product.last_stock = True

            if changes:
                db.commit()
                # Alert user
                context = CallbackContext(None)
                context.bot.send_message(chat_id=product.created_by, text="\n".join(changes))
    except Exception as e:
        print(f"Error checking {product.url}: {e}")
    finally:
        db.close()

# Main Background Task
def background_check():
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    for product in products:
        executor.submit(check_single_product, product)

# Scheduler Setup
scheduler.add_job(background_check, 'interval', seconds=30, id='check_products', max_instances=1)
scheduler.start()

# Bot Run
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
