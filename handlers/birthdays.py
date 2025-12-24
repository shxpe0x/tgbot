"""Birthday-related handlers."""
import telebot
from telebot import types
import logging
from datetime import datetime, date
from database.models import UserDB, BirthdayDB
from keyboards.reply_keyboards import get_main_menu, get_cancel_keyboard
from config import MESSAGES
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# User states
user_states = {}
user_data = {}

def register_birthday_handlers(bot: telebot.TeleBot):
    """Register all birthday handlers."""
    
    # ==================== TEXT BUTTON HANDLERS ====================
    
    @bot.message_handler(func=lambda m: m.text == '➕ Добавить')
    @rate_limit(seconds=2)
    def btn_add(message):
        """Add birthday button."""
        logger.info(f"Button ADD clicked by {message.from_user.id}")
        if message.chat.id in user_states:
            return
        
        user_states[message.chat.id] = 'waiting_name'
        bot.send_message(
            message.chat.id,
            '👤 <b>Введи имя друга:</b>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(func=lambda m: m.text == '📋 Список')
    @rate_limit(seconds=2)
    def btn_list(message):
        """List birthdays button."""
        logger.info(f"Button LIST clicked by {message.from_user.id}")
        if message.chat.id in user_states:
            return
        
        try:
            user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
            birthdays = BirthdayDB.get_all(user_id)
            
            if not birthdays:
                bot.send_message(
                    message.chat.id,
                    '📅 <b>У тебя еще нет сохраненных дней рождения.</b>',
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
            logger.error(f"Error in btn_list: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.message_handler(func=lambda m: m.text == '🔔 Ближайшие')
    @rate_limit(seconds=2)
    def btn_upcoming(message):
        """Upcoming birthdays button."""
        logger.info(f"Button UPCOMING clicked by {message.from_user.id}")
        if message.chat.id in user_states:
            return
        
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
            logger.error(f"Error in btn_upcoming: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.message_handler(func=lambda m: m.text == '🗑️ Удалить')
    @rate_limit(seconds=2)
    def btn_delete(message):
        """Delete birthday button."""
        logger.info(f"Button DELETE clicked by {message.from_user.id}")
        if message.chat.id in user_states:
            return
        
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
            
            user_states[message.chat.id] = 'waiting_delete'
            user_data[message.chat.id] = {'birthdays': birthdays}
            
            text = '🗑️ <b>Введи номер для удаления:</b>\n\n'
            for i, bd in enumerate(birthdays, 1):
                date_str = bd['birth_date'].strftime('%d.%m')
                text += f'{i}. {bd["friend_name"]} - {date_str}\n'
            
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=get_cancel_keyboard(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error in btn_delete: {e}")
            bot.reply_to(message, MESSAGES['error'])
    
    @bot.message_handler(func=lambda m: m.text == '❌ Отмена')
    def btn_cancel(message):
        """Cancel button."""
        logger.info(f"CANCEL clicked by {message.from_user.id}")
        user_states.pop(message.chat.id, None)
        user_data.pop(message.chat.id, None)
        
        bot.send_message(
            message.chat.id,
            '❌ Отменено',
            reply_markup=get_main_menu()
        )
    
    # ==================== STATE HANDLERS ====================
    
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
        """Get date and save."""
        logger.info(f"Got date: {message.text}")
        try:
            date_text = message.text.strip()
            birth_date = None
            birth_year = None
            
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
            
            # Save to DB
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
            
            # Success
            date_str = birth_date.strftime('%d.%m.%Y') if birth_year else birth_date.strftime('%d.%m')
            bot.send_message(
                message.chat.id,
                f'✅ <b>Добавлено!</b>\n\n👤 {name}\n📅 {date_str}',
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error in state_waiting_date: {e}", exc_info=True)
            bot.send_message(
                message.chat.id,
                '❌ Ошибка при сохранении',
                reply_markup=get_main_menu()
            )
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_delete')
    def state_waiting_delete(message):
        """Delete by number."""
        try:
            num = int(message.text)
            birthdays = user_data[message.chat.id]['birthdays']
            
            if num < 1 or num > len(birthdays):
                bot.send_message(message.chat.id, '❌ Неверный номер!')
                return
            
            bd = birthdays[num - 1]
            user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
            
            if BirthdayDB.delete(bd['id'], user_id):
                user_states.pop(message.chat.id, None)
                user_data.pop(message.chat.id, None)
                
                bot.send_message(
                    message.chat.id,
                    '✅ <b>Удалено!</b>',
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
            else:
                bot.send_message(message.chat.id, '❌ Ошибка удаления')
        except ValueError:
            bot.send_message(message.chat.id, '❌ Введи номер!')
        except Exception as e:
            logger.error(f"Error in state_waiting_delete: {e}")
            bot.send_message(message.chat.id, '❌ Ошибка')