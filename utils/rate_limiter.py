"""Rate limiting utility for preventing spam."""
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Store last action time for each user
user_last_action = {}

def rate_limit(seconds: int = 2):
    """Rate limiting decorator.
    
    Args:
        seconds: Minimum seconds between actions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(message):
            user_id = message.from_user.id
            current_time = time.time()
            
            if user_id in user_last_action:
                time_diff = current_time - user_last_action[user_id]
                if time_diff < seconds:
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    # Don't execute the handler
                    return
            
            user_last_action[user_id] = current_time
            return func(message)
        return wrapper
    return decorator

def clear_old_records(max_age_seconds: int = 3600):
    """Clear old rate limit records.
    
    Args:
        max_age_seconds: Maximum age of records to keep
    """
    current_time = time.time()
    to_remove = []
    
    for user_id, last_time in user_last_action.items():
        if current_time - last_time > max_age_seconds:
            to_remove.append(user_id)
    
    for user_id in to_remove:
        del user_last_action[user_id]
    
    if to_remove:
        logger.info(f"Cleared {len(to_remove)} old rate limit records")