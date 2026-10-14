# StockScope AI: AI-Based Stock Market Movement Prediction & Analysis System

**StockScope AI** is a full-featured, modular financial analytics and machine learning web application built for academic research and educational demonstration. It analyzes historical stock market data (specifically National Stock Exchange of India / Yahoo Finance tickers), calculates technical analysis indicators, trains predictive machine learning models to classify next-trading-day price direction, performs chronological backtesting with transaction cost simulation, and provides interactive portfolio and watchlist tools.

---

> **⚠️ IMPORTANT EDUCATIONAL DISCLAIMER**
> StockScope AI is developed strictly for academic, research, and educational demonstration purposes. It is **not** a financial advisory tool, automated trading system, or investment recommendation engine. Financial markets are subject to high volatility and risk. Machine learning probability estimates represent statistical patterns in historical data and do **not** guarantee future price movements. Always consult a certified financial advisor before investing.

---

## 🚀 Key Features

1. **Live & Historical Market Dashboard (`1_Market_Dashboard.py`)**:
   - Interactive candlestick and line charts powered by Plotly.
   - Comprehensive KPI cards: Latest Close, Prior Close, Net Change, Volume, 52-Week High & Low.
   - Flexible timeframe selection (1W, 1M, 3M, 6M, 1Y, 2Y, 5Y).
   - Moving average overlays (SMA 10, 20, 50, 200; EMA 12, 26) and volume bars.
   - Quick watchlist and cache refresh.

2. **Stock Explorer & Technical Analysis (`2_Stock_Explorer.py`)**:
   - Multi-indicator calculation: RSI 14, MACD (with signal line and histogram), Bollinger Bands (20, 2 std), Rolling Volatility, Momentum (ROC), and Volume Variations.
   - Indicator educational tooltips explaining mathematical formulas and interpretation.
   - Return distribution histograms and volatility analysis.

3. **AI Prediction Engine (`3_AI_Prediction.py`)**:
   - Next-day price movement direction classification:
     $$\text{Target} = \begin{cases} 1 & \text{if } \text{Close}_{t+1} > \text{Close}_t \\ 0 & \text{otherwise} \end{cases}$$
   - Strict prevention of look-ahead bias: features at time $t$ use only information available up to the market close of day $t$.
   - Output provides predicted direction, probability of upward movement $P(\text{Up})$, probability of downward/unchanged movement $P(\text{Down})$, training period, and top contributing features.

4. **Model Performance Evaluation (`4_Model_Performance.py`)**:
   - Strict chronological train/test split (no random shuffling of time-series data).
   - Standard evaluation metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.
   - Multiple algorithms compared on the identical chronological test period:
     - Logistic Regression (with standardized feature scaling)
     - Random Forest Classifier
     - HistGradientBoostingClassifier
   - Baseline benchmark comparisons (Majority Class Baseline, Previous Day Momentum Baseline) to confirm true machine learning value.

5. **Chronological Backtesting Engine (`5_Backtesting.py`)**:
   - Walk-forward chronological simulation on unseen out-of-sample data.
   - Directional accuracy tracking.
   - Realistic trading simulation incorporating slippage (0.05%) and transaction/brokerage fees (0.10%).
   - Strategy Equity Curve compared against Buy & Hold benchmark with Maximum Drawdown calculation.

6. **Virtual Paper Trading & Watchlist (`6_Virtual_Portfolio.py`)**:
   - Simulated paper trading portfolio backed by local SQLite storage (`data/stockscope.db`).
   - Track cash balance, stock holdings, average purchase price, current value, and unrealized profit/loss.
   - Reset portfolio option with safety confirmation.
   - Export reports as CSV.

7. **Long-Term Trend Analysis (`7_Long_Term_Analysis.py`)**:
   - Multi-timeframe trend breakdown, historical drawdown analysis, rolling volatility regimes, and educational scenario analysis without pseudo price targets.

8. **Explainable AI & News Sentiment (`8_About_Project.py` / Dashboard)**:
   - Feature importance rankings and coefficients.
   - Real-time Yahoo Finance news feed with keyword-based sentiment classification.
   - Complete academic methodology documentation and Mermaid architecture diagrams.

---

## 🛠️ Technology Stack

- **Frontend & UI**: Python, Streamlit, Plotly Express & Graph Objects
- **Data Engineering**: Pandas, NumPy
- **Machine Learning**: Scikit-Learn (LogisticRegression, RandomForestClassifier, HistGradientBoostingClassifier, StandardScaler, Pipeline)
- **Financial Data Provider**: `yfinance` (Yahoo Finance historical market data)
- **Database & Storage**: SQLite3, Local CSV export
- **Automated Testing**: Pytest

---

## 📁 Project Folder Structure

```
stock-prediction/
│
├── app.py                      # Main Streamlit application entry point
├── config.py                   # Global constants, ticker universe, indicator & ML settings
├── requirements.txt            # Python package dependencies
├── README.md                   # Windows installation & user guide
├── PROJECT_DOCUMENTATION.md    # College academic project report & diagrams
├── .gitignore                  # Source control exclusion rules
│
├── data/                       # Local database storage & cached data
│   ├── .gitkeep
│   └── stockscope.db           # SQLite database for portfolio & history
│
├── models/                     # Serialized model artifacts (if saved)
│   └── .gitkeep
│
├── src/                        # Core application modules
│   ├── __init__.py
│   ├── market_data.py          # Data retrieval from yfinance with validation & TTL caching
│   ├── preprocessing.py       # Data cleaning, null checks, validation
│   ├── indicators.py           # Technical indicators (SMA, EMA, RSI, MACD, BB, Volatility)
│   ├── features.py             # Feature engineering without look-ahead bias
│   ├── train_model.py          # ML training pipelines with chronological splits
│   ├── predict.py              # Next-day direction prediction & probabilities
│   ├── evaluation.py           # Classification metrics & baseline models
│   ├── backtesting.py          # Chronological trade simulation & equity curves
│   ├── charts.py               # Professional dark-theme Plotly visualizations
│   ├── storage.py              # SQLite persistence for watchlist, portfolio & predictions
│   ├── news.py                 # News retrieval & sentiment scoring
│   └── utils.py                # Formatting, number conversions, CSV helpers
│
├── pages/                      # Multi-page Streamlit application
│   ├── 1_Market_Dashboard.py   # Overview, charts, volume, indicators
│   ├── 2_Stock_Explorer.py     # In-depth technical analysis & indicator charts
│   ├── 3_AI_Prediction.py      # Next-trading-day ML movement prediction
│   ├── 4_Model_Performance.py  # Model evaluation metrics & confusion matrices
│   ├── 5_Backtesting.py        # Walk-forward backtest simulation & drawdowns
│   ├── 6_Virtual_Portfolio.py  # Educational paper trading & watchlist
│   ├── 7_Long_Term_Analysis.py # Trend analysis, volatility & historical drawdowns
│   └── 8_About_Project.py      # Project documentation & architecture
│
└── tests/                      # Automated unit test suite
    ├── __init__.py
    ├── test_indicators.py      # Tests for technical indicator math
    ├── test_features.py        # Tests for feature engineering & no leakage
    ├── test_predictions.py     # Tests for ML model training & outputs
    ├── test_backtesting.py     # Tests for chronological backtesting calculations
    └── test_storage.py         # Tests for SQLite database CRUD operations
```

---

## 💻 Windows Setup & Installation Guide (Beginner Friendly)

### Prerequisites
* Windows 10 or Windows 11 (64-bit)
* Python 3.10 to 3.14 (Python 3.14 is verified and recommended)
* An active internet connection for downloading market data via Yahoo Finance.

### Step-by-Step Instructions

1. **Open Command Prompt**:
   Press `Windows Key + R`, type `cmd`, and press `Enter`.

2. **Navigate to the Project Directory**:
   ```cmd
   cd "C:\Users\Admin\Downloads\stock prediction"
   ```

3. **Create a Virtual Environment**:
   ```cmd
   py -3.14 -m venv .venv
   ```

4. **Activate the Virtual Environment**:
   ```cmd
   .venv\Scripts\activate
   ```
   *(You should see `(.venv)` appear at the beginning of your command prompt line).*

5. **Install Dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

6. **Run the Application**:
   ```cmd
   streamlit run app.py
   ```

7. **Access the Dashboard**:
   Streamlit will output local URLs. Open your web browser (Chrome, Edge, Firefox) and navigate to:
   ```
   http://localhost:8501
   ```

---

## 🧪 Running Automated Tests

To run the unit test suite and verify technical indicators, feature engineering, no-leakage guarantees, and backtest math:

```cmd
.venv\Scripts\activate
pytest -v
```

---

## 🔍 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `yfinance` download fails or times out | Network firewall, ISP rate limiting, or Yahoo Finance downtime | Click **Refresh Data** button or test another ticker (e.g., `TCS.NS`, `INFY.NS`). |
| "Insufficient historical data" message | Ticker has fewer than required records (e.g. recently listed IPO) | Select a longer period (e.g. 1Y or 2Y) or choose an established stock. |
| Port 8501 already in use | Another instance of Streamlit is running | Run `streamlit run app.py --server.port 8502`. |
| Script execution policy error in PowerShell | PowerShell execution restriction | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or use standard Command Prompt (`cmd.exe`). |

---

## 🎓 Academic Research Methodology

- **Hypothesis**: Historical technical indicators (momentum, volatility, trend, volume) contain non-random predictive signals for the binary price direction of the next trading session.
- **Target Variable**:
  $$y_t = \mathbb{I}(Close_{t+1} > Close_t)$$
- **Leakage Prevention**: Every feature vector at row $t$ is strictly derived from price data up to timestamp $t$. Testing data is partitioned chronologically strictly after training data to simulate true forward-in-time deployment.
- **Evaluation Standards**: Accuracy alone is insufficient due to market regime imbalance; models are rigorously assessed on Precision, Recall, F1-Score, and compared against naïve majority-class and momentum baselines.
