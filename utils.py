"""
StockScope AI - Utility Functions
Formatting, helper routines, state management, and CSV exports.
"""

from datetime import datetime, date
import io
import re
from typing import Optional, Union
import pandas as pd


def format_currency(val: Optional[Union[float, int]], symbol: str = "₹") -> str:
    """Format a numeric value as a readable currency string."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
        if abs(val) >= 1e7:
            return f"{symbol}{val / 1e7:.2f} Cr"
        elif abs(val) >= 1e5:
            return f"{symbol}{val / 1e5:.2f} L"
        else:
            return f"{symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_percentage(val: Optional[Union[float, int]], include_sign: bool = True) -> str:
    """Format a ratio or percentage float (e.g. 0.025 -> +2.50%)."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
        sign = "+" if include_sign and val > 0 else ""
        return f"{sign}{val:.2f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_number(val: Optional[Union[float, int]]) -> str:
    """Format standard volume or counts with comma separation."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
        if abs(val) >= 1e7:
            return f"{val / 1e7:.2f} Cr"
        elif abs(val) >= 1e5:
            return f"{val / 1e5:.2f} L"
        elif abs(val) >= 1e3:
            return f"{val:,.0f}"
        return f"{val:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def format_date(dt: Optional[Union[datetime, date, str, pd.Timestamp]]) -> str:
    """Safely format date into standard YYYY-MM-DD string."""
    if dt is None or pd.isna(dt):
        return "N/A"
    if isinstance(dt, (datetime, date, pd.Timestamp)):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


def sanitize_ticker(ticker: str) -> str:
    """Clean and standardize stock ticker symbol."""
    if not ticker:
        return ""
    ticker = ticker.strip().upper()
    # Remove any dangerous characters, keep alphanumeric, dots, hyphens, carets
    clean = re.sub(r"[^A-Z0-9\.\^_\-]", "", ticker)
    return clean


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert pandas DataFrame to UTF-8 encoded CSV bytes for download."""
    if df.empty:
        return b""
    return df.to_csv(index=True).encode("utf-8")
