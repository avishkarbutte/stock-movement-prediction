"""
StockScope AI - Data Preprocessing & Validation Module
Ensures incoming market data adheres to data integrity requirements:
- Validates required columns (Open, High, Low, Close, Volume)
- Verifies strictly positive prices
- Checks chronological ordering and handles duplicates
- Flags insufficient historical records
- Never silently fabricates missing prices
"""

from typing import Tuple, List, Optional
import pandas as pd
import numpy as np


class DataValidationError(Exception):
    """Custom exception raised when market data fails validation."""
    pass


def validate_market_data(
    df: Optional[pd.DataFrame],
    min_records: int = 30
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate historical OHLCV data.

    Returns:
        Tuple[pd.DataFrame, List[str]]: (cleaned_dataframe, list_of_warning_messages)

    Raises:
        DataValidationError: If data is fundamentally corrupt, empty, or insufficient.
    """
    warnings: List[str] = []

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise DataValidationError("No market data returned. The dataset is completely empty.")

    # Check required columns (case-insensitive check)
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    col_map = {col.lower(): col for col in df.columns}

    missing_cols = [c for c in required_cols if c.lower() not in col_map]
    if missing_cols:
        raise DataValidationError(f"Missing mandatory market columns: {', '.join(missing_cols)}")

    # Standardize column names to Title Case
    clean_df = df.copy()
    rename_dict = {col_map[c.lower()]: c for c in required_cols if c.lower() in col_map}
    clean_df = clean_df.rename(columns=rename_dict)

    # If MultiIndex columns (sometimes returned by yfinance), flatten them
    if isinstance(clean_df.columns, pd.MultiIndex):
        clean_df.columns = clean_df.columns.get_level_values(0)

    # Keep relevant columns and ensure numeric
    clean_df = clean_df[required_cols]
    for col in required_cols:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    # Ensure Index is DatetimeIndex
    if not isinstance(clean_df.index, pd.DatetimeIndex):
        try:
            clean_df.index = pd.to_datetime(clean_df.index)
        except Exception as e:
            raise DataValidationError(f"Could not convert data index to dates: {e}")

    # Remove timezone info for uniform date handling
    if clean_df.index.tz is not None:
        clean_df.index = clean_df.index.tz_localize(None)

    # Check and remove duplicate timestamps, keeping the last observation
    duplicates = clean_df.index.duplicated(keep="last")
    if duplicates.any():
        num_dups = int(duplicates.sum())
        clean_df = clean_df[~duplicates]
        warnings.append(f"Removed {num_dups} duplicate trading date entries.")

    # Enforce strict chronological ascending sort
    clean_df = clean_df.sort_index(ascending=True)

    # Check for non-positive prices (Open, High, Low, Close must be strictly > 0)
    price_cols = ["Open", "High", "Low", "Close"]
    invalid_prices = (clean_df[price_cols] <= 0).any(axis=1)
    if invalid_prices.any():
        num_invalid = int(invalid_prices.sum())
        warnings.append(f"Dropped {num_invalid} rows containing zero or negative prices.")
        clean_df = clean_df[~invalid_prices]

    # Check for NaN values in price columns
    null_rows = clean_df[price_cols].isna().any(axis=1)
    if null_rows.any():
        num_nulls = int(null_rows.sum())
        warnings.append(f"Dropped {num_nulls} records with missing price values.")
        clean_df = clean_df[~null_rows]

    # Validate High >= Low integrity
    inverted_range = clean_df["High"] < clean_df["Low"]
    if inverted_range.any():
        num_inverted = int(inverted_range.sum())
        warnings.append(f"Corrected {num_inverted} records where High was recorded lower than Low.")
        clean_df.loc[inverted_range, ["High", "Low"]] = clean_df.loc[
            inverted_range, ["Low", "High"]
        ].values

    # Check minimum record threshold
    if len(clean_df) < min_records:
        raise DataValidationError(
            f"Insufficient historical data: Retrieved {len(clean_df)} valid trading days, "
            f"but a minimum of {min_records} days is required for meaningful technical and ML analysis."
        )

    return clean_df, warnings
