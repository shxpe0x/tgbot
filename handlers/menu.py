"""Menu and text button handlers."""
import telebot
from telebot import types
import logging
from handlers.birthdays import cmd_add, cmd_list, cmd_upcoming, cmd_delete

logger = logging.getLogger(__name__)

def register_menu_handlers(bot: telebot.TeleBot):
    """Register handlers for menu button texts."""
    
    @bot.message_handler(func=lambda m: m.text == '➕ Добавить ДР')
    def menu_add(message: types.Message):
        """Handle 'Add Birthday' button."""
        message.text = '/add'
        cmd_add(message)
    
    @bot.message_handler(func=lambda m: m.text == '📋 Список')
    def menu_list(message: types.Message):
        """Handle 'List' button."""
        message.text = '/list'
        cmd_list(message)
    
    @bot.message_handler(func=lambda m: m.text == '🔔 Ближайшие')
    def menu_upcoming(message: types.Message):
        """Handle 'Upcoming' button."""
        message.text = '/upcoming'
        cmd_upcoming(message)
    
    @bot.message_handler(func=lambda m: m.text == '🗑️ Удалить')
    def menu_delete(message: types.Message):
        """Handle 'Delete' button."""
        message.text = '/delete'
        cmd_delete(message)