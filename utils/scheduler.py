"""Scheduler for birthday notifications."""
import logging
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from database.db import get_connection
from config import NOTIFICATION_TIME

logger = logging.getLogger(__name__)

scheduler = None
bot_instance = None

def check_birthdays():
    """Check for birthdays and send notifications."""
    if not bot_instance:
        logger.warning("Bot instance not set for scheduler")
        return
    
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Get all birthdays that match today
            today = datetime.now().date()
            
            cursor.execute('''
                SELECT b.id, b.friend_name, b.birth_year, u.telegram_id
                FROM birthdays b
                JOIN users u ON b.user_id = u.id
                WHERE MONTH(b.birth_date) = %s AND DAY(b.birth_date) = %s
            ''', (today.month, today.day))
            
            birthdays_today = cursor.fetchall()
            
            # Send notifications for today's birthdays
            for bd in birthdays_today:
                try:
                    message = f"🎉 <b>Сегодня день рождения!</b>\n\n"
                    message += f"🎂 <b>{bd['friend_name']}</b>"
                    
                    if bd['birth_year']:
                        age = today.year - bd['birth_year']
                        message += f" исполняется <b>{age} лет</b>!"
                    
                    message += "\n\nНе забудь поздравить! 🎁"
                    
                    bot_instance.send_message(
                        bd['telegram_id'],
                        message,
                        parse_mode='HTML'
                    )
                    logger.info(f"Sent birthday notification to user {bd['telegram_id']}")
                except Exception as e:
                    logger.error(f"Error sending notification to {bd['telegram_id']}: {e}")
            
            # Get birthdays coming up (based on remind_days_before)
            cursor.execute('''
                SELECT b.id, b.friend_name, b.birth_date, b.remind_days_before, u.telegram_id
                FROM birthdays b
                JOIN users u ON b.user_id = u.id
                WHERE b.remind_days_before > 0
            ''')
            
            all_birthdays = cursor.fetchall()
            
            for bd in all_birthdays:
                try:
                    bd_date = bd['birth_date']
                    
                    # Handle leap year edge case
                    try:
                        this_year_bd = date(today.year, bd_date.month, bd_date.day)
                    except ValueError:
                        this_year_bd = date(today.year, bd_date.month, 28)
                    
                    if this_year_bd < today:
                        try:
                            this_year_bd = date(today.year + 1, bd_date.month, bd_date.day)
                        except ValueError:
                            this_year_bd = date(today.year + 1, bd_date.month, 28)
                    
                    days_until = (this_year_bd - today).days
                    
                    if days_until == bd['remind_days_before']:
                        message = f"🔔 <b>Напоминание!</b>\n\n"
                        message += f"Через {days_until} дн. день рождения у <b>{bd['friend_name']}</b>\n"
                        message += f"📅 {this_year_bd.strftime('%d.%m')}"
                        
                        bot_instance.send_message(
                            bd['telegram_id'],
                            message,
                            parse_mode='HTML'
                        )
                        logger.info(f"Sent reminder to user {bd['telegram_id']}")
                except Exception as e:
                    logger.error(f"Error sending reminder: {e}")
        
    except Exception as e:
        logger.error(f"Critical error in check_birthdays: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def start_scheduler(bot):
    """Start the background scheduler."""
    global scheduler, bot_instance
    
    bot_instance = bot
    scheduler = BackgroundScheduler()
    
    # Schedule daily check
    scheduler.add_job(
        check_birthdays,
        'cron',
        hour=NOTIFICATION_TIME['hour'],
        minute=NOTIFICATION_TIME['minute'],
        id='birthday_check'
    )
    
    scheduler.start()
    logger.info(f"Scheduler started. Will check birthdays daily at {NOTIFICATION_TIME['hour']}:{NOTIFICATION_TIME['minute']:02d}")

def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped gracefully")