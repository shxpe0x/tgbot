"""Bot initialization and configuration."""
import telebot
import logging
from config import BOT_TOKEN

logger = logging.getLogger(__name__)

def create_bot() -> telebot.TeleBot:
    """Create and configure bot instance."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
    logger.info("Bot instance created successfully")
    
    return bot