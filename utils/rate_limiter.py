"""Rate limiting utility for preventing spam."""
import time
from functools import wraps
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

# Store last action time for each user with TTL
# Using OrderedDict to maintain insertion order for cleanup
user_last_action = OrderedDict()
MAX_CACHE_SIZE = 10000  # Prevent unlimited growth


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
            
            # Auto-cleanup if cache is too large
            if len(user_last_action) > MAX_CACHE_SIZE:
                _cleanup_old_records()
            
            if user_id in user_last_action:
                time_diff = current_time - user_last_action[user_id]
                if time_diff < seconds:
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    # Don't execute the handler
                    return
            
            user_last_action[user_id] = current_time
            # Move to end to maintain LRU order
            user_last_action.move_to_end(user_id)
            
            return func(message)
        return wrapper
    return decorator


def _cleanup_old_records(max_age_seconds: int = 3600):
    """Internal cleanup function called automatically."""
    current_time = time.time()
    to_remove = []
    
    for user_id, last_time in user_last_action.items():
        if current_time - last_time > max_age_seconds:
            to_remove.append(user_id)
    
    for user_id in to_remove:
        del user_last_action[user_id]
    
    if to_remove:
        logger.info(f"Auto-cleaned {len(to_remove)} old rate limit records")


def clear_old_records(max_age_seconds: int = 3600):
    """Clear old rate limit records manually.
    
    Args:
        max_age_seconds: Maximum age of records to keep
    """
    _cleanup_old_records(max_age_seconds)