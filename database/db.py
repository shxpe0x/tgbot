"""Database connection and initialization."""
import mysql.connector
from mysql.connector import pooling
import logging
from config import DB_CONFIG

logger = logging.getLogger(__name__)

# Connection pool
connection_pool = None

def create_pool():
    """Create MySQL connection pool."""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="bot_pool",
            pool_size=DB_CONFIG['pool_size'],
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        logger.info("Database connection pool created successfully")
    except mysql.connector.Error as e:
        logger.error(f"Error creating connection pool: {e}")
        raise

def get_connection():
    """Get connection from pool."""
    if connection_pool is None:
        create_pool()
    return connection_pool.get_connection()

def init_db():
    """Initialize database tables."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_telegram_id (telegram_id)
                )
            ''')
            
            # Birthdays table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS birthdays (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    friend_name VARCHAR(100) NOT NULL,
                    birth_date DATE NOT NULL,
                    birth_year INT,
                    remind_days_before INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_birth_date (birth_date)
                )
            ''')
            
            conn.commit()
            logger.info("Database tables initialized successfully")
    except mysql.connector.Error as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()