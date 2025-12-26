"""Reply keyboards for the bot."""
from telebot import types

def get_main_menu() -> types.ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_add = types.KeyboardButton('➕ Добавить')
    btn_list = types.KeyboardButton('📋 Список')
    btn_upcoming = types.KeyboardButton('🔔 Ближайшие')
    btn_delete = types.KeyboardButton('🗑️ Удалить')
    btn_sdr = types.KeyboardButton('С днем рождения')
    
    markup.add(btn_add, btn_list)
    markup.add(btn_upcoming, btn_delete)
    markup.add(btn_sdr)
    
    return markup

def get_cancel_keyboard() -> types.ReplyKeyboardMarkup:
    """Get cancel keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cancel = types.KeyboardButton('❌ Отмена')
    markup.add(btn_cancel)
    return markup