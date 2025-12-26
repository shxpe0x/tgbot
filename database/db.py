"""Database connection and initialization."""
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file path
DB_FILE = Path(__file__).parent.parent / 'birthdays.db'

def get_connection():
    """Get SQLite connection.
    
    Returns:
        Database connection
    """
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def init_db():
    """Initialize database tables."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id)')
        
        # Birthdays table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS birthdays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_name TEXT NOT NULL,
                birth_date DATE NOT NULL,
                birth_year INTEGER,
                remind_days_before INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON birthdays(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_birth_date ON birthdays(birth_date)')
        
        # User states table for persistent state management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                telegram_id INTEGER PRIMARY KEY,
                state TEXT,
                data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_updated ON user_states(updated_at)')
        
        conn.commit()
        logger.info(f"Database initialized successfully at {DB_FILE}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
