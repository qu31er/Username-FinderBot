import sqlite3
import logging
from typing import List, Set

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='usernames.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS taken_usernames (
                    username TEXT PRIMARY KEY,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    length INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS free_usernames (
                    username TEXT PRIMARY KEY,
                    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    length INTEGER
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_taken_length ON taken_usernames(length)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_free_length ON free_usernames(length)')
            conn.commit()
            logger.info("✅ База данных инициализирована")
    
    def add_taken(self, username: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO taken_usernames (username, length) VALUES (?, ?)',
                (username.upper(), len(username))
            )
            conn.commit()
    
    def add_taken_batch(self, usernames: List[str]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            data = [(u.upper(), len(u)) for u in usernames]
            cursor.executemany(
                'INSERT OR IGNORE INTO taken_usernames (username, length) VALUES (?, ?)',
                data
            )
            conn.commit()
    
    def add_free(self, username: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO free_usernames (username, length) VALUES (?, ?)',
                (username.upper(), len(username))
            )
            conn.commit()
    
    def add_free_batch(self, usernames: List[str]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            data = [(u.upper(), len(u)) for u in usernames]
            cursor.executemany(
                'INSERT OR IGNORE INTO free_usernames (username, length) VALUES (?, ?)',
                data
            )
            conn.commit()
    
    def is_taken(self, username: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM taken_usernames WHERE username = ?',
                (username.upper(),)
            )
            return cursor.fetchone() is not None
    
    def is_free(self, username: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM free_usernames WHERE username = ?',
                (username.upper(),)
            )
            return cursor.fetchone() is not None
    
    def get_taken_count(self, length: int = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if length:
                cursor.execute('SELECT COUNT(*) FROM taken_usernames WHERE length = ?', (length,))
            else:
                cursor.execute('SELECT COUNT(*) FROM taken_usernames')
            return cursor.fetchone()[0]
    
    def get_free_count(self, length: int = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if length:
                cursor.execute('SELECT COUNT(*) FROM free_usernames WHERE length = ?', (length,))
            else:
                cursor.execute('SELECT COUNT(*) FROM free_usernames')
            return cursor.fetchone()[0]
    
    def get_all_taken(self, length: int = None) -> Set[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if length:
                cursor.execute('SELECT username FROM taken_usernames WHERE length = ?', (length,))
            else:
                cursor.execute('SELECT username FROM taken_usernames')
            return {row[0] for row in cursor.fetchall()}
    
    def get_all_free(self, length: int = None) -> Set[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if length:
                cursor.execute('SELECT username FROM free_usernames WHERE length = ?', (length,))
            else:
                cursor.execute('SELECT username FROM free_usernames')
            return {row[0] for row in cursor.fetchall()}
    
    def get_stats(self) -> dict:
        return {
            'taken_5': self.get_taken_count(5),
            'taken_6': self.get_taken_count(6),
            'taken_total': self.get_taken_count(),
            'free_5': self.get_free_count(5),
            'free_6': self.get_free_count(6),
            'free_total': self.get_free_count()
        }

db = Database()