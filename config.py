"""Configuration module for the bot."""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'bot_user'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'birthdays_db'),
    'pool_size': int(os.getenv('DB_POOL_SIZE', 5))
}

# Notification Settings
NOTIFICATION_TIME = {
    'hour': int(os.getenv('NOTIFICATION_HOUR', 9)),
    'minute': int(os.getenv('NOTIFICATION_MINUTE', 0))
}

# Bot Messages
MESSAGES = {
    'start': '👋 Привет! Я бот-напоминалка дней рождений твоих друзей!\n\nИспользуй меню ниже для управления.',
    'help': '''📖 <b>Доступные команды:</b>\n
/start - Запуск бота
/add - Добавить день рождения
/list - Показать все дни рождения
/upcoming - Ближайшие дни рождения
/delete - Удалить запись
/help - Показать эту справку''',
    'error': '❌ Произошла ошибка. Попробуй еще раз.',
    'cancel': '❌ Операция отменена.'
}