from telethon import TelegramClient, errors
import asyncio
from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME, CHECK_DELAY

#глобальный клиент
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
    Возвращает True, если свободен.
    """
    client = await get_client()
    
    try:
        # получем информацию о юзернейме
        await client.get_entity(f'@{username}')
        return False  # Найден -> занят
    except ValueError as e:
        if 'No user has "username" as username' in str(e):
            return True  # Не найден -> свободен
        else:
            return False
    except errors.FloodWaitError as e:
        # Если телеграм просит подождать
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
    """
    free = []
    total = len(usernames)
    
    for i, username in enumerate(usernames):
        if await check_username(username):
            free.append(username)
            print(f"✅ Найден свободный: @{username}")
        
        # Прогресс
        if (i + 1) % 10 == 0:
            print(f"📊 Проверено: {i+1}/{total}")
        
        #задержка между запросами
        await asyncio.sleep(CHECK_DELAY)
    
    return free

async def close_client():
    """Закрывает клиент"""
    global _client
    if _client:
        await _client.disconnect()
        _client = None
        print("🔌 Клиент закрыт")