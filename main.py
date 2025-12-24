"""Main entry point for the bot."""
import logging
import sys
from bot import create_bot
from database import init_db
from handlers.commands import register_command_handlers
from handlers.birthdays import register_birthday_handlers
from utils.scheduler import start_scheduler, stop_scheduler

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
        
        # Start scheduler
        logger.info("Starting scheduler...")
        start_scheduler(bot)
        
        # Start polling
        logger.info("Bot started successfully! Polling...")
        bot.infinity_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
        # Gracefully stop scheduler
        logger.info("Stopping scheduler...")
        stop_scheduler()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        # Stop scheduler on error too
        stop_scheduler()
        sys.exit(1)

if __name__ == '__main__':
    main()