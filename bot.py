import logging
import random
import string
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

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
        f"🔍 Бот для поиска свободных юзернеймов\n\n"
        f"Выбери длину юзернейма для поиска:\n"
        f"• Только буквы (a-z)\n"
        f"• 5 или 6 знаков\n\n"
        f"📊 Статистика:\n"
        f"• Всего проверено: {stats.get('total_checked', 0)}\n"
        f"• Свободных 5-значных: {stats.get('found_5', 0)}\n"
        f"• Свободных 6-значных: {stats.get('found_6', 0)}",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_stats":
        stats = db.get_stats()
        await query.message.reply_text(
            f"📊 Детальная статистика:\n\n"
            f"• Всего проверено: {stats.get('total_checked', 0)}\n"
            f"• Свободных 5-значных: {stats.get('found_5', 0)}\n"
            f"• Свободных 6-значных: {stats.get('found_6', 0)}"
        )
        return
    
    if query.data == "length_5":
        context.user_data['search_length'] = 5
        await query.message.reply_text("✅ Выбраны 5-значные юзернеймы\n\nОтправь количество для поиска (например: 50)")
    elif query.data == "length_6":
        context.user_data['search_length'] = 6
        await query.message.reply_text("✅ Выбраны 6-значные юзернеймы\n\nОтправь количество для поиска (например: 50)")

def check_username(username):
    """Проверка через t.me - ВОЗВРАЩАЕТ True если СВОБОДЕН"""
    try:
        url = f"https://t.me/{username}"
        response = requests.get(url, timeout=5, allow_redirects=True)
        # Если 404 - страницы нет, значит юзернейм свободен
        if response.status_code == 404:
            return True
        # Если есть контент - занят
        else:
            return False
    except Exception as e:
        logger.error(f"Ошибка проверки {username}: {e}")
        return False

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
        msg = await update.message.reply_text(f"🔍 Начинаю поиск {count} {length}-значных юзернеймов...\n\n")
        
        found = []
        total_checked = 0
        checked = set()
        last_checks = []
        
        while len(found) < count and total_checked < count * 5:
            username = ''.join(random.choices(string.ascii_lowercase, k=length))
            
            if username in checked:
                continue
            checked.add(username)
            total_checked += 1
            
            # РЕАЛЬНАЯ ПРОВЕРКА
            is_free = check_username(username)
            
            if is_free:
                found.append(username)
                last_checks.append(f"✅ @{username}")
                logger.info(f"✅ СВОБОДЕН: {username}")
            else:
                last_checks.append(f"❌ @{username}")
            
            # Обновляем каждые 3 проверки
            if total_checked % 3 == 0 or len(found) >= count:
                display = last_checks[-30:]
                text = f"🔍 Поиск {count} {length}-значных\n"
                text += f"⏳ Проверено: {total_checked} | ✅ Найдено: {len(found)}\n\n"
                text += "\n".join(display)
                
                if len(found) < count:
                    text += f"\n\n⏳ Продолжаю..."
                else:
                    text += f"\n\n✅ ГОТОВО!"
                
                try:
                    await msg.edit_text(text)
                except:
                    pass
        
        # Сохраняем статистику
        if length == 5:
            db.update_stats_5(total_checked, len(found))
        else:
            db.update_stats_6(total_checked, len(found))
        
        # Финальный результат
        if found:
            final = f"✅ Найдено {len(found)} свободных {length}-значных!\n\n"
            final += "\n".join([f"✅ @{u}" for u in found[:50]])
            if len(found) > 50:
                final += f"\n\n📎 И ещё {len(found) - 50}"
        else:
            final = f"😔 Не найдено. Проверено: {total_checked}"
        
        await msg.edit_text(final)
        
    except ValueError:
        await update.message.reply_text("⚠️ Отправь число")
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