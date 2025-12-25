"""Main entry point for the bot."""
import logging
import sys
from bot import create_bot
from database import init_db
from handlers.commands import register_command_handlers
from handlers.birthdays import register_birthday_handlers
# from utils.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# SCHEDULER CONFIGURATION
# ============================================================================
# Планировщик уведомлений отключен для демонстрации.
# Для включения:
# 1. Раскомментируй импорт выше (строка 7)
# 2. Раскомментируй блоки с start_scheduler() и stop_scheduler() ниже
# 3. Убедись что APScheduler установлен: pip install apscheduler
# ============================================================================
ENABLE_SCHEDULER = False

def main():
    """Main function to start the bot."""
    try:
        logger.info("Starting bot...")
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Create bot instance
        bot = create_bot()
        
        # Register handlers
        logger.info("Registering handlers...")
        register_command_handlers(bot)
        register_birthday_handlers(bot)
        
        # Start scheduler (DISABLED FOR DEMO)
        if ENABLE_SCHEDULER:
            logger.info("Starting scheduler...")
            # start_scheduler(bot)
            pass
        else:
            logger.info("Scheduler disabled (set ENABLE_SCHEDULER=True to enable)")
        
        # Start polling
        logger.info("Bot started successfully! Polling...")
        bot.infinity_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
        
        # Gracefully stop scheduler
        if ENABLE_SCHEDULER:
            logger.info("Stopping scheduler...")
            # stop_scheduler()
            pass
        
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        
        # Stop scheduler on error too
        if ENABLE_SCHEDULER:
            # stop_scheduler()
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()
