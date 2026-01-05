from datetime import date, timedelta
from dateutil.relativedelta import relativedelta, FR

def get_third_friday(year, month):
    """Calculates the 3rd Friday of a given month and year (Standard Futures Expiry)."""
    d = date(year, month, 1)
    return d + relativedelta(weekday=FR(3))

def parse_nt8_contract(contract_str):
    """
    Parses a NinjaTrader 8 contract string (e.g., 'MNQ 09-25').
    Returns (symbol, month, year).
    """
    parts = contract_str.split(' ')
    if len(parts) != 2:
        raise ValueError(f"Invalid format: {contract_str}. Expected 'SYMBOL MM-YY'")
    
    symbol = parts[0]
    date_part = parts[1]
    
    try:
        month_str, year_str = date_part.split('-')
        month = int(month_str)
        year = int("20" + year_str) # Assuming 21st century
    except ValueError:
        raise ValueError(f"Invalid date format in: {contract_str}. Expected 'MM-YY'")
        
    return symbol, month, year

def get_previous_contract(contract_str):
    """
    Returns the string for the previous quarterly contract.
    E.g. "MNQ 03-26" -> "MNQ 12-25"
    """
    symbol, month, year = parse_nt8_contract(contract_str)
    
    # Subtract 3 months
    dt = date(year, month, 1) - relativedelta(months=3)
    
    # Format back to "SYMBOL MM-YY"
    new_month = dt.month
    new_year = dt.year % 100  # Get last 2 digits
    
    return f"{symbol} {new_month:02d}-{new_year:02d}"

def get_contract_expiry(contract_str):
    """Returns the expiration date (3rd Friday) of the contract."""
    symbol, month, year = parse_nt8_contract(contract_str)
    return get_third_friday(year, month)

def get_active_trading_period(contract_str):
    """
    Determines the active trading period for a given contract.
    Returns (start_date, end_date).
    """
    symbol, month, year_full = parse_nt8_contract(contract_str)
    current_expiry = get_third_friday(year_full, month)
    
    prev_date = current_expiry - relativedelta(months=3)
    prev_expiry = get_third_friday(prev_date.year, prev_date.month)
    
    return prev_expiry, current_expiry

def get_last_n_days(days=90):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date
