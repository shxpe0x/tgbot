"""Date calculation helpers for birthdays."""
from datetime import date, datetime


def days_until_birthday(birth_date: date, from_date: date = None) -> int:
    """Calculate days until next birthday.
    
    Args:
        birth_date: The birthday date (year is ignored)
        from_date: Reference date (defaults to today)
    
    Returns:
        Number of days until next birthday (0 if today)
    """
    if from_date is None:
        from_date = date.today()
    
    # Handle leap year edge case (Feb 29)
    try:
        this_year_bd = date(from_date.year, birth_date.month, birth_date.day)
    except ValueError:
        # Feb 29 in non-leap year -> use Feb 28
        this_year_bd = date(from_date.year, birth_date.month, 28)
    
    # If birthday already passed this year, check next year
    if this_year_bd < from_date:
        try:
            this_year_bd = date(from_date.year + 1, birth_date.month, birth_date.day)
        except ValueError:
            this_year_bd = date(from_date.year + 1, birth_date.month, 28)
    
    return (this_year_bd - from_date).days


def calculate_age(birth_year: int, birth_date: date, reference_date: date = None) -> int:
    """Calculate age correctly, accounting for whether birthday has passed.
    
    Args:
        birth_year: Year of birth
        birth_date: Birthday date (month and day)
        reference_date: Date to calculate age from (defaults to today)
    
    Returns:
        Current age
    """
    if reference_date is None:
        reference_date = date.today()
    
    age = reference_date.year - birth_year
    
    # Check if birthday hasn't happened yet this year
    try:
        birthday_this_year = date(reference_date.year, birth_date.month, birth_date.day)
    except ValueError:
        # Feb 29 edge case
        birthday_this_year = date(reference_date.year, birth_date.month, 28)
    
    if reference_date < birthday_this_year:
        age -= 1
    
    return age


def is_birthday_today(birth_date: date, reference_date: date = None) -> bool:
    """Check if today is the birthday.
    
    Args:
        birth_date: The birthday date
        reference_date: Date to check against (defaults to today)
    
    Returns:
        True if it's the birthday
    """
    if reference_date is None:
        reference_date = date.today()
    
    return (birth_date.month == reference_date.month and 
            birth_date.day == reference_date.day)
