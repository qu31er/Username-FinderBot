import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# Хранилище выданных юзернеймов (в памяти)
given_usernames = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_stats()
    
    keyboard = [
        [
            InlineKeyboardButton("🔢 5 знаков", callback_data="length_5"),
            InlineKeyboardButton("🔢 6 знаков", callback_data="length_6")
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="show_stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔍 Генератор уникальных юзернеймов\n\n"
        f"Выбери длину:\n"
        f"• 5 знаков\n"
        f"• 6 знаков\n\n"
        f"📊 Статистика:\n"
        f"• Сгенерировано 5-значных: {stats.get('found_5', 0)}\n"
        f"• Сгенерировано 6-значных: {stats.get('found_6', 0)}",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_stats":
        stats = db.get_stats()
        await query.message.reply_text(
            f"📊 Статистика:\n\n"
            f"• Сгенерировано 5-значных: {stats.get('found_5', 0)}\n"
            f"• Сгенерировано 6-значных: {stats.get('found_6', 0)}"
        )
        return
    
    if query.data == "length_5":
        context.user_data['search_length'] = 5
        await query.message.reply_text("✅ Выбраны 5-значные юзернеймы\n\nОтправь количество (например: 50)")
    elif query.data == "length_6":
        context.user_data['search_length'] = 6
        await query.message.reply_text("✅ Выбраны 6-значные юзернеймы\n\nОтправь количество (например: 50)")

def generate_unique_username(length, existing):
    """Генерирует уникальный юзернейм"""
    while True:
        username = ''.join(random.choices(string.ascii_lowercase, k=length))
        if username not in existing:
            return username

async def search_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if 'search_length' not in context.user_data:
            await update.message.reply_text("⚠️ Сначала выбери длину через /start")
            return
            
        count = int(update.message.text)
        if count < 1 or count > 1000:
            await update.message.reply_text("⚠️ Введите число от 1 до 1000")
            return
            
        length = context.user_data['search_length']
        
        await update.message.reply_text(f"🔍 Генерирую {count} уникальных {length}-значных юзернеймов...")
        
        generated = []
        
        for _ in range(count):
            username = generate_unique_username(length, given_usernames)
            given_usernames.add(username)
            generated.append(username)
        
        # Сохраняем статистику
        if length == 5:
            db.update_stats_5(0, len(generated))
        else:
            db.update_stats_6(0, len(generated))
        
        # Формируем ответ
        response = f"✅ Сгенерировано {len(generated)} уникальных {length}-значных юзернеймов!\n\n"
        response += "\n".join([f"@{u}" for u in generated[:50]])
        
        if len(generated) > 50:
            response += f"\n\n📎 И ещё {len(generated) - 50} юзернеймов"
        
        await update.message.reply_text(response)
        
    except ValueError:
        await update.message.reply_text("⚠️ Отправь число, например: 50")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

def main():
    TOKEN = "8793233752:AAHmCe0bv_rTN9nmMvCW7FuqxRGME2HFFgg"
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_usernames))
    
    application.run_polling()

if __name__ == '__main__':
    main()