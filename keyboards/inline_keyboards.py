"""Inline keyboards for the bot."""
from telebot import types

def get_main_menu() -> types.InlineKeyboardMarkup:
    """Get main inline menu with 4 buttons."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_add = types.InlineKeyboardButton('➕ Добавить ДР', callback_data='menu_add')
    btn_list = types.InlineKeyboardButton('📋 Список', callback_data='menu_list')
    btn_upcoming = types.InlineKeyboardButton('🔔 Ближайшие', callback_data='menu_upcoming')
    btn_delete = types.InlineKeyboardButton('🗑️ Удалить', callback_data='menu_delete')
    
    markup.add(btn_add, btn_list)
    markup.add(btn_upcoming, btn_delete)
    
    return markup

def get_back_to_menu() -> types.InlineKeyboardMarkup:
    """Get back to menu button."""
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton('🔙 Главное меню', callback_data='back_to_menu')
    markup.add(btn_back)
    return markup

def get_cancel_keyboard() -> types.InlineKeyboardMarkup:
    """Get cancel keyboard."""
    markup = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton('❌ Отменить', callback_data='cancel')
    markup.add(btn_cancel)
    return markup

def get_confirm_keyboard() -> types.InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_confirm = types.InlineKeyboardButton('✅ Подтвердить', callback_data='confirm_add')
    btn_cancel = types.InlineKeyboardButton('❌ Отмена', callback_data='cancel_add')
    markup.add(btn_confirm, btn_cancel)
    return markup

def get_delete_keyboard(birthdays: list) -> types.InlineKeyboardMarkup:
    """Get delete keyboard with birthday list."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for bd in birthdays:
        date_str = bd['birth_date'].strftime('%d.%m')
        btn_text = f"🗑️ {bd['friend_name']} - {date_str}"
        btn = types.InlineKeyboardButton(btn_text, callback_data=f"delete_{bd['id']}")
        markup.add(btn)
    
    # Back button
    btn_back = types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_menu')
    markup.add(btn_back)
    
    return markup