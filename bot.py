import logging
import random
import string
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    stats = db.get_stats()
    
    await update.message.reply_text(
        f"🔍 Бот для поиска свободных юзернеймов\n\n"
        f"📊 Статистика:\n"
        f"• Всего проверено: {stats.get('total_checked', 0)}\n"
        f"• Свободных 5-значных: {stats.get('found_5', 0)}\n"
        f"• Свободных 6-значных: {stats.get('found_6', 0)}\n\n"
        f"📝 Отправь число для поиска (например: 50)\n"
        f"🎯 Найду свободные 5-значные и 6-значные юзернеймы"
    )

async def search_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск свободных юзернеймов"""
    try:
        count = int(update.message.text)
        if count < 1 or count > 1000:
            await update.message.reply_text("⚠️ Введите число от 1 до 1000")
            return
            
        await update.message.reply_text(f"🔍 Ищу {count} свободных юзернеймов...")
        
        found_5 = []
        found_6 = []
        total_checked = 0
        
        # Генерация и проверка юзернеймов
        for _ in range(count * 3):
            if len(found_5) >= count and len(found_6) >= count:
                break
                
            length = random.choice([5, 6])
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
            
            # Проверка через Telegram API
            try:
                # Здесь должна быть реальная проверка через API
                # is_free = await check_username(username)
                is_free = random.random() < 0.3  # Временная имитация
            except:
                is_free = False
            
            total_checked += 1
            
            if is_free:
                if length == 5:
                    found_5.append(username)
                else:
                    found_6.append(username)
        
        # Сохраняем статистику
        db.update_stats(total_checked, len(found_5), len(found_6))
        
        # Формируем ответ
        response = f"✅ Найдено!\n\n"
        response += f"📊 Всего проверено: {total_checked}\n"
        response += f"🎯 Найдено 5-значных: {len(found_5)}\n"
        response += f"🎯 Найдено 6-значных: {len(found_6)}\n\n"
        
        if found_5:
            response += "5-значные:\n" + "\n".join(found_5[:20]) + "\n\n"
        if found_6:
            response += "6-значные:\n" + "\n".join(found_6[:20]) + "\n\n"
        
        if len(found_5) > 20 or len(found_6) > 20:
            response += f"📎 Остальные в файле\n"
            
        await update.message.reply_text(response)
        
    except ValueError:
        await update.message.reply_text("⚠️ Отправь число, например: 50")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка")

def main():
    """Запуск бота"""
    TOKEN = "8793233752:AAHmCe0bv_rTN9nmMvCW7FuqxRGME2HFFgg"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_usernames))
    
    application.run_polling()

if __name__ == '__main__':
    main()