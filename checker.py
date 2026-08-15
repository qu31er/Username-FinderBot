from telethon import TelegramClient, errors
import asyncio
from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME, CHECK_DELAY
from database import db

# глобальный клиент
_client = None

async def init_client():
    """Инициализация клиента Telethon"""
    global _client
    if _client is None:
        _client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await _client.start(phone=PHONE_NUMBER)
        print("✅ Клиент Telethon инициализирован")
    return _client

async def get_client():
    """Получить клиент (инициализирует если нужно)"""
    if _client is None:
        await init_client()
    return _client

async def check_username(username):
    """
    Проверяет, свободен ли username.
    Сначала проверяет в БД.
    Возвращает True, если свободен.
    """
    username = username.upper()
    
    # 1. Проверяем в БД
    if db.is_taken(username):
        print(f"⏭ Пропускаем (уже в БД): {username}")
        return False
    
    if db.is_free(username):
        print(f"✅ Уже найден как свободный: {username}")
        return True
    
    # 2. Проверяем через API
    client = await get_client()
    
    try:
        await client.get_entity(f'@{username}')
        # Найден -> занят
        db.add_taken(username)
        print(f"❌ Занят (сохранён в БД): {username}")
        return False
    except ValueError as e:
        if 'No user has "username" as username' in str(e):
            # Свободен
            db.add_free(username)
            print(f"✅ СВОБОДЕН (сохранён в БД): {username}")
            return True
        else:
            return False
    except errors.FloodWaitError as e:
        print(f"⏳ Flood wait {e.seconds} секунд")
        await asyncio.sleep(e.seconds)
        return await check_username(username)
    except Exception as e:
        print(f'❌ Ошибка при проверке {username}: {e}')
        return False

async def check_batch(usernames):
    """
    Проверяет список username'ов.
    Возвращает список свободных.
    Фильтрует уже проверенные из БД.
    """
    free = []
    total = len(usernames)
    
    # Фильтруем те, что уже в БД
    to_check = []
    for username in usernames:
        username = username.upper()
        if db.is_taken(username):
            print(f"⏭ Пропускаем (БД): {username}")
        elif db.is_free(username):
            free.append(username)
            print(f" Из БД (свободный): {username}")
        else:
            to_check.append(username)
    
    print(f" Всего: {total}, из БД пропущено: {total - len(to_check)}, к проверке: {len(to_check)}")
    
    # Проверяем новые
    for i, username in enumerate(to_check):
        if await check_username(username):
            free.append(username)
        
        # Прогресс
        if (i + 1) % 10 == 0:
            print(f" Проверено: {i+1}/{len(to_check)}")
        
        # Задержка
        await asyncio.sleep(CHECK_DELAY)
    
    return free

async def close_client():
    """Закрывает клиент"""
    global _client
    if _client:
        await _client.disconnect()
        _client = None
        print(" Клиент закрыт")