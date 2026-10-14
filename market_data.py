"""
StockScope AI - Market Data Retrieval Module
Fetches, caches, validates, and summarizes historical market data using yfinance.
Supports Indian National Stock Exchange (NSE) tickers (.NS), BSE (.BO), and indices.
"""

from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import yfinance as yf

from config import POPULAR_STOCKS, DEFAULT_PERIOD
from src.preprocessing import validate_market_data, DataValidationError
from src.utils import sanitize_ticker

# Try importing streamlit cache, provide transparent fallback if running in standalone test
try:
    import streamlit as st
    cache_decorator = st.cache_data(ttl=300, show_spinner=False)
except Exception:
    def cache_decorator(func):
        return func


def search_popular_stocks(query: str) -> List[Tuple[str, str]]:
    """
    Search starter universe of stocks by ticker or company name.
    Returns list of (Company Name, Ticker) pairs.
    """
    if not query:
        return list(POPULAR_STOCKS.items())
    
    q = query.strip().lower()
    matches = []
    for name, ticker in POPULAR_STOCKS.items():
        if q in name.lower() or q in ticker.lower():
            matches.append((name, ticker))
    return matches


def validate_ticker_symbol(ticker: str) -> Tuple[bool, str]:
    """
    Quickly validate if a ticker symbol is syntactically sound and recognized by yfinance.
    Returns (is_valid, message).
    """
    clean_sym = sanitize_ticker(ticker)
    if not clean_sym:
        return False, "Ticker symbol cannot be empty."
    
    try:
        t = yf.Ticker(clean_sym)
        # Fast history check for 5 days
        hist = t.history(period="5d")
        if hist.empty:
            return False, f"Symbol '{clean_sym}' returned no market data. Verify the symbol (e.g., RELIANCE.NS for NSE)."
        return True, "Valid symbol"
    except Exception as e:
        return False, f"Failed to validate ticker '{clean_sym}': {str(e)}"


@cache_decorator
def _fetch_raw_yfinance(ticker: str, period: str, interval: str = "1d") -> pd.DataFrame:
    """Internal cached helper to download raw data from Yahoo Finance."""
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    return df


def fetch_stock_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
    min_records: int = 5
) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """
    Retrieve, clean, and compute summary metrics for historical stock data.

    Returns:
        Tuple:
            - df: Cleaned chronological OHLCV DataFrame
            - summary: Dict of KPI metrics (close, prev_close, change, pct_change, volume, 52w high/low, etc.)
            - warnings: List of data cleansing notes/warnings
    """
    clean_ticker = sanitize_ticker(ticker)
    if not clean_ticker:
        raise DataValidationError("Ticker symbol is invalid or empty.")

    try:
        raw_df = _fetch_raw_yfinance(clean_ticker, period, interval)
    except Exception as exc:
        raise DataValidationError(
            f"Network or data provider error while retrieving '{clean_ticker}': {str(exc)}. "
            "Check internet connection or retry in a few moments."
        )

    if raw_df is None or raw_df.empty:
        raise DataValidationError(
            f"No historical price records found for ticker '{clean_ticker}'. "
            "Please check that the ticker symbol is valid (e.g., RELIANCE.NS for NSE) and currently active."
        )

    # Validate and clean data
    clean_df, warnings = validate_market_data(raw_df, min_records=min_records)

    # Compute key summary metrics from verified data
    latest_row = clean_df.iloc[-1]
    prev_row = clean_df.iloc[-2] if len(clean_df) >= 2 else latest_row

    latest_close = float(latest_row["Close"])
    prev_close = float(prev_row["Close"])
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close * 100.0) if prev_close != 0 else 0.0

    # Calculate 52-week or period high/low
    period_high = float(clean_df["High"].max())
    period_low = float(clean_df["Low"].min())

    # Try fetching basic company info gracefully
    company_name = clean_ticker
    currency = "INR" if clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO") else "USD"
    
    # Check if popular stocks has name
    for name, sym in POPULAR_STOCKS.items():
        if sym.upper() == clean_ticker.upper():
            company_name = name
            break

    summary: Dict[str, Any] = {
        "ticker": clean_ticker,
        "company_name": company_name,
        "currency": currency,
        "latest_close": latest_close,
        "prev_close": prev_close,
        "price_change": price_change,
        "pct_change": pct_change,
        "latest_volume": int(latest_row["Volume"]),
        "latest_date": clean_df.index[-1].strftime("%Y-%m-%d"),
        "period_high": period_high,
        "period_low": period_low,
        "period": period,
        "records_count": len(clean_df),
        "retrieval_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return clean_df, summary, warnings
