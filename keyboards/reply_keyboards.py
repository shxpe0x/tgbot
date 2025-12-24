"""Reply keyboards for the bot."""
from telebot import types

def get_main_menu() -> types.ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_add = types.KeyboardButton('➕ Добавить ДР')
    btn_list = types.KeyboardButton('📋 Список')
    btn_upcoming = types.KeyboardButton('🔔 Ближайшие')
    btn_delete = types.KeyboardButton('🗑️ Удалить')
    
    markup.add(btn_add, btn_list)
    markup.add(btn_upcoming, btn_delete)
    
    return markup