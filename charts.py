"""
StockScope AI - Charts and Visualizations Module
Creates interactive Plotly figures designed for a modern dark-theme financial dashboard.
"""

from typing import List, Optional, Dict
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import THEME_COLORS


def get_dark_layout_template() -> Dict:
    """Standardized dark layout template for all Plotly charts."""
    return dict(
        paper_bgcolor=THEME_COLORS["bg_dark"],
        plot_bgcolor=THEME_COLORS["card_dark"],
        font=dict(color=THEME_COLORS["text_primary"], family="sans-serif", size=12),
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            gridcolor=THEME_COLORS["grid_color"],
            showgrid=True,
            zerolinecolor=THEME_COLORS["grid_color"],
        ),
        yaxis=dict(
            gridcolor=THEME_COLORS["grid_color"],
            showgrid=True,
            zerolinecolor=THEME_COLORS["grid_color"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        hovermode="x unified",
    )


def create_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    show_sma: Optional[List[int]] = None,
    show_ema: Optional[List[int]] = None,
    show_bb: bool = False
) -> go.Figure:
    """
    Create dual-panel chart: Upper panel candlestick price & overlays; Lower panel volume.
    """
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
        subplot_titles=(f"{ticker} Price Action", "Trading Volume"),
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color=THEME_COLORS["accent_green"],
            decreasing_line_color=THEME_COLORS["accent_red"],
        ),
        row=1,
        col=1,
    )

    # Moving Average Overlays
    colors_map = {
        10: THEME_COLORS["accent_yellow"],
        20: THEME_COLORS["accent_blue"],
        50: THEME_COLORS["accent_purple"],
        200: "#F97316",
        12: "#06B6D4",
        26: "#EC4899",
    }

    if show_sma:
        for p in show_sma:
            col_name = f"SMA_{p}"
            if col_name in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[col_name],
                        mode="lines",
                        name=f"SMA {p}",
                        line=dict(color=colors_map.get(p, "#CBD5E1"), width=1.5),
                    ),
                    row=1,
                    col=1,
                )

    if show_ema:
        for p in show_ema:
            col_name = f"EMA_{p}"
            if col_name in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[col_name],
                        mode="lines",
                        name=f"EMA {p}",
                        line=dict(color=colors_map.get(p, "#94A3B8"), width=1.5, dash="dot"),
                    ),
                    row=1,
                    col=1,
                )

    # Bollinger Bands
    if show_bb and "BB_Upper" in df.columns and "BB_Lower" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_Upper"],
                mode="lines",
                name="BB Upper",
                line=dict(color="rgba(59, 130, 246, 0.4)", width=1),
                showlegend=False,
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_Lower"],
                mode="lines",
                name="Bollinger Bands",
                fill="tonexty",
                fillcolor="rgba(59, 130, 246, 0.08)",
                line=dict(color="rgba(59, 130, 246, 0.4)", width=1),
            ),
            row=1,
            col=1,
        )

    # Volume Subplot
    vol_colors = [
        THEME_COLORS["accent_green"] if c >= o else THEME_COLORS["accent_red"]
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.8,
        ),
        row=2,
        col=1,
    )

    # Layout styling
    fig.update_layout(get_dark_layout_template())
    fig.update_layout(
        height=620,
        xaxis_rangeslider_visible=False,
    )
    return fig


def create_rsi_chart(df: pd.DataFrame, period: int = 14) -> go.Figure:
    """Create interactive RSI oscillator chart with overbought/oversold bands."""
    fig = go.Figure()
    col = f"RSI_{period}"

    if col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                name=f"RSI {period}",
                line=dict(color=THEME_COLORS["accent_purple"], width=2),
            )
        )

    # Overbought reference line (70)
    fig.add_hline(
        y=70,
        line_dash="dash",
        line_color=THEME_COLORS["accent_red"],
        annotation_text="Overbought (70)",
        annotation_position="bottom right",
    )
    # Oversold reference line (30)
    fig.add_hline(
        y=30,
        line_dash="dash",
        line_color=THEME_COLORS["accent_green"],
        annotation_text="Oversold (30)",
        annotation_position="top right",
    )

    fig.update_layout(get_dark_layout_template())
    fig.update_layout(
        title=f"Relative Strength Index (RSI {period})",
        yaxis=dict(range=[0, 100], gridcolor=THEME_COLORS["grid_color"]),
        height=320,
    )
    return fig


def create_macd_chart(df: pd.DataFrame) -> go.Figure:
    """Create MACD line, Signal line, and colored momentum histogram."""
    fig = go.Figure()

    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD"],
                mode="lines",
                name="MACD Line",
                line=dict(color=THEME_COLORS["accent_blue"], width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD_Signal"],
                mode="lines",
                name="Signal Line",
                line=dict(color=THEME_COLORS["accent_yellow"], width=1.5),
            )
        )

    if "MACD_Hist" in df.columns:
        hist_colors = [
            THEME_COLORS["accent_green"] if val >= 0 else THEME_COLORS["accent_red"]
            for val in df["MACD_Hist"]
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["MACD_Hist"],
                name="Histogram",
                marker_color=hist_colors,
                opacity=0.8,
            )
        )

    fig.update_layout(get_dark_layout_template())
    fig.update_layout(title="MACD (12, 26, 9)", height=320)
    return fig


def create_feature_importance_chart(df_importance: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Create horizontal bar chart of top predictive features."""
    top_df = df_importance.head(top_n).iloc[::-1]

    fig = go.Figure(
        go.Bar(
            x=top_df["abs_importance"],
            y=top_df["feature"],
            orientation="h",
            marker=dict(
                color=top_df["abs_importance"],
                colorscale="Tealgrn",
                line=dict(color=THEME_COLORS["card_border"], width=1),
            ),
        )
    )

    fig.update_layout(get_dark_layout_template())
    fig.update_layout(
        title=f"Top {top_n} Important Predictive Features",
        xaxis_title="Relative Importance Score",
        height=400,
    )
    return fig


def create_confusion_matrix_chart(cm_dict: Dict[str, Any]) -> go.Figure:
    """Create 2x2 confusion matrix heatmap."""
    matrix = np.array(cm_dict["matrix"])
    labels_x = ["Pred Down / Flat (0)", "Pred Up (1)"]
    labels_y = ["Actual Down / Flat (0)", "Actual Up (1)"]

    annotations = []
    for i in range(2):
        for j in range(2):
            annotations.append(
                dict(
                    x=labels_x[j],
                    y=labels_y[i],
                    text=f"<b>{matrix[i][j]}</b>",
                    showarrow=False,
                    font=dict(color="#FFFFFF", size=18),
                )
            )

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=labels_x,
            y=labels_y,
            colorscale="Blues",
            showscale=False,
        )
    )

    fig.update_layout(get_dark_layout_template())
    fig.update_layout(
        title="Chronological Test Set Confusion Matrix",
        annotations=annotations,
        height=360,
    )
    return fig


def create_equity_curve_chart(equity_df: pd.DataFrame) -> go.Figure:
    """Create cumulative strategy balance comparison vs buy-and-hold benchmark."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=equity_df.index,
            y=equity_df["AI Strategy"],
            mode="lines",
            name="AI Directional Strategy",
            line=dict(color=THEME_COLORS["accent_green"], width=2.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=equity_df.index,
            y=equity_df["Buy & Hold Benchmark"],
            mode="lines",
            name="Buy & Hold Benchmark",
            line=dict(color=THEME_COLORS["accent_blue"], width=2, dash="dash"),
        )
    )

    fig.update_layout(get_dark_layout_template())
    fig.update_layout(
        title="Equity Growth (Hypothetical ₹100,000 Portfolio)",
        yaxis_title="Portfolio Balance (INR)",
        height=420,
    )
    return fig


def create_drawdown_chart(equity_df: pd.DataFrame) -> go.Figure:
    """Create underwater drawdown curve."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=equity_df.index,
            y=equity_df["Strategy Drawdown"],
            mode="lines",
            name="AI Strategy Drawdown",
            fill="tozeroy",
            line=dict(color=THEME_COLORS["accent_red"], width=1.5),
            fillcolor="rgba(255, 75, 75, 0.2)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=equity_df.index,
            y=equity_df["Benchmark Drawdown"],
            mode="lines",
            name="Benchmark Drawdown",
            line=dict(color="#9CA3AF", width=1.5, dash="dot"),
        )
    )

    fig.update_layout(get_dark_layout_template())
    fig.update_layout(
        title="Historical Drawdown Profile (%)",
        yaxis_title="Drawdown (%)",
        height=300,
    )
    return fig
