"""
StockScope AI - Local Persistence Module (SQLite)
Manages educational watchlists, virtual paper trading positions, cash balances,
and historical prediction logging.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from config import DB_PATH, DATA_DIR


def get_db_connection() -> sqlite3.Connection:
    """Establish connection to local SQLite database with thread safety."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Watchlist Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            company_name TEXT,
            added_at TEXT
        );
    """)

    # 2. Virtual Portfolio Holdings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS virtual_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            shares REAL NOT NULL,
            buy_price REAL NOT NULL,
            buy_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)

    # 3. Virtual Cash Account
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS virtual_cash (
            id INTEGER PRIMARY KEY,
            balance REAL NOT NULL,
            initial_balance REAL NOT NULL
        );
    """)

    # Seed default cash if empty
    cursor.execute("SELECT COUNT(*) FROM virtual_cash;")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO virtual_cash (id, balance, initial_balance) VALUES (1, 100000.0, 100000.0);"
        )

    # 4. Prediction History
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticker TEXT NOT NULL,
            feature_date TEXT NOT NULL,
            target_date TEXT NOT NULL,
            model_name TEXT NOT NULL,
            predicted_direction TEXT NOT NULL,
            prob_up REAL NOT NULL,
            prob_down REAL NOT NULL,
            confidence TEXT NOT NULL,
            actual_direction TEXT
        );
    """)

    conn.commit()
    conn.close()


# Initialize database upon module import
init_db()


# ==========================================
# WATCHLIST FUNCTIONS
# ==========================================

def get_watchlist() -> pd.DataFrame:
    """Retrieve all tickers saved in user's watchlist."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT ticker, company_name, added_at FROM watchlist ORDER BY added_at DESC;", conn)
    conn.close()
    return df


def add_to_watchlist(ticker: str, company_name: str) -> bool:
    """Add a stock ticker to watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT OR REPLACE INTO watchlist (ticker, company_name, added_at) VALUES (?, ?, ?);",
            (ticker.upper().strip(), company_name, now_str)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def remove_from_watchlist(ticker: str) -> bool:
    """Remove a ticker from watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?;", (ticker.upper().strip(),))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# ==========================================
# VIRTUAL PORTFOLIO FUNCTIONS
# ==========================================

def get_virtual_cash() -> Tuple[float, float]:
    """Retrieve current virtual cash balance and initial allocation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, initial_balance FROM virtual_cash WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        return float(row["balance"]), float(row["initial_balance"])
    return 100000.0, 100000.0


def update_virtual_cash(new_balance: float):
    """Update virtual cash balance."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE virtual_cash SET balance = ? WHERE id = 1;", (new_balance,))
    conn.commit()
    conn.close()


def get_virtual_portfolio() -> pd.DataFrame:
    """Retrieve all active hypothetical stock holdings."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT id, ticker, company_name, shares, buy_price, buy_date, created_at "
        "FROM virtual_portfolio ORDER BY id DESC;",
        conn
    )
    conn.close()
    return df


def add_virtual_position(
    ticker: str,
    company_name: str,
    shares: float,
    buy_price: float,
    buy_date: str
) -> Tuple[bool, str]:
    """
    Execute simulated stock purchase.
    Validates sufficient cash before booking the virtual holding.
    """
    total_cost = shares * buy_price
    cash, initial_cash = get_virtual_cash()

    if total_cost > cash:
        return False, f"Insufficient virtual cash. Needed: ₹{total_cost:,.2f}, Available: ₹{cash:,.2f}"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO virtual_portfolio (ticker, company_name, shares, buy_price, buy_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (ticker.upper().strip(), company_name, shares, buy_price, buy_date, now_str)
        )
        # Deduct cash
        new_cash = cash - total_cost
        cursor.execute("UPDATE virtual_cash SET balance = ? WHERE id = 1;", (new_cash,))
        conn.commit()
        return True, "Simulated purchase successful!"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def remove_virtual_position(position_id: int, current_price: float) -> Tuple[bool, str]:
    """Sell simulated position, crediting proceeds to cash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT shares FROM virtual_portfolio WHERE id = ?;", (position_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Position not found."

        shares = float(row["shares"])
        proceeds = shares * current_price

        cursor.execute("DELETE FROM virtual_portfolio WHERE id = ?;", (position_id,))
        cursor.execute("UPDATE virtual_cash SET balance = balance + ? WHERE id = 1;", (proceeds,))
        conn.commit()
        return True, f"Sold position. Credited ₹{proceeds:,.2f} to virtual cash."
    except Exception as e:
        conn.rollback()
        return False, f"Error selling position: {str(e)}"
    finally:
        conn.close()


def reset_virtual_portfolio(initial_cash: float = 100000.0) -> bool:
    """Reset virtual portfolio and reset cash to initial balance."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM virtual_portfolio;")
        cursor.execute(
            "UPDATE virtual_cash SET balance = ?, initial_balance = ? WHERE id = 1;",
            (initial_cash, initial_cash)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# ==========================================
# PREDICTION HISTORY LOGGING
# ==========================================

def log_prediction(
    ticker: str,
    feature_date: str,
    target_date: str,
    model_name: str,
    predicted_direction: str,
    prob_up: float,
    prob_down: float,
    confidence: str
) -> bool:
    """Log an AI prediction record to SQLite for auditing and evaluation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO prediction_history (
                timestamp, ticker, feature_date, target_date, model_name,
                predicted_direction, prob_up, prob_down, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                now_str, ticker.upper().strip(), feature_date, target_date,
                model_name, predicted_direction, prob_up, prob_down, confidence
            )
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_prediction_history(ticker: Optional[str] = None) -> pd.DataFrame:
    """Retrieve logged predictions, optionally filtered by ticker."""
    conn = get_db_connection()
    if ticker:
        df = pd.read_sql_query(
            "SELECT * FROM prediction_history WHERE ticker = ? ORDER BY id DESC;",
            conn,
            params=(ticker.upper().strip(),)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM prediction_history ORDER BY id DESC;",
            conn
        )
    conn.close()
    return df


def clear_prediction_history() -> bool:
    """Clear all logged prediction records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM prediction_history;")
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
