"""Birthday-related handlers."""
import telebot
from telebot import types
import logging
from datetime import datetime, date
from database.models import UserDB, BirthdayDB
from keyboards.inline_keyboards import (
    get_main_menu,
    get_back_to_menu,
    get_cancel_keyboard,
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
    
    # ==================== INLINE MENU CALLBACKS ====================
    
    @bot.callback_query_handler(func=lambda c: c.data == 'menu_add')
    def callback_menu_add(call):
        """Start adding birthday from menu."""
        logger.info(f"Menu ADD clicked by {call.from_user.id}")
        user_states[call.message.chat.id] = 'waiting_name'
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            '👤 <b>Введи имя друга:</b>',
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.callback_query_handler(func=lambda c: c.data == 'menu_list')
    def callback_menu_list(call):
        """Show list from menu."""
        logger.info(f"Menu LIST clicked by {call.from_user.id}")
        try:
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            birthdays = BirthdayDB.get_all(user_id)
            
            if not birthdays:
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    '📅 <b>У тебя еще нет сохраненных дней рождения.</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    reply_markup=get_main_menu(),
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
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in callback_menu_list: {e}")
            bot.answer_callback_query(call.id, '❌ Ошибка')
    
    @bot.callback_query_handler(func=lambda c: c.data == 'menu_upcoming')
    def callback_menu_upcoming(call):
        """Show upcoming birthdays from menu."""
        logger.info(f"Menu UPCOMING clicked by {call.from_user.id}")
        try:
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            birthdays = BirthdayDB.get_upcoming(user_id, days=30)
            
            if not birthdays:
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    '📅 <b>В ближайшие 30 дней нет дней рождения.</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    reply_markup=get_main_menu(),
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
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in callback_menu_upcoming: {e}")
            bot.answer_callback_query(call.id, '❌ Ошибка')
    
    @bot.callback_query_handler(func=lambda c: c.data == 'menu_delete')
    def callback_menu_delete(call):
        """Show delete menu."""
        logger.info(f"Menu DELETE clicked by {call.from_user.id}")
        try:
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            birthdays = BirthdayDB.get_all(user_id)
            
            if not birthdays:
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    '📅 <b>У тебя нет сохраненных дней рождения.</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
                return
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                '🗑️ <b>Выбери день рождения для удаления:</b>',
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=get_delete_keyboard(birthdays),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in callback_menu_delete: {e}")
            bot.answer_callback_query(call.id, '❌ Ошибка')
    
    @bot.callback_query_handler(func=lambda c: c.data == 'back_to_menu')
    def callback_back_to_menu(call):
        """Return to main menu."""
        logger.info(f"BACK TO MENU clicked by {call.from_user.id}")
        # Clear any state
        user_states.pop(call.message.chat.id, None)
        user_data.pop(call.message.chat.id, None)
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            '🎂 <b>Главное меню</b>\nВыбери действие:',
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
    
    @bot.callback_query_handler(func=lambda c: c.data == 'cancel')
    def callback_cancel(call):
        """Cancel current action."""
        logger.info(f"CANCEL clicked by {call.from_user.id}")
        user_states.pop(call.message.chat.id, None)
        user_data.pop(call.message.chat.id, None)
        
        bot.answer_callback_query(call.id, '❌ Отменено')
        bot.edit_message_text(
            '❌ Отменено',
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
    
    @bot.callback_query_handler(func=lambda c: c.data.startswith('delete_'))
    def callback_delete(call):
        """Delete birthday."""
        logger.info(f"DELETE clicked by {call.from_user.id}: {call.data}")
        try:
            birthday_id = int(call.data.split('_')[1])
            user_id = UserDB.create_or_get(call.from_user.id, call.from_user.username)
            
            if BirthdayDB.delete(birthday_id, user_id):
                bot.answer_callback_query(call.id, '✅ Удалено!')
                bot.edit_message_text(
                    '✅ <b>День рождения успешно удален!</b>',
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
            else:
                bot.answer_callback_query(call.id, '❌ Ошибка')
        except Exception as e:
            logger.error(f"Error in callback_delete: {e}")
            bot.answer_callback_query(call.id, '❌ Ошибка')
    
    # ==================== MESSAGE HANDLERS ====================
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_name')
    def state_waiting_name(message):
        """Get name."""
        logger.info(f"Got name: {message.text}")
        user_data[message.chat.id] = {'name': message.text}
        user_states[message.chat.id] = 'waiting_date'
        
        bot.send_message(
            message.chat.id,
            '📅 <b>Введи дату рождения</b>\nФормат: ДД.ММ.ГГГГ или ДД.ММ\n\nПример: <code>25.12.2000</code>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_date')
    def state_waiting_date(message):
        """Get date and save immediately (no confirmation)."""
        logger.info(f"Got date: {message.text}")
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
                bot.send_message(
                    message.chat.id,
                    '❌ Неверный формат! Используй ДД.ММ.ГГГГ или ДД.ММ',
                    reply_markup=get_cancel_keyboard()
                )
                return
            
            # Save immediately to DB
            user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
            name = user_data[message.chat.id]['name']
            
            birthday_id = BirthdayDB.add(
                user_id=user_id,
                friend_name=name,
                birth_date=birth_date,
                birth_year=birth_year
            )
            
            logger.info(f"Birthday saved with ID: {birthday_id}")
            
            # Clear state
            user_states.pop(message.chat.id, None)
            user_data.pop(message.chat.id, None)
            
            # Success message
            date_str = birth_date.strftime('%d.%m.%Y') if birth_year else birth_date.strftime('%d.%m')
            bot.send_message(
                message.chat.id,
                f'✅ <b>Добавлено!</b>\n\n👤 {name}\n📅 {date_str}',
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error in state_waiting_date: {e}", exc_info=True)
            bot.reply_to(message, '❌ Ошибка при сохранении', reply_markup=get_main_menu())