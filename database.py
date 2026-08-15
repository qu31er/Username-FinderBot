import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='bot.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица проверок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    url TEXT,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица статистики
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value INTEGER DEFAULT 0
                )
            ''')
            
            # Инициализация ключей статистики
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('total_checked', 0))
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('total_passed', 0))
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('total_failed', 0))
            
            conn.commit()
            conn.close()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def update_stats(self, user_id, url, status):
        """Обновление статистики"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Добавляем запись о проверке
            cursor.execute(
                'INSERT INTO checks (user_id, url, status) VALUES (?, ?, ?)',
                (user_id, url, status)
            )
            
            # Обновляем общий счетчик
            cursor.execute('UPDATE stats SET value = value + 1 WHERE key = ?', ('total_checked',))
            
            # Обновляем статус
            if status == 'passed':
                cursor.execute('UPDATE stats SET value = value + 1 WHERE key = ?', ('total_passed',))
            elif status == 'failed':
                cursor.execute('UPDATE stats SET value = value + 1 WHERE key = ?', ('total_failed',))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики: {e}")
            return False
    
    def get_stats(self):
        """Получение статистики"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM stats')
            rows = cursor.fetchall()
            conn.close()
            
            stats = {}
            for key, value in rows:
                stats[key] = value
            
            # Гарантируем наличие всех ключей
            stats.setdefault('total_checked', 0)
            stats.setdefault('total_passed', 0)
            stats.setdefault('total_failed', 0)
            
            return stats
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {'total_checked': 0, 'total_passed': 0, 'total_failed': 0}
    
    def get_total_checked(self):
        """Получить общее количество проверок"""
        return self.get_stats().get('total_checked', 0)
    
    def get_total_passed(self):
        """Получить количество успешных проверок"""
        return self.get_stats().get('total_passed', 0)
    
    def get_total_failed(self):
        """Получить количество неудачных проверок"""
        return self.get_stats().get('total_failed', 0)