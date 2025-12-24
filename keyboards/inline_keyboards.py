"""Inline keyboards for the bot."""
from telebot import types

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
    
    return markup