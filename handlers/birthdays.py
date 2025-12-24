"""Birthday-related handlers."""
import telebot
from telebot import types
import logging
from datetime import datetime, date
from database.models import UserDB, BirthdayDB
from keyboards.inline_keyboards import (
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_delete_keyboard
)
from config import MESSAGES
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# User states for multi-step dialogs
user_states = {}
user_data = {}

# Store bot instance
_bot = None

def _get_bot():
    """Get bot instance."""
    return _bot

def cmd_add(message: types.Message):
    """Start adding birthday process."""
    bot = _get_bot()
    try:
        user_states[message.chat.id] = 'waiting_name'
        bot.send_message(
            message.chat.id,
            '👤 <b>Введи имя друга:</b>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in cmd_add: {e}")
        bot.reply_to(message, MESSAGES['error'])

def cmd_list(message: types.Message):
    """Show all birthdays."""
    bot = _get_bot()
    try:
        user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
        birthdays = BirthdayDB.get_all(user_id)
        
        if not birthdays:
            bot.send_message(
                message.chat.id,
                '📅 <b>У тебя еще нет сохраненных дней рождения.</b>\n\nИспользуй /add чтобы добавить первый!',
                parse_mode='HTML'
            )
            return
        
        text = '🎉 <b>Список дней рождения:</b>\n\n'
        
        for bd in birthdays:
            date_obj = bd['birth_date']
            date_str = date_obj.strftime('%d.%m')
            
            text += f'👤 <b>{bd["friend_name"]}</b> - {date_str}'
            
            if bd['birth_year']:
                age = datetime.now().year - bd['birth_year']
                text += f' ({age} лет)'
            
            text += '\n'
        
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in cmd_list: {e}")
        bot.reply_to(message, MESSAGES['error'])

def cmd_upcoming(message: types.Message):
    """Show upcoming birthdays."""
    bot = _get_bot()
    try:
        user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
        birthdays = BirthdayDB.get_upcoming(user_id, days=30)
        
        if not birthdays:
            bot.send_message(
                message.chat.id,
                '📅 <b>В ближайшие 30 дней нет дней рождения.</b>',
                parse_mode='HTML'
            )
            return
        
        text = '🔔 <b>Ближайшие дни рождения:</b>\n\n'
        
        for bd in birthdays:
            date_obj = bd['birth_date']
            date_str = date_obj.strftime('%d.%m')
            
            # Calculate days until birthday
            today = datetime.now().date()
            this_year_bd = date(today.year, date_obj.month, date_obj.day)
            if this_year_bd < today:
                this_year_bd = date(today.year + 1, date_obj.month, date_obj.day)
            days_left = (this_year_bd - today).days
            
            text += f'👤 <b>{bd["friend_name"]}</b> - {date_str}'
            
            if days_left == 0:
                text += ' 🎉 <b>СЕГОДНЯ!</b>'
            elif days_left == 1:
                text += ' (завтра)'
            else:
                text += f' (через {days_left} дн.)'
            
            text += '\n'
        
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in cmd_upcoming: {e}")
        bot.reply_to(message, MESSAGES['error'])

def cmd_delete(message: types.Message):
    """Start delete process."""
    bot = _get_bot()
    try:
        user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
        birthdays = BirthdayDB.get_all(user_id)
        
        if not birthdays:
            bot.send_message(
                message.chat.id,
                '📅 <b>У тебя нет сохраненных дней рождения.</b>',
                parse_mode='HTML'
            )
            return
        
        bot.send_message(
            message.chat.id,
            '🗑️ <b>Выбери день рождения для удаления:</b>',
            reply_markup=get_delete_keyboard(birthdays),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in cmd_delete: {e}")
        bot.reply_to(message, MESSAGES['error'])

def register_birthday_handlers(bot: telebot.TeleBot):
    """Register all birthday handlers."""
    global _bot
    _bot = bot
    
    @bot.message_handler(commands=['add'])
    @rate_limit(seconds=2)
    def handle_add_command(message: types.Message):
        cmd_add(message)
    
    # Text button handlers - must come BEFORE state handlers
    @bot.message_handler(func=lambda m: m.text in ['➕ Добавить ДР', '📋 Список', '🔔 Ближайшие', '🗑️ Удалить'])
    def handle_menu_buttons(message: types.Message):
        """Handle reply keyboard button presses."""
        # Skip if in state (to avoid conflicts)
        if message.chat.id in user_states:
            return
            
        if message.text == '➕ Добавить ДР':
            cmd_add(message)
        elif message.text == '📋 Список':
            cmd_list(message)
        elif message.text == '🔔 Ближайшие':
            cmd_upcoming(message)
        elif message.text == '🗑️ Удалить':
            cmd_delete(message)
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_name')
    def get_name(message: types.Message):
        """Get friend's name."""
        try:
            if message.text.startswith('/'):
                return
            
            user_data[message.chat.id] = {'name': message.text}
            user_states[message.chat.id] = 'waiting_date'
            
            bot.send_message(
                message.chat.id,
                '📅 <b>Введи дату рождения</b> (формат: ДД.ММ.ГГГГ или ДД.ММ):\n\nПример: <code>25.12.2000</code> или <code>25.12</code>',
                reply_markup=get_cancel_keyboard(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in get_name: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_date')
    def get_date(message: types.Message):
        """Get birthday date."""
        try:
            if message.text.startswith('/'):
                return
            
            # Parse date
            date_text = message.text.strip()
            birth_date = None
            birth_year = None
            
            # Try different formats
            for fmt in ['%d.%m.%Y', '%d.%m']:
                try:
                    parsed = datetime.strptime(date_text, fmt)
                    if fmt == '%d.%m.%Y':
                        birth_year = parsed.year
                        birth_date = parsed.date()
                    else:
                        # No year provided, use current year
                        birth_date = date(datetime.now().year, parsed.month, parsed.day)
                    break
                except ValueError:
                    continue
            
            if not birth_date:
                bot.send_message(
                    message.chat.id,
                    '❌ Неверный формат даты. Используй формат ДД.ММ.ГГГГ или ДД.ММ'
                )
                return
            
            user_data[message.chat.id]['birth_date'] = birth_date
            user_data[message.chat.id]['birth_year'] = birth_year
            
            # Show confirmation
            name = user_data[message.chat.id]['name']
            date_str = birth_date.strftime('%d.%m.%Y') if birth_year else birth_date.strftime('%d.%m')
            
            confirm_text = f'✅ <b>Подтверди данные:</b>\n\n'
            confirm_text += f'👤 Имя: <b>{name}</b>\n'
            confirm_text += f'📅 Дата: <b>{date_str}</b>'
            
            if birth_year:
                age = datetime.now().year - birth_year
                confirm_text += f'\n🎂 Возраст: <b>{age} лет</b>'
            
            user_states[message.chat.id] = 'waiting_confirmation'
            
            bot.send_message(
                message.chat.id,
                confirm_text,
                reply_markup=get_confirm_keyboard(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in get_date: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.callback_query_handler(func=lambda call: call.data in ['confirm_add', 'cancel_add'])
    def handle_confirmation(call: types.CallbackQuery):
        """Handle confirmation callback."""
        try:
            if call.data == 'confirm_add':
                # Save to database
                user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
                data = user_data.get(call.message.chat.id, {})
                
                BirthdayDB.add(
                    user_id=user_id,
                    friend_name=data['name'],
                    birth_date=data['birth_date'],
                    birth_year=data.get('birth_year')
                )
                
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    '✅ <b>День рождения успешно добавлен!</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    parse_mode='HTML'
                )
            else:
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    MESSAGES['cancel'],
                    chat_id=call.message.chat.id,
                    message_id=call.message.id
                )
            
            # Clear state
            user_states.pop(call.message.chat.id, None)
            user_data.pop(call.message.chat.id, None)
            
        except Exception as e:
            logger.error(f"Error in handle_confirmation: {e}")
            bot.answer_callback_query(call.id, MESSAGES['error'])
    
    @bot.message_handler(commands=['list'])
    @rate_limit(seconds=2)
    def handle_list_command(message: types.Message):
        cmd_list(message)
    
    @bot.message_handler(commands=['upcoming'])
    @rate_limit(seconds=2)
    def handle_upcoming_command(message: types.Message):
        cmd_upcoming(message)
    
    @bot.message_handler(commands=['delete'])
    @rate_limit(seconds=2)
    def handle_delete_command(message: types.Message):
        cmd_delete(message)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
    def handle_delete(call: types.CallbackQuery):
        """Handle delete callback."""
        try:
            birthday_id = int(call.data.split('_')[1])
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            
            if BirthdayDB.delete(birthday_id, user_id):
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    '✅ <b>День рождения успешно удален!</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    parse_mode='HTML'
                )
            else:
                bot.answer_callback_query(call.id, '❌ Ошибка при удалении')
                
        except Exception as e:
            logger.error(f"Error in handle_delete: {e}")
            bot.answer_callback_query(call.id, MESSAGES['error'])
    
    @bot.callback_query_handler(func=lambda call: call.data == 'cancel')
    def handle_cancel(call: types.CallbackQuery):
        """Handle cancel callback."""
        try:
            user_states.pop(call.message.chat.id, None)
            user_data.pop(call.message.chat.id, None)
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                MESSAGES['cancel'],
                chat_id=call.message.chat.id,
                message_id=call.message.id
            )
        except Exception as e:
            logger.error(f"Error in handle_cancel: {e}")
            bot.answer_callback_query(call.id, MESSAGES['error'])