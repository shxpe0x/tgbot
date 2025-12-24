"""Basic command handlers."""
import telebot
from telebot import types
import logging
from config import MESSAGES
from keyboards.reply_keyboards import get_main_menu
from database.models import UserDB
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

def register_command_handlers(bot: telebot.TeleBot):
    """Register all command handlers."""
    
    @bot.message_handler(commands=['start'])
    @rate_limit(seconds=3)
    def cmd_start(message: types.Message):
        """Handle /start command."""
        try:
            # Create or get user
            UserDB.create_or_get(
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )
            
            bot.send_message(
                message.chat.id,
                MESSAGES['start'],
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
            logger.info(f"User {message.from_user.id} started bot")
        except Exception as e:
            logger.error(f"Error in cmd_start: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.message_handler(commands=['help'])
    @rate_limit(seconds=2)
    def cmd_help(message: types.Message):
        """Handle /help command."""
        try:
            bot.send_message(
                message.chat.id,
                MESSAGES['help'],
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in cmd_help: {e}")
            bot.reply_to(message, MESSAGES['error'])