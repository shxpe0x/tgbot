"""Keyboards package."""
from .reply_keyboards import get_main_menu
from .inline_keyboards import (
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_delete_keyboard
)

__all__ = [
    'get_main_menu',
    'get_cancel_keyboard',
    'get_confirm_keyboard',
    'get_delete_keyboard'
]