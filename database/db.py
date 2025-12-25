"""Database connection and initialization."""
import mysql.connector
from mysql.connector import pooling, Error
import logging
import time
from config import DB_CONFIG

logger = logging.getLogger(__name__)

# Connection pool
connection_pool = None

def create_pool():
    """Create MySQL connection pool with proper configuration."""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="bot_pool",
            pool_size=DB_CONFIG['pool_size'],
            pool_reset_session=True,  # Reset session state on connection reuse
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            # Timeouts
            connection_timeout=10,  # 10 seconds to establish connection
            autocommit=False,  # Explicit transaction control
            get_warnings=True,  # Get SQL warnings
            # Keepalive
            use_pure=False  # Use C extension for better performance
        )
        logger.info("Database connection pool created successfully")
    except Error as e:
        logger.error(f"Error creating connection pool: {e}")
        raise

def get_connection(max_retries=3, retry_delay=1):
    """Get connection from pool with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Database connection
    
    Raises:
        mysql.connector.Error: If unable to get connection after retries
    """
    if connection_pool is None:
        create_pool()
    
    for attempt in range(max_retries):
        try:
            conn = connection_pool.get_connection()
            # Test connection
            conn.ping(reconnect=True, attempts=1, delay=0)
            return conn
        except Error as e:
            logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to get connection after {max_retries} attempts")
                raise

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
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()