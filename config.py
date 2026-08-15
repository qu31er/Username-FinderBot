import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

#BOT
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")

#MTProto API
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

if not API_ID or not API_HASH or not PHONE_NUMBER:
    raise ValueError("❌ API_ID, API_HASH или PHONE_NUMBER не найдены в переменных окружения!")

API_ID = int(API_ID)

#НАСТРОЙКИ
CHECK_DELAY = int(os.getenv('CHECK_DELAY', 2))
MAX_RESULTS = int(os.getenv('MAX_RESULTS', 10))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))

#ФАЙЛ СЕССИИ
SESSION_NAME = 'user_session'