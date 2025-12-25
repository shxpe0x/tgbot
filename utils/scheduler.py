"""Scheduler for birthday notifications."""
import logging
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from database.db import get_connection
from config import NOTIFICATION_TIME
from utils.date_helpers import calculate_age, days_until_birthday
from utils.rate_limiter import clear_old_records

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
        today = date.today()
        
        with conn.cursor(dictionary=True) as cursor:
            # Get all birthdays that match today
            cursor.execute('''
                SELECT b.id, b.friend_name, b.birth_year, b.birth_date, u.telegram_id
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
                        age = calculate_age(bd['birth_year'], bd['birth_date'], today)
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
            
            # Get birthdays for upcoming reminders (excluding today to avoid duplicates)
            cursor.execute('''
                SELECT b.id, b.friend_name, b.birth_date, b.remind_days_before, u.telegram_id
                FROM birthdays b
                JOIN users u ON b.user_id = u.id
                WHERE b.remind_days_before > 0
                AND NOT (MONTH(b.birth_date) = %s AND DAY(b.birth_date) = %s)
            ''', (today.month, today.day))
            
            upcoming_birthdays = cursor.fetchall()
            
            for bd in upcoming_birthdays:
                try:
                    days_until = days_until_birthday(bd['birth_date'], today)
                    
                    # Send reminder only if days match AND it's not today (already handled above)
                    if days_until == bd['remind_days_before'] and days_until > 0:
                        # Calculate the actual date for display
                        try:
                            future_date = date(today.year, bd['birth_date'].month, bd['birth_date'].day)
                        except ValueError:
                            future_date = date(today.year, bd['birth_date'].month, 28)
                        
                        if future_date < today:
                            try:
                                future_date = date(today.year + 1, bd['birth_date'].month, bd['birth_date'].day)
                            except ValueError:
                                future_date = date(today.year + 1, bd['birth_date'].month, 28)
                        
                        message = f"🔔 <b>Напоминание!</b>\n\n"
                        message += f"Через {days_until} дн. день рождения у <b>{bd['friend_name']}</b>\n"
                        message += f"📅 {future_date.strftime('%d.%m')}"
                        
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

def cleanup_rate_limiter():
    """Periodic cleanup of rate limiter records."""
    try:
        clear_old_records(max_age_seconds=3600)
        logger.info("Rate limiter cleanup completed")
    except Exception as e:
        logger.error(f"Error in rate limiter cleanup: {e}")

def start_scheduler(bot):
    """Start the background scheduler."""
    global scheduler, bot_instance
    
    bot_instance = bot
    scheduler = BackgroundScheduler()
    
    # Schedule daily birthday check
    scheduler.add_job(
        check_birthdays,
        'cron',
        hour=NOTIFICATION_TIME['hour'],
        minute=NOTIFICATION_TIME['minute'],
        id='birthday_check'
    )
    
    # Schedule hourly rate limiter cleanup
    scheduler.add_job(
        cleanup_rate_limiter,
        'interval',
        hours=1,
        id='rate_limiter_cleanup'
    )
    
    scheduler.start()
    logger.info(f"Scheduler started. Will check birthdays daily at {NOTIFICATION_TIME['hour']}:{NOTIFICATION_TIME['minute']:02d}")

def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped gracefully")
