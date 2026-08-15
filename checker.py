"""
Проверка username через Telegram API
"""
import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import UsernameNotOccupiedError

from config import API_ID, API_HASH, PHONE_NUMBER

logger = logging.getLogger(__name__)

class UsernameChecker:
    """Класс для проверки username"""
    
    def __init__(self, db):
        self.db = db
        self.client = None
    
    async def get_client(self):
        """Получить или создать клиент Telethon"""
        if self.client is None:
            self.client = TelegramClient('session', API_ID, API_HASH)
            await self.client.start(phone=PHONE_NUMBER)
            logger.info("✅ Telethon клиент подключён")
        return self.client
    
    async def check_username(self, username: str) -> bool:
        """
        Проверяет, свободен ли username
        
        Returns:
            True - если свободен, False - если занят
        """
        try:
            client = await self.get_client()
            
            # Пробуем получить информацию о пользователе
            entity = await client.get_entity(f"@{username}")
            
            # Если мы здесь - значит пользователь существует
            logger.debug(f"@{username} - занят")
            return False
            
        except UsernameNotOccupiedError:
            # Username свободен
            logger.debug(f"@{username} - СВОБОДЕН!")
            return True
            
        except ValueError as e:
            # Неверный формат username
            logger.warning(f"Ошибка формата @{username}: {e}")
            return False
            
        except Exception as e:
            # Другие ошибки (например, флуд)
            logger.error(f"Ошибка проверки @{username}: {e}")
            await asyncio.sleep(5)  # Ждём перед повторной попыткой
            return False
    
    async def close(self):
        """Закрыть клиент"""
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Telethon клиент отключён")