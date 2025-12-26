"""Database models for users and birthdays."""
import logging
import html
from datetime import datetime, date
from .db import get_connection
from utils.date_helpers import days_until_birthday

logger = logging.getLogger(__name__)

# Constants
MAX_BIRTHDAYS_PER_USER = 500  # Limit to prevent abuse

class UserDB:
    """User database operations."""
    
    @staticmethod
    def create_or_get(telegram_id: int, username: str = None) -> int:
        """Create user or get existing user ID."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Try to get existing user
            cursor.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # Create new user
            cursor.execute(
                "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
                (telegram_id, username)
            )
            user_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created new user: {telegram_id}")
            return user_id
                
        except Exception as e:
            logger.error(f"Error in create_or_get user: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

class BirthdayDB:
    """Birthday database operations."""
    
    @staticmethod
    def add(user_id: int, friend_name: str, birth_date: date, 
            birth_year: int = None, remind_days: int = 1) -> int:
        """Add new birthday with validation and limits."""
        conn = None
        try:
            # Sanitize friend name
            friend_name = html.escape(friend_name.strip())
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check birthday count limit
            cursor.execute(
                "SELECT COUNT(*) as count FROM birthdays WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result['count'] >= MAX_BIRTHDAYS_PER_USER:
                raise ValueError(f"Birthday limit reached ({MAX_BIRTHDAYS_PER_USER} max)")
            
            # Add birthday
            cursor.execute(
                '''INSERT INTO birthdays 
                   (user_id, friend_name, birth_date, birth_year, remind_days_before)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, friend_name, birth_date.isoformat(), birth_year, remind_days)
            )
            birthday_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added birthday {birthday_id} for user {user_id}")
            return birthday_id
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Error adding birthday: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_all(user_id: int) -> list:
        """Get all birthdays for a user."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                '''SELECT id, friend_name, birth_date, birth_year, remind_days_before
                   FROM birthdays WHERE user_id = ?
                   ORDER BY strftime('%m-%d', birth_date)''',
                (user_id,)
            )
            
            results = cursor.fetchall()
            
            # Convert to list of dicts and parse dates
            birthdays = []
            for row in results:
                bd = dict(row)
                bd['birth_date'] = date.fromisoformat(bd['birth_date'])
                birthdays.append(bd)
            
            return birthdays
            
        except Exception as e:
            logger.error(f"Error getting birthdays: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def delete(birthday_id: int, user_id: int) -> bool:
        """Delete birthday by ID."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM birthdays WHERE id = ? AND user_id = ?",
                (birthday_id, user_id)
            )
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted birthday {birthday_id} for user {user_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting birthday: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_upcoming(user_id: int, days: int = 30) -> list:
        """Get upcoming birthdays within specified days."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get all birthdays for user
            cursor.execute(
                '''SELECT id, friend_name, birth_date, birth_year
                   FROM birthdays WHERE user_id = ?''',
                (user_id,)
            )
            all_birthdays = cursor.fetchall()
            
            # Filter using date_helpers for consistency
            today = date.today()
            upcoming = []
            
            for row in all_birthdays:
                bd = dict(row)
                bd['birth_date'] = date.fromisoformat(bd['birth_date'])
                days_until = days_until_birthday(bd['birth_date'], today)
                
                if 0 <= days_until <= days:
                    upcoming.append(bd)
            
            # Sort by days until birthday
            upcoming.sort(key=lambda x: days_until_birthday(x['birth_date'], today))
            
            return upcoming
        except Exception as e:
            logger.error(f"Error getting upcoming birthdays: {e}")
            raise
        finally:
            if conn:
                conn.close()
