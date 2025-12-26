"""Birthday-related handlers."""
import telebot
from telebot import types
import logging
from datetime import datetime, date
from database.models import UserDB, BirthdayDB, MAX_BIRTHDAYS_PER_USER
from keyboards.reply_keyboards import get_main_menu, get_cancel_keyboard
from config import MESSAGES
from utils.rate_limiter import rate_limit
from utils.date_helpers import calculate_age, days_until_birthday
import html as html_module

logger = logging.getLogger(__name__)

# User states
user_states = {}
user_data = {}

# Constants
MAX_NAME_LENGTH = 100

def register_birthday_handlers(bot: telebot.TeleBot):
    """Register all birthday handlers."""
    
    # ==================== COMMANDS ====================
    
    @bot.message_handler(commands=['cancel'])
    def cmd_cancel(message):
        """Cancel current operation."""
        if message.chat.id in user_states:
            user_states.pop(message.chat.id, None)
            user_data.pop(message.chat.id, None)
            bot.send_message(
                message.chat.id,
                '❌ Отменено',
                reply_markup=get_main_menu()
            )
        else:
            bot.send_message(message.chat.id, 'ℹ️ Нет активных операций')
    
    # ==================== TEXT BUTTON HANDLERS ====================
    
    @bot.message_handler(func=lambda m: m.text == '❌ Отмена')
    def btn_cancel(message):
        """Cancel button - should work regardless of state."""
        logger.info(f"CANCEL clicked by {message.from_user.id}")
        user_states.pop(message.chat.id, None)
        user_data.pop(message.chat.id, None)
        
        bot.send_message(
            message.chat.id,
            '❌ Отменено',
            reply_markup=get_main_menu()
        )
    
    @bot.message_handler(func=lambda m: m.text == '➕ Добавить')
    @rate_limit(seconds=2)
    def btn_add(message):
        """Add birthday button."""
        logger.info(f"Button ADD clicked by {message.from_user.id}")
        
        try:
            # Check birthday limit before starting
            user_id = UserDB.create_or_get(message.from_user.id, message.from_user.username)
            birthdays = BirthdayDB.get_all(user_id)
            
            if len(birthdays) >= MAX_BIRTHDAYS_PER_USER:
                bot.send_message(
                    message.chat.id,
                    f'❌ <b>Достигнут лимит:</b> {MAX_BIRTHDAYS_PER_USER} дней рождения.\n\n'
                    'Удали старые записи перед добавлением новых.',
                    parse_mode='HTML'
                )
                return
        except Exception as e:
            logger.error(f"Error checking birthday limit: {e}")
            bot.reply_to(message, MESSAGES['error'])
            return
        
        # Clear any previous state
        user_states.pop(message.chat.id, None)
        user_data.pop(message.chat.id, None)
        
        user_states[message.chat.id] = 'waiting_name'
        bot.send_message(
            message.chat.id,
            '👤 <b>Введи имя друга:</b>\n\n<i>Максимум 100 символов</i>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(func=lambda m: m.text == '📋 Список')
    @rate_limit(seconds=2)
    def btn_list(message):
        """List birthdays button."""
        logger.info(f"Button LIST clicked by {message.from_user.id}")
        
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
            today = date.today()
            
            for bd in birthdays:
                date_str = bd['birth_date'].strftime('%d.%m')
                # Names are already escaped in DB
                text += f'👤 <b>{bd["friend_name"]}</b> - {date_str}'
                
                if bd['birth_year']:
                    age = calculate_age(bd['birth_year'], bd['birth_date'], today)
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
            today = date.today()
            
            for bd in birthdays:
                date_str = bd['birth_date'].strftime('%d.%m')
                days_left = days_until_birthday(bd['birth_date'], today)
                
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
    
    # ==================== STATE HANDLERS ====================
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_name')
    def state_waiting_name(message):
        """Get name with validation."""
        name = message.text.strip()
        
        # Validate name length
        if len(name) > MAX_NAME_LENGTH:
            bot.send_message(
                message.chat.id,
                f'❌ Слишком длинное имя! Максимум {MAX_NAME_LENGTH} символов.\n'
                f'Твоё имя: {len(name)} символов.',
                reply_markup=get_cancel_keyboard(),
                parse_mode='HTML'
            )
            return
        
        if len(name) < 1:
            bot.send_message(
                message.chat.id,
                '❌ Имя не может быть пустым!',
                reply_markup=get_cancel_keyboard()
            )
            return
        
        logger.info(f"Got name: {name}")
        user_data[message.chat.id] = {'name': name}
        user_states[message.chat.id] = 'waiting_date'
        
        bot.send_message(
            message.chat.id,
            '📅 <b>Введи дату рождения</b>\nФормат: ДД.ММ.ГГГГ или ДД.ММ\n\nПример: <code>25.12.2000</code>',
            reply_markup=get_cancel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_date')
    def state_waiting_date(message):
        """Get date and save with improved validation."""
        logger.info(f"Got date: {message.text}")
        try:
            date_text = message.text.strip()
            birth_date = None
            birth_year = None
            
            # Try parsing different formats
            for fmt in ['%d.%m.%Y', '%d.%m']:
                try:
                    parsed = datetime.strptime(date_text, fmt)
                    
                    # Validate the date actually exists
                    try:
                        if fmt == '%d.%m.%Y':
                            birth_year = parsed.year
                            birth_date = date(parsed.year, parsed.month, parsed.day)
                            
                            # Validate year is reasonable
                            current_year = datetime.now().year
                            if birth_year < 1900 or birth_year > current_year:
                                bot.send_message(
                                    message.chat.id,
                                    f'❌ Неверный год! Год должен быть между 1900 и {current_year}.',
                                    reply_markup=get_cancel_keyboard(),
                                    parse_mode='HTML'
                                )
                                return
                        else:
                            # For dates without year, use leap year for validation
                            # This handles Feb 29 correctly
                            try:
                                birth_date = date(2000, parsed.month, parsed.day)
                            except ValueError:
                                bot.send_message(
                                    message.chat.id,
                                    f'❌ Неверная дата! Такой даты не существует.\nПример: <code>25.12.2000</code>',
                                    reply_markup=get_cancel_keyboard(),
                                    parse_mode='HTML'
                                )
                                return
                    except ValueError:
                        # Invalid date like 31.02 or 30.02
                        bot.send_message(
                            message.chat.id,
                            f'❌ Неверная дата! Такой даты не существует.\nПример: <code>25.12.2000</code>',
                            reply_markup=get_cancel_keyboard(),
                            parse_mode='HTML'
                        )
                        return
                    
                    break
                except ValueError:
                    continue
            
            if not birth_date:
                bot.send_message(
                    message.chat.id,
                    '❌ Неверный формат! Используй ДД.ММ.ГГГГ или ДД.ММ\nПример: <code>25.12.2000</code>',
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='HTML'
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
                f'✅ <b>Добавлено!</b>\n\n👤 {html_module.escape(name)}\n📅 {date_str}',
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
            
        except ValueError as e:
            logger.error(f"Validation error in state_waiting_date: {e}")
            if 'Birthday limit reached' in str(e):
                bot.send_message(
                    message.chat.id,
                    f'❌ <b>Достигнут лимит:</b> {MAX_BIRTHDAYS_PER_USER} дней рождения',
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    '❌ Ошибка при сохранении',
                    reply_markup=get_main_menu()
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
    
    # ==================== FALLBACK HANDLER ====================
    
    @bot.message_handler(func=lambda m: True)
    def fallback_handler(message):
        """Handle unknown messages."""
        # Only respond if user is not in any state
        if message.chat.id not in user_states:
            bot.send_message(
                message.chat.id,
                'ℹ️ Не понимаю эту команду.\n\nИспользуй кнопки меню или /help для справки.',
                parse_mode='HTML'
            )
