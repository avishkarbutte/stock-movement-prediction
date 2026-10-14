"""
StockScope AI - Main Streamlit Application
AI-Based Stock Market Movement Prediction & Analysis System
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    DISCLAIMER_TEXT,
    POPULAR_STOCKS,
    DEFAULT_TICKER,
    PERIOD_OPTIONS,
    DEFAULT_PERIOD,
    THEME_COLORS
)
from src.utils import sanitize_ticker, format_currency, format_percentage, format_number
from src.market_data import fetch_stock_data, search_popular_stocks
from src.storage import get_watchlist, add_to_watchlist, get_virtual_cash, get_prediction_history

# Set Streamlit Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} | Financial Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme CSS styling
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {THEME_COLORS['bg_dark']};
            color: {THEME_COLORS['text_primary']};
        }}
        .kpi-card {{
            background-color: {THEME_COLORS['card_dark']};
            border: 1px solid {THEME_COLORS['card_border']};
            border-radius: 10px;
            padding: 18px;
            text-align: left;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        .kpi-title {{
            font-size: 13px;
            color: {THEME_COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .kpi-value {{
            font-size: 26px;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 4px;
        }}
        .kpi-delta-pos {{
            color: {THEME_COLORS['accent_green']};
            font-size: 14px;
            font-weight: 600;
        }}
        .kpi-delta-neg {{
            color: {THEME_COLORS['accent_red']};
            font-size: 14px;
            font-weight: 600;
        }}
        .disclaimer-box {{
            background-color: rgba(245, 158, 11, 0.1);
            border-left: 4px solid {THEME_COLORS['accent_yellow']};
            padding: 12px 16px;
            border-radius: 4px;
            font-size: 13px;
            color: #FCD34D;
            margin-bottom: 20px;
        }}
        .nav-card {{
            background-color: {THEME_COLORS['card_dark']};
            border: 1px solid {THEME_COLORS['card_border']};
            border-radius: 8px;
            padding: 16px;
            height: 100%;
            transition: transform 0.2s ease;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize Session State
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = DEFAULT_TICKER
if "selected_period" not in st.session_state:
    st.session_state.selected_period = DEFAULT_PERIOD
if "trained_models" not in st.session_state:
    st.session_state.trained_models = None
if "prepared_data" not in st.session_state:
    st.session_state.prepared_data = None

# Sidebar Controls
with st.sidebar:
    st.markdown(f"## 📈 {APP_NAME}")
    st.caption(f"v{APP_VERSION} • Educational AI System")
    st.markdown("---")

    # Stock Selector Mode
    selector_mode = st.radio("Stock Selection", ["Popular NSE Equities", "Custom Ticker"], horizontal=True)

    if selector_mode == "Popular NSE Equities":
        stock_options = list(POPULAR_STOCKS.keys())
        # Find index of current ticker
        current_name = [k for k, v in POPULAR_STOCKS.items() if v == st.session_state.selected_ticker]
        default_idx = stock_options.index(current_name[0]) if current_name else 0
        selected_stock_name = st.selectbox("Select Company / Index", stock_options, index=default_idx)
        st.session_state.selected_ticker = POPULAR_STOCKS[selected_stock_name]
    else:
        custom_input = st.text_input(
            "Enter Yahoo Ticker (e.g. INFY.NS, AAPL)",
            value=st.session_state.selected_ticker
        )
        if custom_input:
            st.session_state.selected_ticker = sanitize_ticker(custom_input)

    # Time Period Selector
    period_keys = list(PERIOD_OPTIONS.keys())
    cur_p_idx = period_keys.index(st.session_state.selected_period) if st.session_state.selected_period in period_keys else 4
    st.session_state.selected_period = st.selectbox("Analysis Horizon", period_keys, index=cur_p_idx)

    # Refresh data button
    if st.button("🔄 Force Refresh Market Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.trained_models = None
        st.success("Data cache cleared!")

    st.markdown("---")
    st.markdown("### 💼 Quick Portfolio Status")
    cash_bal, _ = get_virtual_cash()
    st.markdown(f"**Virtual Cash:** {format_currency(cash_bal)}")
    
    # Watchlist count
    wl_df = get_watchlist()
    st.markdown(f"**Watchlist Items:** {len(wl_df)}")

    st.markdown("---")
    st.caption("Developed for Academic Research & Demonstration. Not financial advice.")


# Main Application Layout
st.title(f"📊 {APP_NAME}")
st.markdown(f"*{APP_SUBTITLE}*")

# Prominent Educational Disclaimer
st.markdown(
    f"""
    <div class="disclaimer-box">
        <b>⚠️ ACADEMIC & RESEARCH NOTICE:</b> {DISCLAIMER_TEXT}
    </div>
    """,
    unsafe_allow_html=True
)

ticker = st.session_state.selected_ticker
period_str = PERIOD_OPTIONS.get(st.session_state.selected_period, "1y")

# Fetch market data for selected ticker
with st.spinner(f"Retrieving market data for {ticker}..."):
    try:
        raw_df, summary, warnings = fetch_stock_data(ticker, period=period_str)
        data_error = None
    except Exception as e:
        data_error = str(e)
        raw_df, summary, warnings = None, None, []

if data_error:
    st.error(f"❌ Could not load market data for '{ticker}': {data_error}")
    st.info("💡 Try selecting another stock from the sidebar or verify your internet connection.")
else:
    # Display Warnings if any
    for w in warnings:
        st.warning(f"ℹ️ {w}")

    # Top KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    delta_class = "kpi-delta-pos" if summary["price_change"] >= 0 else "kpi-delta-neg"
    delta_symbol = "▲" if summary["price_change"] >= 0 else "▼"

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">{summary['company_name']}</div>
                <div class="kpi-value">{format_currency(summary['latest_close'])}</div>
                <div class="{delta_class}">{delta_symbol} {format_currency(abs(summary['price_change']))} ({format_percentage(summary['pct_change'])})</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Prior Close</div>
                <div class="kpi-value">{format_currency(summary['prev_close'])}</div>
                <div style="color: #9CA3AF; font-size: 13px;">Trading Date: {summary['latest_date']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Latest Volume</div>
                <div class="kpi-value">{format_number(summary['latest_volume'])}</div>
                <div style="color: #9CA3AF; font-size: 13px;">Total Shares Traded</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">{st.session_state.selected_period} Range High</div>
                <div class="kpi-value">{format_currency(summary['period_high'])}</div>
                <div style="color: #00D09C; font-size: 13px;">Peak Resistance</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">{st.session_state.selected_period} Range Low</div>
                <div class="kpi-value">{format_currency(summary['period_low'])}</div>
                <div style="color: #FF4B4B; font-size: 13px;">Base Support</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Action Toolbar: Add to Watchlist & Data Info
    tool_col1, tool_col2 = st.columns([2, 4])
    with tool_col1:
        if st.button(f"⭐ Add {ticker} to Watchlist", use_container_width=True):
            if add_to_watchlist(ticker, summary["company_name"]):
                st.success(f"Added {ticker} to your local watchlist!")
            else:
                st.info(f"{ticker} is already in your watchlist.")
    with tool_col2:
        st.caption(
            f"📅 **Data Range:** {summary['records_count']} trading days | "
            f"🕒 **Last Retrieved:** {summary['retrieval_timestamp']} | "
            f"*(End-of-day quotes, not live streaming tick data)*"
        )

st.markdown("---")

# Navigation Showcase Section
st.subheader("🧭 Explore Modules")
st.markdown("Navigate to the dedicated analytical pages using the sidebar or the modules below:")

mcol1, mcol2, mcol3, mcol4 = st.columns(4)

with mcol1:
    st.markdown(
        """
        <div class="nav-card">
            <h4>📊 Market Dashboard</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Interactive Plotly candlestick charts, volume dynamics, and configurable moving averages.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with mcol2:
    st.markdown(
        """
        <div class="nav-card">
            <h4>🔍 Stock Explorer</h4>
            <p style="color: #9CA3AF; font-size: 13px;">In-depth technical indicators: RSI 14, MACD momentum, Bollinger Bands, and return distributions.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with mcol3:
    st.markdown(
        """
        <div class="nav-card">
            <h4>🤖 AI Prediction</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Next-trading-day movement direction classification, calibrated probabilities, and feature importance.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with mcol4:
    st.markdown(
        """
        <div class="nav-card">
            <h4>📈 Model Evaluation</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Chronological out-of-sample testing, confusion matrices, and benchmarks against naive baselines.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")
mcol5, mcol6, mcol7, mcol8 = st.columns(4)

with mcol5:
    st.markdown(
        """
        <div class="nav-card">
            <h4>⏱️ Backtesting</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Realistic chronological strategy simulation with transaction costs, slippage, and equity drawdowns.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with mcol6:
    st.markdown(
        """
        <div class="nav-card">
            <h4>💼 Virtual Portfolio</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Educational paper trading account, position tracker, live unrealized P&L, and local SQLite persistence.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with mcol7:
    st.markdown(
        """
        <div class="nav-card">
            <h4>🔭 Long-Term Analysis</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Multi-timeframe moving average trends, historical drawdowns, and volatility regime discussions.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with mcol8:
    st.markdown(
        """
        <div class="nav-card">
            <h4>📚 Project & News</h4>
            <p style="color: #9CA3AF; font-size: 13px;">Verified Yahoo Finance news feed, academic documentation, and system architecture diagrams.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Recent Prediction Audit Section
st.markdown("---")
st.subheader("📜 Recent Prediction Audit Log")
pred_hist = get_prediction_history()

if pred_hist.empty:
    st.info("No predictions logged yet. Visit the **🤖 AI Prediction** page to generate and log model predictions.")
else:
    st.dataframe(
        pred_hist.head(5)[["timestamp", "ticker", "feature_date", "model_name", "predicted_direction", "prob_up", "confidence"]],
        use_container_width=True
    )
