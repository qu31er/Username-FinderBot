import os
import logging
from typing import Set, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DictionaryManager:
    """Управление словарями (текстовые файлы)"""
    
    def __init__(self, words_dir='words'):
        self.words_dir = words_dir
        self._ensure_dir()
        
        # Пути к файлам
        self.forbidden_file = os.path.join(words_dir, 'forbidden.txt')
        self.taken_5_file = os.path.join(words_dir, 'taken_5.txt')
        self.taken_6_file = os.path.join(words_dir, 'taken_6.txt')
        self.free_5_file = os.path.join(words_dir, 'free_5.txt')
        self.free_6_file = os.path.join(words_dir, 'free_6.txt')
        
        # Кэши для быстрого доступа
        self._forbidden_cache = None
        self._taken_cache = {}
        self._free_cache = {}
        
        # Загружаем всё при инициализации
        self.load_all()
    
    def _ensure_dir(self):
        """Создаёт папку для словарей если её нет"""
        if not os.path.exists(self.words_dir):
            os.makedirs(self.words_dir)
            logger.info(f"📁 Создана папка {self.words_dir}")
    
    def _read_file(self, filepath: str) -> Set[str]:
        """Читает файл и возвращает множество строк (в верхнем регистре)"""
        if not os.path.exists(filepath):
            return set()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [line.strip().upper() for line in f if line.strip()]
                return set(lines)
        except Exception as e:
            logger.error(f"❌ Ошибка чтения {filepath}: {e}")
            return set()
    
    def _write_file(self, filepath: str, data: Set[str], append: bool = False) -> None:
        """Записывает множество в файл"""
        try:
            mode = 'a' if append else 'w'
            with open(filepath, mode, encoding='utf-8') as f:
                if append:
                    for item in data:
                        f.write(f"{item.upper()}\n")
                else:
                    f.write('\n'.join(sorted(data)))
                    if data:
                        f.write('\n')
        except Exception as e:
            logger.error(f"❌ Ошибка записи {filepath}: {e}")
    
    def load_all(self):
        """Загружает все словари в кэш"""
        self._forbidden_cache = self._read_file(self.forbidden_file)
        self._taken_cache = {
            5: self._read_file(self.taken_5_file),
            6: self._read_file(self.taken_6_file)
        }
        self._free_cache = {
            5: self._read_file(self.free_5_file),
            6: self._read_file(self.free_6_file)
        }
        logger.info(f"📚 Загружено словарей:")
        logger.info(f"  • Запрещённых: {len(self._forbidden_cache)}")
        logger.info(f"  • Занятых 5: {len(self._taken_cache[5])}")
        logger.info(f"  • Занятых 6: {len(self._taken_cache[6])}")
        logger.info(f"  • Свободных 5: {len(self._free_cache[5])}")
        logger.info(f"  • Свободных 6: {len(self._free_cache[6])}")
    
    # ==================== РАБОТА С ЗАПРЕЩЁННЫМИ ====================
    
    def is_forbidden(self, username: str) -> bool:
        """Проверяет, есть ли ник в списке запрещённых"""
        return username.upper() in self._forbidden_cache
    
    def add_forbidden(self, username: str) -> None:
        """Добавляет ник в список запрещённых"""
        username = username.upper()
        if username not in self._forbidden_cache:
            self._forbidden_cache.add(username)
            self._write_file(self.forbidden_file, {username}, append=True)
            logger.info(f"🚫 Добавлен в запрещённые: {username}")
    
    def get_forbidden_count(self) -> int:
        """Количество запрещённых комбинаций"""
        return len(self._forbidden_cache)
    
    # ==================== РАБОТА С ЗАНЯТЫМИ ====================
    
    def is_taken(self, username: str) -> bool:
        """Проверяет, есть ли ник в списке занятых"""
        username = username.upper()
        length = len(username)
        if length not in (5, 6):
            return False
        return username in self._taken_cache.get(length, set())
    
    def add_taken(self, username: str) -> None:
        """Добавляет ник в список занятых"""
        username = username.upper()
        length = len(username)
        if length not in (5, 6):
            return
        
        if username not in self._taken_cache[length]:
            self._taken_cache[length].add(username)
            filepath = self.taken_5_file if length == 5 else self.taken_6_file
            self._write_file(filepath, {username}, append=True)
            logger.info(f"🔴 Добавлен в занятые ({length}): {username}")
    
    def add_taken_batch(self, usernames: List[str]) -> None:
        """Добавляет несколько ников в занятые"""
        for username in usernames:
            self.add_taken(username)
    
    def get_taken_count(self, length: int = None) -> int:
        """Количество занятых ников"""
        if length:
            return len(self._taken_cache.get(length, set()))
        return sum(len(v) for v in self._taken_cache.values())
    
    def get_all_taken(self, length: int = None) -> Set[str]:
        """Возвращает все занятые ники"""
        if length:
            return self._taken_cache.get(length, set()).copy()
        result = set()
        for v in self._taken_cache.values():
            result.update(v)
        return result
    
    # ==================== РАБОТА СО СВОБОДНЫМИ ====================
    
    def is_free(self, username: str) -> bool:
        """Проверяет, есть ли ник в списке свободных"""
        username = username.upper()
        length = len(username)
        if length not in (5, 6):
            return False
        return username in self._free_cache.get(length, set())
    
    def add_free(self, username: str) -> None:
        """Добавляет ник в список свободных"""
        username = username.upper()
        length = len(username)
        if length not in (5, 6):
            return
        
        if username not in self._free_cache[length]:
            self._free_cache[length].add(username)
            filepath = self.free_5_file if length == 5 else self.free_6_file
            self._write_file(filepath, {username}, append=True)
            logger.info(f"🟢 Добавлен в свободные ({length}): {username}")
    
    def add_free_batch(self, usernames: List[str]) -> None:
        """Добавляет несколько ников в свободные"""
        for username in usernames:
            self.add_free(username)
    
    def get_free_count(self, length: int = None) -> int:
        """Количество свободных ников"""
        if length:
            return len(self._free_cache.get(length, set()))
        return sum(len(v) for v in self._free_cache.values())
    
    def get_all_free(self, length: int = None) -> Set[str]:
        """Возвращает все свободные ники"""
        if length:
            return self._free_cache.get(length, set()).copy()
        result = set()
        for v in self._free_cache.values():
            result.update(v)
        return result
    
    # ==================== СТАТИСТИКА ====================
    
    def get_stats(self) -> dict:
        """Возвращает полную статистику"""
        return {
            'forbidden': self.get_forbidden_count(),
            'taken_5': self.get_taken_count(5),
            'taken_6': self.get_taken_count(6),
            'taken_total': self.get_taken_count(),
            'free_5': self.get_free_count(5),
            'free_6': self.get_free_count(6),
            'free_total': self.get_free_count()
        }
    
    # ==================== ИМПОРТ/ЭКСПОРТ ====================
    
    def export_taken_to_file(self, filename: str = None) -> None:
        """Экспортирует все занятые ники в один файл"""
        if not filename:
            filename = os.path.join(self.words_dir, f'taken_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        all_taken = self.get_all_taken()
        self._write_file(filename, all_taken)
        logger.info(f"📤 Экспортировано {len(all_taken)} занятых ников в {filename}")
    
    def export_free_to_file(self, filename: str = None) -> None:
        """Экспортирует все свободные ники в один файл"""
        if not filename:
            filename = os.path.join(self.words_dir, f'free_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        all_free = self.get_all_free()
        self._write_file(filename, all_free)
        logger.info(f"📤 Экспортировано {len(all_free)} свободных ников в {filename}")

#глобальный экземпляр
dict_manager = DictionaryManager()