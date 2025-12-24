"""Database models for users and birthdays."""
import logging
from datetime import datetime, date
from .db import get_connection

logger = logging.getLogger(__name__)

class UserDB:
    """User database operations."""
    
    @staticmethod
    def create_or_get(telegram_id: int, username: str = None) -> int:
        """Create user or get existing user ID."""
        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                # Check if user exists
                cursor.execute(
                    "SELECT id FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    return result['id']
                
                # Create new user
                cursor.execute(
                    "INSERT INTO users (telegram_id, username) VALUES (%s, %s)",
                    (telegram_id, username)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error in create_or_get user: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

class BirthdayDB:
    """Birthday database operations."""
    
    @staticmethod
    def add(user_id: int, friend_name: str, birth_date: date, 
            birth_year: int = None, remind_days: int = 1) -> int:
        """Add new birthday."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO birthdays 
                       (user_id, friend_name, birth_date, birth_year, remind_days_before)
                       VALUES (%s, %s, %s, %s, %s)''',
                    (user_id, friend_name, birth_date, birth_year, remind_days)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding birthday: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @staticmethod
    def get_all(user_id: int) -> list:
        """Get all birthdays for a user."""
        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    '''SELECT id, friend_name, birth_date, birth_year, remind_days_before
                       FROM birthdays WHERE user_id = %s
                       ORDER BY MONTH(birth_date), DAY(birth_date)''',
                    (user_id,)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting birthdays: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def delete(birthday_id: int, user_id: int) -> bool:
        """Delete birthday by ID."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM birthdays WHERE id = %s AND user_id = %s",
                    (birthday_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting birthday: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @staticmethod
    def get_upcoming(user_id: int, days: int = 30) -> list:
        """Get upcoming birthdays within specified days."""
        conn = get_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    '''SELECT id, friend_name, birth_date, birth_year
                       FROM birthdays WHERE user_id = %s
                       AND (
                           (DAYOFYEAR(birth_date) >= DAYOFYEAR(CURDATE()) 
                            AND DAYOFYEAR(birth_date) <= DAYOFYEAR(CURDATE()) + %s)
                           OR
                           (DAYOFYEAR(birth_date) < DAYOFYEAR(CURDATE())
                            AND DAYOFYEAR(birth_date) <= (DAYOFYEAR(CURDATE()) + %s - 365))
                       )
                       ORDER BY 
                           CASE 
                               WHEN DAYOFYEAR(birth_date) >= DAYOFYEAR(CURDATE())
                               THEN DAYOFYEAR(birth_date)
                               ELSE DAYOFYEAR(birth_date) + 365
                           END''',
                    (user_id, days, days)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting upcoming birthdays: {e}")
            raise
        finally:
            conn.close()