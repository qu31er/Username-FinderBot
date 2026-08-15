import logging
import random
import string
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с инлайн кнопками"""
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
    """Обработчик нажатия инлайн кнопок"""
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
    
    # Сохраняем выбранную длину в context
    if query.data == "length_5":
        context.user_data['search_length'] = 5
        await query.message.reply_text("✅ Выбраны 5-значные юзернеймы\n\nОтправь количество для поиска (например: 50)")
    elif query.data == "length_6":
        context.user_data['search_length'] = 6
        await query.message.reply_text("✅ Выбраны 6-значные юзернеймы\n\nОтправь количество для поиска (например: 50)")

def check_username_via_api(username):
    """Проверяет свободен ли юзернейм через API Telegram"""
    try:
        # Используем API Telegram для проверки
        url = f"https://t.me/{username}"
        response = requests.get(url, timeout=5)
        
        # Если страница существует - юзернейм занят
        if response.status_code == 200:
            return False
        else:
            return True
    except:
        # Если ошибка - считаем что занят
        return False

async def search_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск свободных юзернеймов"""
    try:
        # Проверяем выбрана ли длина
        if 'search_length' not in context.user_data:
            await update.message.reply_text(
                "⚠️ Сначала выбери длину юзернейма через /start"
            )
            return
            
        count = int(update.message.text)
        if count < 1 or count > 1000:
            await update.message.reply_text("⚠️ Введите число от 1 до 1000")
            return
            
        length = context.user_data['search_length']
        msg = await update.message.reply_text(f"🔍 Ищу {count} свободных {length}-значных юзернеймов...\n⏳ Это может занять время")
        
        found = []
        total_checked = 0
        checked_usernames = set()
        
        # Генерация и проверка юзернеймов (только буквы)
        while len(found) < count and total_checked < count * 5:
            # Только буквы, без цифр
            username = ''.join(random.choices(string.ascii_lowercase, k=length))
            
            # Пропускаем если уже проверяли
            if username in checked_usernames:
                continue
            checked_usernames.add(username)
            total_checked += 1
            
            # Проверка через сайт t.me
            is_free = check_username_via_api(username)
            
            # Обновляем статус каждые 20 проверок
            if total_checked % 20 == 0:
                try:
                    await msg.edit_text(
                        f"🔍 Ищу {count} свободных {length}-значных юзернеймов...\n"
                        f"⏳ Проверено: {total_checked}\n"
                        f"✅ Найдено: {len(found)}"
                    )
                except:
                    pass
            
            if is_free:
                found.append(username)
                logger.info(f"Найден свободный: {username}")
        
        # Сохраняем статистику
        if length == 5:
            db.update_stats_5(total_checked, len(found))
        else:
            db.update_stats_6(total_checked, len(found))
        
        # Формируем ответ с @
        response = f"✅ Найдено {len(found)} свободных {length}-значных юзернеймов!\n\n"
        response += f"📊 Всего проверено: {total_checked}\n"
        response += f"🎯 Найдено: {len(found)}\n\n"
        
        if found:
            response += "📝 Нажми на любой юзернейм, чтобы проверить:\n\n"
            found_with_at = [f"@{username}" for username in found]
            response += "\n".join(found_with_at[:50])
            
            if len(found) > 50:
                response += f"\n\n📎 И ещё {len(found) - 50} юзернеймов"
        else:
            response = f"😔 Не найдено свободных {length}-значных юзернеймов\n\n"
            response += f"📊 Всего проверено: {total_checked}"
        
        await msg.edit_text(response)
        
    except ValueError:
        await update.message.reply_text("⚠️ Отправь число, например: 50")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

def main():
    """Запуск бота"""
    TOKEN = "8793233752:AAHmCe0bv_rTN9nmMvCW7FuqxRGME2HFFgg"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_usernames))
    
    application.run_polling()

if __name__ == '__main__':
    main()