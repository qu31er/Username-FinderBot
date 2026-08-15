import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, MAX_RESULTS, BATCH_SIZE
from forbidden import is_forbidden
from generator import generate_batch
from checker import init_client, check_batch, close_client
import checker

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище сессий пользователей
user_sessions = {}

#КНОПКИ

def get_main_keyboard():
    """Главное меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("🔍 Найти 5 букв", callback_data='find_5')],
        [InlineKeyboardButton("🔍 Найти 6 букв", callback_data='find_6')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stop_keyboard():
    """Кнопка остановки поиска"""
    keyboard = [[InlineKeyboardButton("⏹ Остановить поиск", callback_data='stop')]]
    return InlineKeyboardMarkup(keyboard)

# ОБРАБОТЧИКИ 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🤖 *Бот для поиска свободных юзернеймов*\n\n"
        "Я ищу свободные ники из 5 или 6 букв.\n"
        "Выбери длину и я начну поиск!\n\n"
        "⚠️ *Внимание:* Поиск может занять несколько минут.",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == 'find_5':
        await start_search(query, 5)
    elif data == 'find_6':
        await start_search(query, 6)
    elif data == 'stats':
        await show_stats(query)
    elif data == 'help':
        await show_help(query)
    elif data == 'stop':
        await stop_search(query)

async def start_search(query, length):
    """Запуск поиска"""
    user_id = query.from_user.id
    
    # Если уже идёт поиск
    if user_id in user_sessions and user_sessions[user_id].get('running', False):
        await query.edit_message_text(
            f"⏳ Уже идёт поиск для {length} букв!\n"
            f"Найдено: {len(user_sessions[user_id].get('found', []))} ников",
            reply_markup=get_stop_keyboard()
        )
        return
    
    # инициализируем сессию
    user_sessions[user_id] = {
        'running': True,
        'found': [],
        'length': length,
        'total_checked': 0
    }
    
    await query.edit_message_text(
        f"🔍 Начинаю поиск *{length}-буквенных* юзернеймов...\n\n"
        f"⏳ Это может занять несколько минут.\n"
        f"Я проверяю только читаемые комбинации и фильтрую очевидные.",
        reply_markup=get_stop_keyboard(),
        parse_mode='Markdown'
    )
    
    #запускаем поиск в фоне
    asyncio.create_task(run_search(user_id, length))

async def run_search(user_id, length):
    """Фоновый процесс поиска"""
    try:
        #инициализируем клиент Telethon
        client = await init_client()
        
        #генерируем комбинации
        total_checked = 0
        found_free = []
        
        while user_sessions[user_id].get('running', False):
            # Генерируем пачку
            batch = generate_batch(length, count=BATCH_SIZE, readable=True)
            
            # Фильтруем запретные
            filtered = [u for u in batch if not is_forbidden(u)]
            
            # Проверяем
            free = await check_batch(filtered)
            
            # Сохраняем результаты
            found_free.extend(free)
            total_checked += len(filtered)
            
            user_sessions[user_id]['found'] = found_free
            user_sessions[user_id]['total_checked'] = total_checked
            
            # Если нашли достаточно — останавливаем
            if len(found_free) >= MAX_RESULTS:
                user_sessions[user_id]['running'] = False
                break
        
        # Отправляем результаты
        await send_results(user_id)
        
        # Закрываем клиент
        await close_client()
        
    except Exception as e:
        logger.error(f"Ошибка в run_search: {e}")
        user_sessions[user_id]['running'] = False

async def send_results(user_id):
    """Отправка результатов пользователю"""
    session = user_sessions.get(user_id, {})
    found = session.get('found', [])
    total = session.get('total_checked', 0)
    length = session.get('length', 0)
    
    if found:
        # Формируем список ников
        nicks = '\n'.join([f"• @{nick}" for nick in found[:MAX_RESULTS]])
        
        message = (
            f"✅ *Найдено {len(found)} свободных {length}-буквенных ников!*\n\n"
            f"{nicks}\n\n"
            f"📊 Всего проверено: {total}\n"
            f"⏱ Время: ~{total * 2 // 60} минут\n\n"
            f"💡 Чтобы продолжить поиск, нажми /start"
        )
    else:
        message = (
            f"😔 *Свободных {length}-буквенных ников не найдено*\n\n"
            f"📊 Проверено: {total} комбинаций\n\n"
            f"💡 Попробуй ещё раз или измени длину"
        )
    
    #отправляем в личку
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение: {e}")

async def show_stats(query):
    """Показать статистику"""
    user_id = query.from_user.id
    session = user_sessions.get(user_id, {})
    
    if session.get('running', False):
        found = len(session.get('found', []))
        checked = session.get('total_checked', 0)
        length = session.get('length', 0)
        
        await query.edit_message_text(
            f"📊 *Текущая статистика*\n\n"
            f"Длина: {length} букв\n"
            f"Проверено: {checked}\n"
            f"Найдено свободных: {found}\n"
            f"Статус: 🔄 Идёт поиск",
            reply_markup=get_stop_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "📊 *Статистика*\n\n"
            "Нет активного поиска.\n"
            "Нажми /start чтобы начать!",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

async def show_help(query):
    """Показать помощь"""
    await query.edit_message_text(
        "❓ *Помощь*\n\n"
        "🤖 Я ищу свободные юзернеймы из 5 или 6 букв.\n\n"
        "🔍 *Как это работает:*\n"
        "1. Выбери длину ников (5 или 6 букв)\n"
        "2. Я генерирую читаемые комбинации\n"
        "3. Фильтрую очевидные (слова, повторы)\n"
        "4. Проверяю каждый через Telegram API\n"
        "5. Отправляю найденные свободные ники\n\n"
        "⏱ *Время:* ~2 секунды на проверку\n"
        "📊 *Лимит:* 10 ников за раз\n\n"
        "⚠️ *Важно:* Не злоупотребляй, чтобы не заблокировали!",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def stop_search(query):
    """Остановить поиск"""
    user_id = query.from_user.id
    
    if user_id in user_sessions:
        user_sessions[user_id]['running'] = False
        
        await query.edit_message_text(
            "⏹ *Поиск остановлен*\n\n"
            "Нажми /start чтобы начать снова.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        await query.edit_message_text(
            "Нет активного поиска.",
            reply_markup=get_main_keyboard()
        )

#ЗАПУСК

async def main():
    """Запуск бота"""
    #создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    #добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    #запускаем
    logger.info("🚀 Бот запущен!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())