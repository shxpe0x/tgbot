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

def register_birthday_handlers(bot: telebot.TeleBot):
    """Register all birthday handlers."""
    
    # ==================== CALLBACK HANDLERS ====================
    # IMPORTANT: Must be registered FIRST!
    
    @bot.callback_query_handler(func=lambda c: c.data == 'confirm_add')
    def callback_confirm_add(call):
        """Handle confirm button."""
        logger.info(f"CONFIRM CALLBACK TRIGGERED! User: {call.from_user.id}")
        try:
            chat_id = call.message.chat.id
            
            # Get data
            data = user_data.get(chat_id)
            if not data:
                logger.error(f"No data for chat {chat_id}")
                bot.answer_callback_query(call.id, '❌ Ошибка: данные потеряны')
                return
            
            # Save to DB
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            birthday_id = BirthdayDB.add(
                user_id=user_id,
                friend_name=data['name'],
                birth_date=data['birth_date'],
                birth_year=data.get('birth_year')
            )
            
            logger.info(f"Birthday saved with ID: {birthday_id}")
            
            # Clear state
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            
            # Answer
            bot.answer_callback_query(call.id, '✅ Сохранено!')
            bot.edit_message_text(
                '✅ <b>День рождения успешно добавлен!</b>',
                chat_id=chat_id,
                message_id=call.message.id,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in callback_confirm_add: {e}", exc_info=True)
            bot.answer_callback_query(call.id, '❌ Ошибка')
    
    @bot.callback_query_handler(func=lambda c: c.data == 'cancel_add')
    def callback_cancel_add(call):
        """Handle cancel button."""
        logger.info(f"CANCEL CALLBACK TRIGGERED! User: {call.from_user.id}")
        try:
            chat_id = call.message.chat.id
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                MESSAGES['cancel'],
                chat_id=chat_id,
                message_id=call.message.id
            )
        except Exception as e:
            logger.error(f"Error in callback_cancel_add: {e}")
    
    @bot.callback_query_handler(func=lambda c: c.data == 'cancel')
    def callback_cancel(call):
        """Handle cancel button."""
        logger.info(f"CANCEL CALLBACK TRIGGERED! User: {call.from_user.id}")
        try:
            chat_id = call.message.chat.id
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                MESSAGES['cancel'],
                chat_id=chat_id,
                message_id=call.message.id
            )
        except Exception as e:
            logger.error(f"Error in callback_cancel: {e}")
    
    @bot.callback_query_handler(func=lambda c: c.data.startswith('delete_'))
    def callback_delete(call):
        """Handle delete button."""
        logger.info(f"DELETE CALLBACK TRIGGERED! User: {call.from_user.id}")
        try:
            birthday_id = int(call.data.split('_')[1])
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            
            if BirthdayDB.delete(birthday_id, user_id):
                bot.answer_callback_query(call.id, '✅ Удалено')
                bot.edit_message_text(
                    '✅ <b>День рождения успешно удален!</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    parse_mode='HTML'
                )
            else:
                bot.answer_callback_query(call.id, '❌ Ошибка')
        except Exception as e:
            logger.error(f"Error in callback_delete: {e}")
    
    # ==================== COMMAND HANDLERS ====================
    
    @bot.message_handler(commands=['add'])
    @rate_limit(seconds=2)
    def cmd_add(message):
        """Start adding birthday."""
        user_states[message.chat.id] = 'waiting_name'
        bot.send_message(
            message.chat.id,
            '👤 <b>Введи имя друга:</b>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(commands=['list'])
    @rate_limit(seconds=2)
    def cmd_list(message):
        """Show all birthdays."""
        try:
            user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
            birthdays = BirthdayDB.get_all(user_id)
            
            if not birthdays:
                bot.send_message(
                    message.chat.id,
                    '📅 <b>У тебя еще нет сохраненных дней рождения.</b>\n\nИспользуй /add',
                    parse_mode='HTML'
                )
                return
            
            text = '🎉 <b>Список дней рождения:</b>\n\n'
            for bd in birthdays:
                date_str = bd['birth_date'].strftime('%d.%m')
                text += f'👤 <b>{bd["friend_name"]}</b> - {date_str}'
                if bd['birth_year']:
                    age = datetime.now().year - bd['birth_year']
                    text += f' ({age} лет)'
                text += '\n'
            
            bot.send_message(message.chat.id, text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error in cmd_list: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.message_handler(commands=['upcoming'])
    @rate_limit(seconds=2)
    def cmd_upcoming(message):
        """Show upcoming birthdays."""
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
                date_str = bd['birth_date'].strftime('%d.%m')
                today = datetime.now().date()
                this_year_bd = date(today.year, bd['birth_date'].month, bd['birth_date'].day)
                if this_year_bd < today:
                    this_year_bd = date(today.year + 1, bd['birth_date'].month, bd['birth_date'].day)
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
    
    @bot.message_handler(commands=['delete'])
    @rate_limit(seconds=2)
    def cmd_delete(message):
        """Start delete process."""
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
    
    # ==================== TEXT BUTTON HANDLERS ====================
    
    @bot.message_handler(func=lambda m: m.text == '➕ Добавить ДР')
    def text_btn_add(message):
        if message.chat.id not in user_states:
            cmd_add(message)
    
    @bot.message_handler(func=lambda m: m.text == '📋 Список')
    def text_btn_list(message):
        if message.chat.id not in user_states:
            cmd_list(message)
    
    @bot.message_handler(func=lambda m: m.text == '🔔 Ближайшие')
    def text_btn_upcoming(message):
        if message.chat.id not in user_states:
            cmd_upcoming(message)
    
    @bot.message_handler(func=lambda m: m.text == '🗑️ Удалить')
    def text_btn_delete(message):
        if message.chat.id not in user_states:
            cmd_delete(message)
    
    # ==================== STATE HANDLERS ====================
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_name')
    def state_waiting_name(message):
        """Get name."""
        if message.text.startswith('/'):
            return
        
        user_data[message.chat.id] = {'name': message.text}
        user_states[message.chat.id] = 'waiting_date'
        logger.info(f"Name saved: {message.text}")
        
        bot.send_message(
            message.chat.id,
            '📅 <b>Введи дату рождения</b>\nФормат: ДД.ММ.ГГГГ или ДД.ММ\n\nПример: <code>25.12.2000</code>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_date')
    def state_waiting_date(message):
        """Get date."""
        if message.text.startswith('/'):
            return
        
        try:
            date_text = message.text.strip()
            birth_date = None
            birth_year = None
            
            # Try formats
            for fmt in ['%d.%m.%Y', '%d.%m']:
                try:
                    parsed = datetime.strptime(date_text, fmt)
                    if fmt == '%d.%m.%Y':
                        birth_year = parsed.year
                        birth_date = parsed.date()
                    else:
                        birth_date = date(datetime.now().year, parsed.month, parsed.day)
                    break
                except ValueError:
                    continue
            
            if not birth_date:
                bot.send_message(message.chat.id, '❌ Неверный формат! Используй ДД.ММ.ГГГГ или ДД.ММ')
                return
            
            user_data[message.chat.id]['birth_date'] = birth_date
            user_data[message.chat.id]['birth_year'] = birth_year
            user_states[message.chat.id] = 'waiting_confirmation'
            
            logger.info(f"Date saved: {birth_date}, year: {birth_year}")
            logger.info(f"User data NOW: {user_data[message.chat.id]}")
            
            # Confirmation
            name = user_data[message.chat.id]['name']
            date_str = birth_date.strftime('%d.%m.%Y') if birth_year else birth_date.strftime('%d.%m')
            
            text = f'✅ <b>Подтверди данные:</b>\n\n'
            text += f'👤 Имя: <b>{name}</b>\n'
            text += f'📅 Дата: <b>{date_str}</b>'
            
            if birth_year:
                age = datetime.now().year - birth_year
                text += f'\n🎂 Возраст: <b>{age} лет</b>'
            
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=get_confirm_keyboard(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in state_waiting_date: {e}", exc_info=True)
            bot.reply_to(message, MESSAGES['error'])