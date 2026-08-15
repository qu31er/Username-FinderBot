import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, MAX_RESULTS, BATCH_SIZE
from forbidden import is_forbidden
from generator import generate_batch
from checker import init_client, check_batch, close_client
from database import db

# включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# хранилище сессий
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
        "📊 *В БД уже:*\n"
        f"• Занятых: {db.get_taken_count()}\n"
        f"• Свободных: {db.get_free_count()}\n\n"
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
        'total_checked': 0,
        'skipped_db': 0
    }
    
    await query.edit_message_text(
        f"🔍 Начинаю поиск *{length}-буквенных* юзернеймов...\n\n"
        f"⏳ Это может занять несколько минут.\n"
        f"📊 В БД уже есть {db.get_taken_count(length)} занятых ников этой длины.\n"
        f"♻️ Они будут пропущены автоматически.",
        reply_markup=get_stop_keyboard(),
        parse_mode='Markdown'
    )
    
    # запускаем поиск в фоне
    asyncio.create_task(run_search(user_id, length))

async def run_search(user_id, length):
    """Фоновый процесс поиска"""
    try:
        # инициализируем клиент Telethon
        await init_client()
        
        total_checked = 0
        found_free = []
        skipped = 0
        
        # загружаем уже проверенные из БД
        taken_set = db.get_all_taken(length)
        print(f"📊 Загружено {len(taken_set)} занятых ников из БД")
        
        while user_sessions[user_id].get('running', False):
            # генерируем пачку
            batch = generate_batch(length, count=BATCH_SIZE, readable=True)
            
            # фильтруем запретные
            filtered = [u for u in batch if not is_forbidden(u)]
            
            # убираем те, что уже в БД
            to_check = [u for u in filtered if u not in taken_set]
            skipped += len(filtered) - len(to_check)
            
            if not to_check:
                print("⏭ Все сгенерированные ники уже в БД, генерируем новые...")
                continue
            
            # проверяем
            free = await check_batch(to_check)
           
            # добавляем проверенные в БД (check_batch уже сохраняет)
            found_free.extend(free)
            total_checked += len(to_check)
            
            # обновляем сессию
            user_sessions[user_id]['found'] = found_free
            user_sessions[user_id]['total_checked'] = total_checked
            user_sessions[user_id]['skipped_db'] = skipped
            
            # если нашли достаточно — останавливаем
            if len(found_free) >= MAX_RESULTS:
                user_sessions[user_id]['running'] = False
                break
        
        # отправляем результаты
        await send_results(user_id)
        
        # закрываем клиент
        await close_client()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в run_search: {e}")
        user_sessions[user_id]['running'] = False

async def send_results(user_id):
    """Отправка результатов пользователю"""
    session = user_sessions.get(user_id, {})
    found = session.get('found', [])
    total = session.get('total_checked', 0)
    length = session.get('length', 0)
    skipped = session.get('skipped_db', 0)
    
    if found:
        nicks = '\n'.join([f"• @{nick}" for nick in found[:MAX_RESULTS]])
        
        message = (
            f"✅ *Найдено {len(found)} свободных {length}-буквенных ников!*\n\n"
            f"{nicks}\n\n"
            f"📊 Всего проверено: {total}\n"
            f"♻️ Пропущено из БД: {skipped}\n"
            f"📦 Всего в БД занятых: {db.get_taken_count(length)}\n\n"
            f"💡 Чтобы продолжить поиск, нажми /start"
        )
    else:
        message = (
            f"😔 *Свободных {length}-буквенных ников не найдено*\n\n"
            f"📊 Проверено новых: {total}\n"
            f"♻️ Пропущено из БД: {skipped}\n"
            f"📦 Всего в БД занятых: {db.get_taken_count(length)}\n\n"
            f"💡 Попробуй ещё раз или измени длину"
        )
    
    # отправляем в личку
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
        logger.error(f"❌ Не удалось отправить сообщение: {e}")

async def show_stats(query):
    """Показать статистику"""
    user_id = query.from_user.id
    
    # статистика БД
    taken_5 = db.get_taken_count(5)
    taken_6 = db.get_taken_count(6)
    free_5 = db.get_free_count(5)
    free_6 = db.get_free_count(6)
    
    # статистика сессии
    session = user_sessions.get(user_id, {})
    
    stats = (
        f"📊 *Статистика базы данных*\n\n"
        f"🔴 *Занятых ников:*\n"
        f"  • 5 букв: {taken_5}\n"
        f"  • 6 букв: {taken_6}\n"
        f"  • Всего: {taken_5 + taken_6}\n\n"
        f"🟢 *Свободных ников:*\n"
        f"  • 5 букв: {free_5}\n"
        f"  • 6 букв: {free_6}\n"
        f"  • Всего: {free_5 + free_6}\n"
    )
    
    if session.get('running', False):
        stats += (
            f"\n🔄 *Текущий поиск:*\n"
            f"  • Проверено: {session.get('total_checked', 0)}\n"
            f"  • Найдено: {len(session.get('found', []))}\n"
            f"  • Пропущено из БД: {session.get('skipped_db', 0)}"
        )
    
    await query.edit_message_text(
        stats,
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
        "5. Сохраняю все проверенные в БД\n"
        "6. Отправляю найденные свободные ники\n\n"
        "💾 *База данных:*\n"
        "• Все занятые ники сохраняются\n"
        "• При следующем поиске они пропускаются\n"
        "• Это ускоряет поиск в разы!\n\n"
        "⏱ *Время:* ~2 секунды на проверку\n"
        "📊 *Лимит:* 10 ников за раз",
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
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🚀 Бот запущен!")
    logger.info(f"📊 В БД: занятых {db.get_taken_count()}, свободных {db.get_free_count()}")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())