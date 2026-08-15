import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        stats = db.get_stats()
        
        # Безопасное получение значений
        total_checked = stats.get('total_checked', 0) if stats else 0
        total_passed = stats.get('total_passed', 0) if stats else 0
        total_failed = stats.get('total_failed', 0) if stats else 0
        
        await update.message.reply_text(
            f"👋 Привет! Я бот для проверки ссылок.\n\n"
            f"📊 Статистика:\n"
            f"• Всего проверено: {total_checked}\n"
            f"• Успешно: {total_passed}\n"
            f"• Ошибок: {total_failed}\n\n"
            f"📎 Отправь мне ссылку, и я её проверю."
        )
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ссылок"""
    try:
        url = update.message.text
        user_id = update.effective_user.id
        
        # Здесь ваша логика проверки ссылки
        # Пример:
        # result = check_url(url)
        
        # Обновляем статистику
        db.update_stats(user_id, url, status="checked")
        
        await update.message.reply_text(
            f"✅ Ссылка проверена!\n"
            f"🔗 {url}\n"
            f"📊 Статус: OK"
        )
    except Exception as e:
        logger.error(f"Ошибка при проверке ссылки: {e}")
        await update.message.reply_text("⚠️ Ошибка при проверке ссылки.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    try:
        stats = db.get_stats()
        
        total_checked = stats.get('total_checked', 0) if stats else 0
        total_passed = stats.get('total_passed', 0) if stats else 0
        total_failed = stats.get('total_failed', 0) if stats else 0
        
        await update.message.reply_text(
            f"📊 Детальная статистика:\n"
            f"• Всего проверено: {total_checked}\n"
            f"• Успешно: {total_passed}\n"
            f"• Ошибок: {total_failed}\n"
            f"• Процент успеха: {round((total_passed / total_checked * 100) if total_checked > 0 else 0, 1)}%"
        )
    except Exception as e:
        logger.error(f"Ошибка в stats: {e}")
        await update.message.reply_text("⚠️ Ошибка получения статистики.")

def main():
    """Запуск бота"""
    # Замените на ваш токен
    TOKEN = "8793233752:AAHmCe0bv_rTN9nmMvCW7FuqxRGME2HFFgg"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_link))
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()