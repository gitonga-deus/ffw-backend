"""
Date formatting utilities for certificates.
"""
from datetime import datetime


def get_ordinal_suffix(day: int) -> str:
    """
    Get the ordinal suffix for a day number.
    
    Args:
        day: Day of the month (1-31)
        
    Returns:
        Ordinal suffix ('st', 'nd', 'rd', or 'th')
    """
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return suffix


def format_date_with_ordinal(date: datetime) -> str:
    """
    Format a date in long format with ordinal suffix.
    Example: "November 17th, 2025"
    
    Args:
        date: datetime object
        
    Returns:
        Formatted date string with ordinal suffix
    """
    day = date.day
    suffix = get_ordinal_suffix(day)
    
    # Format: "Month Day{suffix}, Year"
    formatted_date = date.strftime(f"%B {day}{suffix}, %Y")
    
    return formatted_date


def get_date_parts_for_superscript(date: datetime) -> tuple:
    """
    Get date parts separated for rendering with superscript ordinal.
    
    Args:
        date: datetime object
        
    Returns:
        Tuple of (month, day, suffix, year) for custom rendering
        Example: ("November", "17", "th", "2025")
    """
    day = date.day
    suffix = get_ordinal_suffix(day)
    month = date.strftime("%B")
    year = date.strftime("%Y")
    
    return (month, str(day), suffix, year)
