import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='bot.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value INTEGER DEFAULT 0
                )
            ''')
            
            # Инициализация ключей
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('total_checked', 0))
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('found_5', 0))
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('found_6', 0))
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('checked_5', 0))
            cursor.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('checked_6', 0))
            
            conn.commit()
            conn.close()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
    
    def update_stats_5(self, checked, found):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE stats SET value = value + ? WHERE key = ?', (checked, 'checked_5'))
            cursor.execute('UPDATE stats SET value = value + ? WHERE key = ?', (found, 'found_5'))
            cursor.execute('UPDATE stats SET value = value + ? WHERE key = ?', (checked, 'total_checked'))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка обновления: {e}")
    
    def update_stats_6(self, checked, found):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE stats SET value = value + ? WHERE key = ?', (checked, 'checked_6'))
            cursor.execute('UPDATE stats SET value = value + ? WHERE key = ?', (found, 'found_6'))
            cursor.execute('UPDATE stats SET value = value + ? WHERE key = ?', (checked, 'total_checked'))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка обновления: {e}")
    
    def get_stats(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM stats')
            rows = cursor.fetchall()
            conn.close()
            
            stats = {}
            for key, value in rows:
                stats[key] = value
            
            stats.setdefault('total_checked', 0)
            stats.setdefault('found_5', 0)
            stats.setdefault('found_6', 0)
            stats.setdefault('checked_5', 0)
            stats.setdefault('checked_6', 0)
            
            return stats
        except Exception as e:
            logger.error(f"❌ Ошибка получения: {e}")
            return {'total_checked': 0, 'found_5': 0, 'found_6': 0, 'checked_5': 0, 'checked_6': 0}