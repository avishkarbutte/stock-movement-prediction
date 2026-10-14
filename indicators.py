"""
StockScope AI - Technical Indicators Calculation Module
Computes financial and technical indicators using Pandas and NumPy without look-ahead bias.
Each function operates chronologically, using strictly historical data up to row t.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


# Indicator explanations for UI tooltips and educational documentation
INDICATOR_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "SMA": {
        "name": "Simple Moving Average",
        "formula": "SMA_n = (Close_t + Close_{t-1} + ... + Close_{t-n+1}) / n",
        "description": "Calculates the average price over a specific window of n trading sessions. Smooths out short-term fluctuations and identifies underlying price trends.",
    },
    "EMA": {
        "name": "Exponential Moving Average",
        "formula": "EMA_t = Close_t * (2 / (n + 1)) + EMA_{t-1} * (1 - 2 / (n + 1))",
        "description": "Places a greater weight and significance on the most recent price points, reacting faster to recent price action than simple moving averages.",
    },
    "RSI": {
        "name": "Relative Strength Index (14)",
        "formula": "RSI = 100 - (100 / (1 + RS)), where RS = Average Gain / Average Loss over 14 periods",
        "description": "Momentum oscillator measuring the speed and change of price movements on a scale of 0 to 100. Values above 70 typically signal overbought conditions; values below 30 signal oversold conditions.",
    },
    "MACD": {
        "name": "Moving Average Convergence Divergence",
        "formula": "MACD Line = EMA_12 - EMA_26; Signal Line = EMA_9(MACD); Histogram = MACD - Signal",
        "description": "Trend-following momentum indicator displaying the relationship between two exponential moving averages. Crosses above the signal line suggest bullish momentum; crosses below suggest bearish momentum.",
    },
    "Bollinger_Bands": {
        "name": "Bollinger Bands (20, 2)",
        "formula": "Middle = SMA_20; Upper = SMA_20 + 2 * StdDev; Lower = SMA_20 - 2 * StdDev",
        "description": "Volatility bands placed above and below a 20-day simple moving average. Bands expand during periods of high market volatility and contract during consolidation.",
    },
    "Daily_Returns": {
        "name": "Daily Returns",
        "formula": "Return_t = (Close_t - Close_{t-1}) / Close_{t-1}",
        "description": "Percentage change in closing price from the previous trading session to the current session.",
    },
    "Rolling_Volatility": {
        "name": "Rolling Volatility (20d)",
        "formula": "Volatility = Rolling_Std(Daily_Returns, 20) * sqrt(252)",
        "description": "Annualized rolling standard deviation of daily returns over a 20-day window, reflecting short-term market risk and price dispersion.",
    },
    "Momentum": {
        "name": "Price Momentum (ROC 10d)",
        "formula": "ROC_10 = ((Close_t - Close_{t-10}) / Close_{t-10}) * 100",
        "description": "Measures the percentage rate of change in price between the current closing price and the closing price 10 sessions ago.",
    },
    "Volume_Change": {
        "name": "Volume Change Ratio",
        "formula": "Volume_Ratio = Volume_t / SMA_20(Volume)",
        "description": "Ratio of current trading volume to its 20-day moving average. Ratios > 1.0 denote above-average institutional or retail trading activity.",
    },
}


def add_simple_moving_averages(
    df: pd.DataFrame,
    periods: Optional[list] = None
) -> pd.DataFrame:
    """Calculate Simple Moving Averages for specified periods."""
    if periods is None:
        periods = [10, 20, 50, 200]
    out = df.copy()
    for p in periods:
        if len(out) >= p:
            out[f"SMA_{p}"] = out["Close"].rolling(window=p, min_periods=p).mean()
        else:
            out[f"SMA_{p}"] = np.nan
    return out


def add_exponential_moving_averages(
    df: pd.DataFrame,
    periods: Optional[list] = None
) -> pd.DataFrame:
    """Calculate Exponential Moving Averages for specified periods."""
    if periods is None:
        periods = [12, 26]
    out = df.copy()
    for p in periods:
        out[f"EMA_{p}"] = out["Close"].ewm(span=p, adjust=False).mean()
    return out


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI) using standard exponential smoothing.
    Scale: 0 to 100.
    """
    out = df.copy()
    delta = out["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Use exponential moving average for smoothing (Wilder's style approximation)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    # Prevent division by zero
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Where avg_loss was 0 and avg_gain > 0, RSI is 100; where both 0, RSI is 50
    rsi = rsi.fillna(100.0).where(avg_loss != 0, 100.0)
    rsi = rsi.where((avg_gain != 0) | (avg_loss != 0), 50.0)

    out[f"RSI_{period}"] = rsi
    return out


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    Calculate Moving Average Convergence Divergence (MACD).
    Returns MACD line, Signal line, and MACD Histogram.
    """
    out = df.copy()
    ema_fast = out["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = out["Close"].ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    out["MACD"] = macd_line
    out["MACD_Signal"] = signal_line
    out["MACD_Hist"] = histogram
    return out


def add_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands: Middle Band (SMA 20), Upper Band (+2 std), Lower Band (-2 std),
    and Bandwidth.
    """
    out = df.copy()
    sma = out["Close"].rolling(window=period, min_periods=period).mean()
    rolling_std = out["Close"].rolling(window=period, min_periods=period).std()

    upper = sma + (num_std * rolling_std)
    lower = sma - (num_std * rolling_std)

    out["BB_Middle"] = sma
    out["BB_Upper"] = upper
    out["BB_Lower"] = lower
    # Bollinger Bandwidth: (Upper - Lower) / Middle
    out["BB_Bandwidth"] = (upper - lower) / sma.replace(0, np.nan)
    return out


def add_returns_and_volatility(
    df: pd.DataFrame,
    vol_window: int = 20
) -> pd.DataFrame:
    """
    Calculate Daily Returns and Annualized 20-day Rolling Volatility.
    """
    out = df.copy()
    out["Daily_Return"] = out["Close"].pct_change()
    # Annualized volatility assuming 252 trading days/year
    out["Rolling_Vol_20"] = out["Daily_Return"].rolling(
        window=vol_window, min_periods=vol_window
    ).std() * np.sqrt(252)
    return out


def add_momentum(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    Calculate Price Momentum (Rate of Change over specified window).
    """
    out = df.copy()
    out[f"Momentum_{window}"] = (
        (out["Close"] - out["Close"].shift(window)) / out["Close"].shift(window).replace(0, np.nan)
    ) * 100.0
    return out


def add_volume_indicators(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calculate Volume SMA and Volume Change Ratio.
    """
    out = df.copy()
    vol_sma = out["Volume"].rolling(window=window, min_periods=window).mean()
    out["Volume_SMA_20"] = vol_sma
    out["Volume_Ratio"] = out["Volume"] / vol_sma.replace(0, np.nan)
    return out


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline function to compute all supported technical indicators in sequence.
    Preserves chronological order and handles NaN windows appropriately.
    """
    out = df.copy()
    out = add_simple_moving_averages(out, periods=[10, 20, 50, 200])
    out = add_exponential_moving_averages(out, periods=[12, 26])
    out = add_rsi(out, period=14)
    out = add_macd(out, fast=12, slow=26, signal=9)
    out = add_bollinger_bands(out, period=20, num_std=2.0)
    out = add_returns_and_volatility(out, vol_window=20)
    out = add_momentum(out, window=10)
    out = add_volume_indicators(out, window=20)
    return out
