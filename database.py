import sqlite3
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='usernames.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Создаёт таблицы если их нет"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # таблица занятых юзернеймов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS taken_usernames (
                    username TEXT PRIMARY KEY,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    length INTEGER
                )
            ''')
            
            #таблица свободных юзернеймов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS free_usernames (
                    username TEXT PRIMARY KEY,
                    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    length INTEGER
                )
            ''')
            
            # индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_taken_length ON taken_usernames(length)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_free_length ON free_usernames(length)')
            
            conn.commit()
            logger.info("✅ База данных инициализирована")
    
    def add_taken(self, username: str) -> None:
        """Добавляет занятый юзернейм в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO taken_usernames (username, length) VALUES (?, ?)',
                    (username.upper(), len(username))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка добавления занятого ника: {e}")
    
    def add_taken_batch(self, usernames: List[str]) -> None:
        """Добавляет несколько занятых юзернеймов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                data = [(u.upper(), len(u)) for u in usernames]
                cursor.executemany(
                    'INSERT OR IGNORE INTO taken_usernames (username, length) VALUES (?, ?)',
                    data
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка добавления занятых ников: {e}")
    
    def add_free(self, username: str) -> None:
        """Добавляет свободный юзернейм в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO free_usernames (username, length) VALUES (?, ?)',
                    (username.upper(), len(username))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка добавления свободного ника: {e}")
    
    def add_free_batch(self, usernames: List[str]) -> None:
        """Добавляет несколько свободных юзернеймов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                data = [(u.upper(), len(u)) for u in usernames]
                cursor.executemany(
                    'INSERT OR IGNORE INTO free_usernames (username, length) VALUES (?, ?)',
                    data
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка добавления свободных ников: {e}")
    
    def is_taken(self, username: str) -> bool:
        """Проверяет, есть ли юзернейм в БД занятых"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT 1 FROM taken_usernames WHERE username = ?',
                    (username.upper(),)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ Ошибка проверки занятого ника: {e}")
            return False
    
    def is_free(self, username: str) -> bool:
        """Проверяет, есть ли юзернейм в БД свободных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT 1 FROM free_usernames WHERE username = ?',
                    (username.upper(),)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ Ошибка проверки свободного ника: {e}")
            return False
    
    def get_taken_count(self, length: int = None) -> int:
        """Количество занятых ников (опционально по длине)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if length:
                    cursor.execute('SELECT COUNT(*) FROM taken_usernames WHERE length = ?', (length,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM taken_usernames')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Ошибка подсчёта занятых: {e}")
            return 0
    
    def get_free_count(self, length: int = None) -> int:
        """Количество свободных ников (опционально по длине)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if length:
                    cursor.execute('SELECT COUNT(*) FROM free_usernames WHERE length = ?', (length,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM free_usernames')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Ошибка подсчёта свободных: {e}")
            return 0
    
    def get_all_taken(self, length: int = None) -> Set[str]:
        """Возвращает все занятые ники как множество"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if length:
                    cursor.execute('SELECT username FROM taken_usernames WHERE length = ?', (length,))
                else:
                    cursor.execute('SELECT username FROM taken_usernames')
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"❌ Ошибка получения занятых: {e}")
            return set()
    
    def clear_taken(self) -> None:
        """Очищает таблицу занятых (для отладки)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM taken_usernames')
                conn.commit()
                logger.info("🗑 Таблица занятых очищена")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")
    
    def clear_free(self) -> None:
        """Очищает таблицу свободных (для отладки)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM free_usernames')
                conn.commit()
                logger.info("🗑 Таблица свободных очищена")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")

# Глобальный экземпляр БД
db = Database()