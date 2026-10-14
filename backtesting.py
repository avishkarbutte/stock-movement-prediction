"""
StockScope AI - Chronological Backtesting Engine
Simulates out-of-sample directional trading strategies using machine learning predictions.
Incorporates transaction costs, execution slippage, maximum drawdown, and Buy & Hold benchmarks.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from config import BACKTEST_CONFIG


def run_chronological_backtest(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    raw_df: pd.DataFrame,
    initial_capital: float = 100000.0,
    fee_pct: float = 0.001,  # 0.1% transaction cost
    slippage_pct: float = 0.0005  # 0.05% slippage
) -> Dict[str, Any]:
    """
    Execute chronological out-of-sample backtest.

    Strategy Logic:
    - At session t close: if model predicts UP (1), enter/hold long position for next session.
    - If model predicts DOWN (0), stay in cash (0% market exposure).
    - Costs applied on state transitions (Buy / Sell).
    - Benchmark: 100% Buy & Hold from start of test period.

    Returns:
        Dict with equity curves, metrics, trade log, and drawdowns.
    """
    if X_test.empty or y_test.empty:
        raise ValueError("Cannot run backtest on empty test dataset.")

    test_dates = X_test.index
    y_pred = pipeline.predict(X_test)
    y_true = y_test.values

    # Retrieve probability of UP movement if available
    probs_up = (
        pipeline.predict_proba(X_test)[:, 1]
        if hasattr(pipeline, "predict_proba")
        else y_pred.astype(float)
    )

    # Next session actual returns from raw price data
    # For day t, next day return is Close_{t+1} / Close_t - 1
    # raw_df must contain the test_dates
    next_returns = []
    close_prices = []
    
    for dt in test_dates:
        if dt in raw_df.index:
            idx = raw_df.index.get_loc(dt)
            if idx + 1 < len(raw_df):
                c_now = raw_df["Close"].iloc[idx]
                c_next = raw_df["Close"].iloc[idx + 1]
                ret = (c_next - c_now) / c_now
                next_returns.append(ret)
                close_prices.append(c_now)
            else:
                next_returns.append(0.0)
                close_prices.append(raw_df["Close"].iloc[idx])
        else:
            next_returns.append(0.0)
            close_prices.append(100.0)

    next_returns = np.array(next_returns)

    # Simulation tracking
    n_days = len(test_dates)
    strategy_capital = np.zeros(n_days)
    benchmark_capital = np.zeros(n_days)
    positions = np.zeros(n_days)  # 1 = Long, 0 = Cash
    trade_costs = np.zeros(n_days)

    curr_strat_cap = initial_capital
    curr_bench_cap = initial_capital
    prev_pos = 0

    trade_log: List[Dict[str, Any]] = []

    for i in range(n_days):
        signal = int(y_pred[i])  # 1 for Buy/Hold, 0 for Cash
        prob = float(probs_up[i])
        actual = int(y_true[i])
        market_ret = float(next_returns[i])
        dt_str = test_dates[i].strftime("%Y-%m-%d")

        # Did position change? If so, apply fee + slippage
        cost_rate = (fee_pct + slippage_pct)
        step_cost = 0.0

        if signal != prev_pos:
            # Transaction executed
            step_cost = curr_strat_cap * cost_rate
            curr_strat_cap -= step_cost

        # Calculate return for this day
        if signal == 1:
            strat_step_ret = market_ret
        else:
            strat_step_ret = 0.0

        curr_strat_cap *= (1.0 + strat_step_ret)
        curr_bench_cap *= (1.0 + market_ret)

        strategy_capital[i] = curr_strat_cap
        benchmark_capital[i] = curr_bench_cap
        positions[i] = signal
        trade_costs[i] = step_cost

        # Record trade log item
        trade_log.append({
            "Date": dt_str,
            "Signal": "BUY / LONG" if signal == 1 else "CASH",
            "Prob_Up": f"{prob * 100:.1f}%",
            "Actual_Direction": "UP" if actual == 1 else "DOWN/SAME",
            "Correct": "✅" if signal == actual else "❌",
            "Session_Return": f"{market_ret * 100:+.2f}%",
            "Strategy_Balance": f"₹{curr_strat_cap:,.2f}",
        })

        prev_pos = signal

    # Calculate Performance Metrics
    strat_total_return = (strategy_capital[-1] - initial_capital) / initial_capital
    bench_total_return = (benchmark_capital[-1] - initial_capital) / initial_capital

    # Directional Accuracy
    directional_accuracy = float(np.mean(y_pred == y_true))

    # Maximum Drawdown calculation: Peak-to-Trough
    strat_peaks = np.maximum.accumulate(strategy_capital)
    strat_drawdowns = (strategy_capital - strat_peaks) / strat_peaks
    strat_max_dd = float(np.min(strat_drawdowns))

    bench_peaks = np.maximum.accumulate(benchmark_capital)
    bench_drawdowns = (benchmark_capital - bench_peaks) / bench_peaks
    bench_max_dd = float(np.min(bench_drawdowns))

    # Number of trades executed
    pos_changes = np.diff(np.insert(positions, 0, 0))
    num_trades = int(np.sum(np.abs(pos_changes) > 0))

    # Equity curves DataFrame for Plotly
    equity_df = pd.DataFrame({
        "Date": test_dates,
        "AI Strategy": strategy_capital,
        "Buy & Hold Benchmark": benchmark_capital,
        "Strategy Drawdown": strat_drawdowns * 100.0,
        "Benchmark Drawdown": bench_drawdowns * 100.0,
    }).set_index("Date")

    return {
        "initial_capital": initial_capital,
        "final_strategy_capital": float(strategy_capital[-1]),
        "final_benchmark_capital": float(benchmark_capital[-1]),
        "strategy_total_return_pct": float(strat_total_return * 100.0),
        "benchmark_total_return_pct": float(bench_total_return * 100.0),
        "directional_accuracy_pct": float(directional_accuracy * 100.0),
        "strategy_max_drawdown_pct": float(strat_max_dd * 100.0),
        "benchmark_max_drawdown_pct": float(bench_max_dd * 100.0),
        "num_trades": num_trades,
        "total_transaction_costs": float(np.sum(trade_costs)),
        "equity_df": equity_df,
        "trade_log": pd.DataFrame(trade_log),
        "assumptions": {
            "fee_pct": fee_pct * 100.0,
            "slippage_pct": slippage_pct * 100.0,
            "exposure": "Long on 1, 100% Cash on 0",
        }
    }
