"""
StockScope AI - Feature Engineering & Target Construction Module
Generates machine learning feature matrices and explicit classification targets.
Guarantees zero look-ahead bias by computing features strictly from past data (row <= t).
"""

from typing import Tuple, List, Dict
import pandas as pd
import numpy as np

from src.indicators import compute_all_indicators


# Detailed metadata explaining each engineered feature
FEATURE_DOCUMENTATION: Dict[str, str] = {
    "return_1d": "1-day percentage price return from day t-1 to day t.",
    "return_lag1": "Lagged 1-day return (from day t-2 to day t-1).",
    "return_lag2": "Lagged 1-day return (from day t-3 to day t-2).",
    "return_lag3": "Lagged 1-day return (from day t-4 to day t-3).",
    "return_5d": "5-day rolling return (from day t-5 to day t).",
    "ratio_close_sma10": "Ratio of current Close to 10-day SMA; values > 1 indicate short-term bullish trend.",
    "ratio_close_sma20": "Ratio of current Close to 20-day SMA; measures deviation from medium trend.",
    "ratio_close_sma50": "Ratio of current Close to 50-day SMA; primary intermediate trend indicator.",
    "sma_cross_10_50": "Ratio of 10-day SMA to 50-day SMA; golden cross (>1) or death cross (<1) indicator.",
    "rsi_14": "Relative Strength Index (14); momentum gauge between 0 and 100.",
    "macd": "MACD line (EMA 12 - EMA 26).",
    "macd_signal": "MACD signal line (9-day EMA of MACD line).",
    "macd_hist": "MACD histogram (MACD line - Signal line); reflects accelerating momentum.",
    "bb_pct_b": "Bollinger Bands %B indicator: (Close - Lower) / (Upper - Lower). Measures price position within bands.",
    "bb_bandwidth": "Bollinger Bandwidth; quantifies market volatility contraction and expansion.",
    "high_low_range": "Normalized intraday price range: (High - Low) / Close.",
    "open_close_return": "Intraday bar return: (Close - Open) / Open.",
    "rolling_vol_20": "Annualized 20-day rolling return volatility.",
    "momentum_10": "10-day price momentum rate of change percentage.",
    "volume_ratio": "Ratio of current session volume to its 20-day moving average.",
    "volume_ratio_lag1": "Lagged volume ratio from previous session.",
}


def construct_target(df: pd.DataFrame) -> pd.Series:
    """
    Explicit Target Construction:
    Target_t = 1 if Close_{t+1} > Close_t else 0.
    Equal closing prices (Close_{t+1} == Close_t) are assigned 0 (no upward movement).
    The last row will naturally produce NaN because tomorrow's close has not occurred.
    """
    next_close = df["Close"].shift(-1)
    # 1 if next session closed higher, 0 if lower or equal
    target = (next_close > df["Close"]).astype(float)
    # The last row has no future observation, keep it as NaN
    target.iloc[-1] = np.nan
    target.name = "Target"
    return target


def create_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Transform raw OHLCV DataFrame into rich engineered feature set.
    All calculations are strictly backward-looking.
    """
    # 1. Compute foundational technical indicators
    ind = compute_all_indicators(df)

    feat = pd.DataFrame(index=df.index)

    # 2. Return and lagged return features
    feat["return_1d"] = ind["Daily_Return"]
    feat["return_lag1"] = ind["Daily_Return"].shift(1)
    feat["return_lag2"] = ind["Daily_Return"].shift(2)
    feat["return_lag3"] = ind["Daily_Return"].shift(3)
    feat["return_5d"] = (df["Close"] - df["Close"].shift(5)) / df["Close"].shift(5).replace(0, np.nan)

    # 3. Moving average ratios (normalized, stationary features)
    feat["ratio_close_sma10"] = df["Close"] / ind["SMA_10"].replace(0, np.nan)
    feat["ratio_close_sma20"] = df["Close"] / ind["SMA_20"].replace(0, np.nan)
    feat["ratio_close_sma50"] = df["Close"] / ind["SMA_50"].replace(0, np.nan)
    feat["sma_cross_10_50"] = ind["SMA_10"] / ind["SMA_50"].replace(0, np.nan)

    # 4. Oscillators and momentum
    feat["rsi_14"] = ind["RSI_14"]
    feat["macd"] = ind["MACD"]
    feat["macd_signal"] = ind["MACD_Signal"]
    feat["macd_hist"] = ind["MACD_Hist"]

    # 5. Volatility and Bollinger metrics
    bb_range = (ind["BB_Upper"] - ind["BB_Lower"]).replace(0, np.nan)
    feat["bb_pct_b"] = (df["Close"] - ind["BB_Lower"]) / bb_range
    feat["bb_bandwidth"] = ind["BB_Bandwidth"]
    feat["rolling_vol_20"] = ind["Rolling_Vol_20"]

    # 6. Bar dynamics
    feat["high_low_range"] = (df["High"] - df["Low"]) / df["Close"].replace(0, np.nan)
    feat["open_close_return"] = (df["Close"] - df["Open"]) / df["Open"].replace(0, np.nan)
    feat["momentum_10"] = ind["Momentum_10"]

    # 7. Volume features
    feat["volume_ratio"] = ind["Volume_Ratio"]
    feat["volume_ratio_lag1"] = ind["Volume_Ratio"].shift(1)

    feature_cols = list(feat.columns)
    return feat, feature_cols


def prepare_ml_dataset(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, List[str]]:
    """
    Prepare complete dataset for ML modeling:
    - Calculates features without look-ahead bias
    - Constructs binary target
    - Extracts the final row (latest available trading session) as inference row
    - Removes initial NaN periods from rolling calculations in training set

    Returns:
        X (pd.DataFrame): Historical feature matrix
        y (pd.Series): Historical binary targets (0 or 1)
        latest_row (pd.DataFrame): Single row of features for tomorrow's prediction
        feature_names (List[str]): List of all feature names
    """
    features_df, feature_names = create_feature_matrix(df)
    target_series = construct_target(df)

    # Combine temporarily to align drops
    combined = features_df.copy()
    combined["__TARGET__"] = target_series

    # The latest row is the last index (where Target is NaN because tomorrow is unknown)
    latest_feature_row = features_df.iloc[[-1]].copy()

    # Historical training records are all rows EXCEPT the last one
    historical = combined.iloc[:-1].copy()

    # Drop rows with NaN caused by indicator lookback windows (e.g. 50-day SMA)
    valid_historical = historical.dropna()

    if valid_historical.empty:
        raise ValueError(
            "Feature preparation resulted in an empty dataset after dropping rolling window NaNs. "
            "Please provide a longer historical time window (e.g., 1 Year or 2 Years)."
        )

    X = valid_historical[feature_names].copy()
    y = valid_historical["__TARGET__"].astype(int)

    return X, y, latest_feature_row, feature_names
