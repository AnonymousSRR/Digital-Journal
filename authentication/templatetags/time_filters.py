from django import template

register = template.Library()

@register.filter
def format_writing_time(seconds):
    """
    Format writing time in seconds to a human-readable format.
    Examples: 45 -> "45s", 120 -> "2m", 3661 -> "1.0h"
    """
    # Handle None, empty string, or zero values
    if seconds is None or seconds == "" or seconds == 0:
        return "N/A"
    
    # Convert to integer
    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        return "N/A"
    
    # Handle zero after conversion (for string "0" case)
    if seconds == 0:
        return "N/A"
    
    # Handle negative values
    if seconds < 0:
        return f"{seconds}s"
    
    # Format based on duration
    if seconds >= 3600:
        # 1 hour or more
        hours = seconds / 3600
        return f"{hours:.1f}h"
    elif seconds >= 60:
        # 1 minute to 59 minutes
        minutes = seconds // 60  # Use integer division to avoid rounding issues
        return f"{minutes}m"
    else:
        # Less than 1 minute
        return f"{seconds}s" 