
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import BOT_TOKEN, CHECK_DELAY, MAX_RESULTS
from database import Database
from checker import UsernameChecker
from generator import UsernameGenerator

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация БД и генератора
db = Database()
generator = UsernameGenerator()
checker = UsernameChecker(db)

# Состояния пользователей
user_states = {}

# === Обработчики команд ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - приветствие и статистика"""
    user = update.effective_user
    stats = db.get_stats()
    
    # Формируем статистику
    stats_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🤖 Я ищу свободные Telegram-юзернеймы из 5 или 6 букв.\n"
        f"📊 Статистика БД:\n"
        f"• Занятых 5 букв: {stats['taken_5']}\n"
        f"• Занятых 6 букв: {stats['taken_6']}\n"
        f"• Свободных 5 букв: {stats['free_5']}\n"
        f"• Свободных 6 букв: {stats['free_6']}\n"
        f"• Всего проверено: {stats['total_checked']}\n\n"
        f"🔍 Выбери длину ника для поиска:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔍 5 букв", callback_data="search_5"),
            InlineKeyboardButton("🔍 6 букв", callback_data="search_6"),
        ],
        [InlineKeyboardButton("📊 Обновить статистику", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(stats_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "stats":
        stats = db.get_stats()
        stats_text = (
            f"📊 Статистика БД:\n"
            f"• Занятых 5 букв: {stats['taken_5']}\n"
            f"• Занятых 6 букв: {stats['taken_6']}\n"
            f"• Свободных 5 букв: {stats['free_5']}\n"
            f"• Свободных 6 букв: {stats['free_6']}\n"
            f"• Всего проверено: {stats['total_checked']}"
        )
        await query.edit_message_text(stats_text)
        return
    
    if data.startswith("search_"):
        length = int(data.split("_")[1])
        
        # Проверяем, не запущен ли уже поиск для этого пользователя
        if user_id in user_states and user_states[user_id].get("running", False):
            await query.edit_message_text("⏳ Поиск уже запущен! Подожди...")
            return
        
        # Запускаем поиск
        user_states[user_id] = {"running": True, "length": length}
        
        await query.edit_message_text(
            f"🔍 Начинаю поиск свободных {length}-буквенных ников...\n"
            f"⏱ Задержка {CHECK_DELAY} сек между запросами\n"
            f"Это может занять некоторое время..."
        )
        
        try:
            # Генерируем ники и проверяем
            found = []
            checked = 0
            skipped = 0
            
            async for username in generator.generate_readable(length):
                # Проверяем, не отменён ли поиск
                if not user_states.get(user_id, {}).get("running", False):
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="⏹ Поиск остановлен пользователем."
                    )
                    return
                
                # Проверяем в БД
                if db.is_checked(username):
                    skipped += 1
                    continue
                
                # Проверяем через Telegram API
                is_free = await checker.check_username(username)
                checked += 1
                
                if is_free:
                    found.append(username)
                    db.save_free(username)
                    # Отправляем найденный ник сразу
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"✅ Найден свободный ник: @{username}"
                    )
                    if len(found) >= MAX_RESULTS:
                        break
                else:
                    db.save_taken(username)
                
                # Задержка между запросами
                await asyncio.sleep(CHECK_DELAY)
            
            # Итоговое сообщение
            if found:
                result_text = (
                    f"✅ Найдено {len(found)} свободных {length}-буквенных ников!\n\n"
                    f"📊 Проверено новых: {checked}\n"
                    f"♻️ Пропущено из словарей: {skipped}\n"
                    f"📦 Всего в словарях занятых ({length}): {db.count_taken(length)}"
                )
            else:
                result_text = (
                    f"😕 Не найдено новых свободных {length}-буквенных ников.\n\n"
                    f"📊 Проверено новых: {checked}\n"
                    f"♻️ Пропущено из словарей: {skipped}\n"
                    f"📦 Всего в словарях занятых ({length}): {db.count_taken(length)}"
                )
            
            await context.bot.send_message(chat_id=user_id, text=result_text)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка при поиске: {str(e)}"
            )
        finally:
            user_states[user_id] = {"running": False}

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /cancel - остановить поиск"""
    user_id = update.effective_user.id
    if user_id in user_states:
        user_states[user_id]["running"] = False
        await update.message.reply_text("⏹ Поиск остановлен.")
    else:
        await update.message.reply_text("🤔 У тебя нет активного поиска.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /stats - показать статистику"""
    stats = db.get_stats()
    stats_text = (
        f"📊 Статистика БД:\n"
        f"• Занятых 5 букв: {stats['taken_5']}\n"
        f"• Занятых 6 букв: {stats['taken_6']}\n"
        f"• Свободных 5 букв: {stats['free_5']}\n"
        f"• Свободных 6 букв: {stats['free_6']}\n"
        f"• Всего проверено: {stats['total_checked']}"
    )
    await update.message.reply_text(stats_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help - справка"""
    help_text = (
        "🤖 Помощь по боту:\n\n"
        "/start - Главное меню со статистикой\n"
        "/stats - Показать статистику БД\n"
        "/cancel - Остановить текущий поиск\n"
        "/help - Эта справка\n\n"
        "🔍 Используй кнопки в меню для поиска ников.\n"
        "⚠️ Бот использует твой аккаунт для проверки, не злоупотребляй!"
    )
    await update.message.reply_text(help_text)

# === ИНИЦИАЛИЗАЦИЯ БОТА (ИСПРАВЛЕННАЯ ВЕРСИЯ) ===

def main() -> None:
    """Запуск бота"""
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    logger.info("🚀 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()