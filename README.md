# AI-Driven Pair Trading & Financial Analytics Dashboard

An end-to-end financial analytics project exploring statistical arbitrage, pair trading, time-series analysis, forecasting, and backtesting through an interactive Streamlit dashboard.

<p align="center">
  <a href="https://statistical-arbitrage-pair-trading-8pt9dnatsxudbbd7b4xw7.streamlit.app/">
    <img src="https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Live Streamlit Demo">
  </a>
  &nbsp;
  <a href="https://github.com/manjiriapshinge25/statistical-arbitrage-pair-trading">
    <img src="https://img.shields.io/badge/GitHub-Source%20Code-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Repository">
  </a>
</p>

## 🚀 Live Demo

Explore the interactive dashboard here:

**[Open the Pair Trading Dashboard](https://statistical-arbitrage-pair-trading-8pt9dnatsxuddbbd7b4xw7.streamlit.app/)**

The dashboard includes:
- Overview of strategy performance and current trading signals
- Pair analysis with spread and statistical analysis
- Backtesting and performance evaluation
- Forecasting and financial analytics

## 📌 Project Overview

Pair trading is a statistical arbitrage strategy that seeks to capitalize on relative price movements between two historically related financial assets.

This project combines financial data analysis, statistical modeling, time-series methods, and interactive visualization to investigate asset relationships, generate trading signals, and evaluate historical strategy performance.

The dashboard supports analysis of Indian banking equities, including HDFC Bank and Kotak Mahindra Bank.

## ✨ Key Features

- **Overview Dashboard:** View strategy signals, Z-scores, returns, maximum drawdown, and Sharpe ratio.
- **Pair Analysis:** Investigate relationships between assets and examine spread behavior.
- **Statistical Arbitrage:** Explore spread deviations and Z-score-based trading signals.
- **Backtesting:** Evaluate historical strategy performance using metrics and visualizations.
- **Forecasting:** Explore time-series forecasting visualizations.
- **Interactive Controls:** Configure trading pairs, date ranges, strategy presets, and initial capital.
- **Research Notebooks:** Explore financial analytics and model development.

## 🛠️ Technology Stack

| Technology       | Purpose                              |
| ---------------- | ------------------------------------ |
| Python           | Core programming language            |
| Pandas           | Data manipulation and analysis       |
| NumPy            | Numerical computation                |
| Statsmodels      | Statistical and time-series modeling |
| Plotly           | Interactive visualizations           |
| Streamlit        | Web application and dashboard        |
| yfinance         | Historical financial market data     |
| Jupyter Notebook | Research and experimentation         |

## 📂 Project Structure

```text
statistical-arbitrage-pair-trading/
├── app_pages/
│   ├── overview.py
│   ├── pair_analysis.py
│   ├── backtest.py
│   └── forecasting.py
├── src/
│   ├── config.py
│   ├── data.py
│   ├── page_helpers.py
│   ├── research.py
│   └── backtest.py
├── tests/
│   └── test_research.py
├── AI-Driven Pair Trading & Financial Analytics Dashboard.ipynb
├── pair_trading_dashboard.ipynb
├── pair_trading_app.py
├── requirements.txt
└── .gitignore
```

## 🔬 Analytical Methodology

1. **Data Collection:** Retrieve historical financial market data.
2. **Exploratory Analysis:** Examine price movements and relationships between assets.
3. **Statistical Analysis:** Investigate cointegration and estimate relationships between selected assets.
4. **Spread Construction:** Analyze relative price movements through a spread.
5. **Signal Generation:** Use spread behavior and Z-scores to explore potential trading signals.
6. **Forecasting:** Apply time-series forecasting methods where appropriate.
7. **Backtesting:** Evaluate historical strategy performance.
8. **Visualization:** Present analytical results through interactive charts.

## 📊 Performance Metrics

The dashboard displays metrics such as:

- Strategy return
- Benchmark return
- Maximum drawdown
- Sharpe ratio
- Latest trading signal and Z-score
- Number of signal changes

Results depend on the selected assets, date range, strategy configuration, and underlying calculations. Historical performance does not guarantee future returns.

## 💻 Installation and Usage

### Prerequisites

- Python 3.10 or a compatible version
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/manjiriapshinge25/statistical-arbitrage-pair-trading.git
cd statistical-arbitrage-pair-trading
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run pair_trading_app.py
```

Open the local URL displayed in your terminal.

## 🧪 Testing

The repository includes a `tests/` directory for research-related tests.

Run the tests with:

```bash
python -m pytest tests/
```

Install `pytest` separately if it is not included in the dependencies.

## 🎯 Learning Objectives

This project explores practical applications of:

- Statistical arbitrage and pair trading
- Time-series analysis and cointegration
- Financial data analysis
- Trading signal generation
- Forecasting and backtesting
- Interactive dashboard development

## ⚠️ Limitations and Disclaimer

Historical relationships between assets can change over time. Backtesting results do not guarantee future performance. Real-world trading also involves transaction costs, slippage, liquidity constraints, execution risk, and changing market conditions.

This project is intended for educational and analytical purposes only. It does not constitute financial advice or a recommendation to buy or sell securities.

## 👩‍💻 Author

**Manjiri Apshinge**

M.Sc. Data Science | NMIMS

- GitHub: [@manjiriapshinge25](https://github.com/manjiriapshinge25)
- Repository: [AI-Driven Pair Trading & Financial Analytics Dashboard](https://github.com/manjiriapshinge25/statistical-arbitrage-pair-trading)
- Live Demo: [Open Streamlit Dashboard](https://statistical-arbitrage-pair-trading-8pt9dnatsxuddbbd7b4xw7.streamlit.app/)

---

*Exploring the intersection of data science, statistical modeling, and financial analytics.*
