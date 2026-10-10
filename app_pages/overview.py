from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.data import download_benchmark, download_prices
from src.research import calculate_research_metrics


PAIR_PRESETS = {
    "HDFC Bank vs Kotak Mahindra Bank": (
        "HDFCBANK.NS",
        "KOTAKBANK.NS",
        "HDFC Bank",
        "Kotak Mahindra Bank",
    ),
    "HDFC Bank vs ICICI Bank": (
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "HDFC Bank",
        "ICICI Bank",
    ),
    "SBI vs Bank of Baroda": (
        "SBIN.NS",
        "BANKBARODA.NS",
        "State Bank of India",
        "Bank of Baroda",
    ),
}

STRATEGY_PRESETS = {
    "Balanced": {
        "window": 60,
        "threshold": 2.0,
        "exit_z": 0.5,
        "stop_loss_z": 4.0,
        "max_holding_days": 120,
        "allocation_pct": 100,
        "transaction_cost_bps": 10.0,
        "slippage_bps": 5.0,
    },
    "Conservative": {
        "window": 90,
        "threshold": 2.5,
        "exit_z": 0.5,
        "stop_loss_z": 3.5,
        "max_holding_days": 90,
        "allocation_pct": 60,
        "transaction_cost_bps": 15.0,
        "slippage_bps": 10.0,
    },
    "Aggressive": {
        "window": 40,
        "threshold": 1.5,
        "exit_z": 0.3,
        "stop_loss_z": 5.0,
        "max_holding_days": 180,
        "allocation_pct": 100,
        "transaction_cost_bps": 5.0,
        "slippage_bps": 5.0,
    },
}


st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="stMetric"] {
        border: 1px solid #e4e7ec;
        border-radius: 6px;
        padding: 10px 14px;
        background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def calculate_pair_metrics(
    prices: pd.DataFrame,
    window: int,
    threshold: float,
    exit_z: float,
    stop_loss_z: float,
    max_holding_days: int,
    allocation_pct: float,
    transaction_cost_bps: float,
    slippage_bps: float,
    initial_capital: float,
) -> dict[str, object]:
    first_asset, second_asset = prices.columns[:2]
    log_prices = np.log(prices)
    hedge_ratio = np.polyfit(
        log_prices[second_asset],
        log_prices[first_asset],
        1,
    )[0]
    spread = (
        log_prices[first_asset]
        - hedge_ratio * log_prices[second_asset]
    )
    rolling_mean = spread.rolling(window).mean()
    rolling_std = spread.rolling(window).std()
    z_score = (spread - rolling_mean) / rolling_std

    signal = pd.Series(0.0, index=prices.index)
    current_position = 0.0
    holding_days = 0
    for timestamp, z_value in z_score.items():
        if pd.isna(z_value):
            signal.loc[timestamp] = 0
            continue
        if current_position == 0:
            if z_value < -threshold:
                current_position = 1.0
                holding_days = 0
            elif z_value > threshold:
                current_position = -1.0
                holding_days = 0
        else:
            holding_days += 1
            should_exit = abs(z_value) <= exit_z
            should_stop = abs(z_value) >= stop_loss_z
            should_expire = holding_days >= max_holding_days
            if should_exit or should_stop or should_expire:
                current_position = 0.0
                holding_days = 0
        signal.loc[timestamp] = current_position

    position = signal.shift(1).fillna(0)

    spread_change = spread.diff()
    gross_strategy_return = position * np.expm1(spread_change)
    turnover = position.diff().abs().fillna(position.abs())
    cost_rate = (transaction_cost_bps + slippage_bps) / 10000
    trading_cost = turnover * cost_rate
    strategy_change = (
        allocation_pct / 100 * gross_strategy_return - trading_cost
    )
    equity_curve = initial_capital * (1 + strategy_change.fillna(0)).cumprod()
    strategy_curve = equity_curve / initial_capital * 100
    cumulative_strategy = np.log(equity_curve / initial_capital)
    cumulative_spread = spread_change.cumsum()
    drawdown = strategy_curve / strategy_curve.cummax() - 1

    entries = position.loc[turnover > 0]
    trades = pd.DataFrame(
        {
            "Date": entries.index,
            "Position": entries.values,
            "Z-score": z_score.reindex(entries.index).values,
        }
    )
    trades["Action"] = trades["Position"].map(
        {1.0: "Long spread", -1.0: "Short spread", 0.0: "Flat"}
    )
    trades = trades[["Date", "Action", "Z-score"]].sort_values(
        "Date", ascending=False
    )

    trade_records = []
    open_trade = None
    for timestamp, new_position in position.items():
        if open_trade is not None and new_position != open_trade["Position"]:
            entry_date = open_trade["Date"]
            period = spread.loc[entry_date:timestamp].diff().fillna(0)
            gross_return = open_trade["Position"] * np.expm1(period.sum())
            trade_records.append(
                {
                    "Entry date": entry_date,
                    "Exit date": timestamp,
                    "Action": (
                        "Long spread"
                        if open_trade["Position"] == 1
                        else "Short spread"
                    ),
                    "Holding days": (timestamp - entry_date).days,
                    "Return": allocation_pct / 100 * gross_return
                    - 2 * cost_rate,
                }
            )
            open_trade = None
        if open_trade is None and new_position != 0:
            open_trade = {"Date": timestamp, "Position": new_position}
    trade_results = pd.DataFrame(trade_records)

    return {
        "spread": spread,
        "rolling_mean": rolling_mean,
        "rolling_std": rolling_std,
        "z_score": z_score,
        "cumulative_strategy": cumulative_strategy,
        "cumulative_spread": cumulative_spread,
        "strategy_curve": strategy_curve,
        "drawdown": drawdown,
        "position": position,
        "trades": trades,
        "strategy_return": (np.exp(cumulative_strategy.iloc[-1]) - 1) * 100,
        "spread_return": (np.exp(cumulative_spread.iloc[-1]) - 1) * 100,
        "volatility": strategy_change.std() * np.sqrt(252) * 100,
        "sharpe": (
            strategy_change.mean() / strategy_change.std() * np.sqrt(252)
            if strategy_change.std()
            else np.nan
        ),
        "latest_z": z_score.iloc[-1],
        "hedge_ratio": hedge_ratio,
        "max_drawdown": drawdown.min() * 100,
        "active_days": int((position != 0).sum()),
        "profitable_days": int((strategy_change > 0).sum()),
        "total_signal_changes": len(trades),
        "equity_curve": equity_curve,
        "trading_cost": trading_cost.sum() * 100,
        "trade_results": trade_results,
        "initial_capital": initial_capital,
        "final_capital": equity_curve.iloc[-1],
        "allocation_pct": allocation_pct,
    }


def add_metric(label: str, value: str) -> None:
    st.metric(label, value)


st.title("Pair trading dashboard")
st.caption("Compare two NSE-listed instruments using a configurable mean-reversion strategy.")

today = date.today()
default_start = today - timedelta(days=365 * 3)

with st.sidebar:
    st.header("Settings")
    pair_choice = st.selectbox("Trading pair", [*PAIR_PRESETS, "Custom pair"])
    if pair_choice == "Custom pair":
        first_ticker = st.text_input("First ticker", value="HDFCBANK.NS")
        second_ticker = st.text_input("Second ticker", value="KOTAKBANK.NS")
        first_label = st.text_input("First label", value="First asset")
        second_label = st.text_input("Second label", value="Second asset")
    else:
        (
            first_ticker,
            second_ticker,
            first_label,
            second_label,
        ) = PAIR_PRESETS[pair_choice]

    strategy_preset = st.selectbox(
        "Strategy preset",
        [*STRATEGY_PRESETS, "Custom"],
        help="Presets configure the signal and execution assumptions below.",
    )
    preset = STRATEGY_PRESETS.get(strategy_preset, STRATEGY_PRESETS["Balanced"])
    start_date = st.date_input("From", value=default_start)
    end_date = st.date_input("To", value=today)
    if strategy_preset == "Custom":
        window = st.slider("Rolling window", min_value=20, max_value=180, value=60, step=10)
        threshold = st.slider("Z-score threshold", min_value=1.0, max_value=3.5, value=2.0, step=0.1, format="%.1f")
        exit_z = st.slider("Exit z-score", min_value=0.0, max_value=1.5, value=0.5, step=0.1, format="%.1f")
        stop_loss_z = st.slider("Stop-loss z-score", min_value=2.5, max_value=6.0, value=4.0, step=0.5, format="%.1f")
        max_holding_days = st.number_input("Maximum holding days", min_value=5, max_value=500, value=120, step=5)
        allocation_pct = st.slider("Capital allocation", min_value=10, max_value=100, value=100, step=10, format="%d%%")
        transaction_cost_bps = st.number_input("Transaction cost (basis points)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        slippage_bps = st.number_input("Slippage (basis points)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
    else:
        window = preset["window"]
        threshold = preset["threshold"]
        exit_z = preset["exit_z"]
        stop_loss_z = preset["stop_loss_z"]
        max_holding_days = preset["max_holding_days"]
        allocation_pct = preset["allocation_pct"]
        transaction_cost_bps = preset["transaction_cost_bps"]
        slippage_bps = preset["slippage_bps"]
        st.caption(
            f"Preset settings: {window}-day window, entry ±{threshold:.1f}, "
            f"exit ±{exit_z:.1f}, {allocation_pct}% allocation."
        )
    initial_capital = st.number_input(
        "Initial capital",
        min_value=1_000.0,
        max_value=100_000_000.0,
        value=100_000.0,
        step=10_000.0,
    )
    run_research = st.toggle(
        "Run research analysis",
        value=False,
        help="Runs cointegration, stationarity, hedge-ratio, and ARIMA diagnostics.",
    )
    forecast_days = st.slider(
        "Forecast horizon",
        min_value=1,
        max_value=20,
        value=5,
        disabled=not run_research,
    )
    if st.button("Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

first_ticker = first_ticker.strip().upper()
second_ticker = second_ticker.strip().upper()
first_label = first_label.strip() or "First asset"
second_label = second_label.strip() or "Second asset"

if not first_ticker or not second_ticker:
    st.error("Enter both ticker symbols.")
    st.stop()
if first_ticker == second_ticker:
    st.error("Choose two different ticker symbols.")
    st.stop()
if start_date >= end_date:
    st.error("Choose a valid date range.")
    st.stop()

try:
    prices = download_prices(
        start_date,
        end_date,
        first_ticker,
        second_ticker,
        first_label,
        second_label,
    )
    benchmark = download_benchmark(start_date, end_date)
except Exception as exc:
    st.error(
        "Data download failed. Check the ticker symbols and your network connection. "
        f"Provider error: {exc}"
    )
    st.stop()

if prices.empty:
    st.error(
        f"No price data was returned for {first_ticker} and {second_ticker}. "
        "Use Yahoo Finance ticker symbols, such as HDFCBANK.NS."
    )
    st.stop()
if len(prices) <= window:
    st.error(
        f"The selected range has only {len(prices)} observations, but the "
        f"strategy needs more than the {window}-day rolling window."
    )
    st.stop()

metrics = calculate_pair_metrics(
    prices,
    window,
    threshold,
    exit_z,
    stop_loss_z,
    max_holding_days,
    allocation_pct,
    transaction_cost_bps,
    slippage_bps,
    initial_capital,
)
latest_z = metrics["latest_z"]
latest_position = metrics["position"].iloc[-1]
if latest_position == 1:
    signal_label = "Long spread"
    signal_explanation = (
        f"{first_label} is relatively cheap versus {second_label}."
    )
elif latest_position == -1:
    signal_label = "Short spread"
    signal_explanation = (
        f"{first_label} is relatively expensive versus {second_label}."
    )
else:
    signal_label = "Neutral"
    signal_explanation = "No active trading position is open."

if pd.isna(latest_z):
    signal_explanation = "Not enough observations to calculate the latest z-score."

st.subheader("Current signal")
with st.container(border=True):
    signal_columns = st.columns(3)
    with signal_columns[0]:
        st.metric("Signal", signal_label)
    with signal_columns[1]:
        st.metric("Latest z-score", "—" if pd.isna(latest_z) else f"{latest_z:.2f}")
    with signal_columns[2]:
        st.metric("Latest trading date", prices.index[-1].strftime("%Y-%m-%d"))
        st.caption(signal_explanation)

metric_columns = st.columns(5)
with metric_columns[0]:
    st.metric("Strategy return", f"{metrics['strategy_return']:.2f}%", border=True)
with metric_columns[1]:
    st.metric("NIFTY 50 return", "—" if benchmark.empty else f"{(benchmark.iloc[-1] / benchmark.iloc[0] - 1) * 100:.2f}%", border=True)
with metric_columns[2]:
    st.metric("Maximum drawdown", f"{metrics['max_drawdown']:.2f}%", border=True)
with metric_columns[3]:
    sharpe = metrics["sharpe"]
    st.metric("Sharpe ratio", "—" if pd.isna(sharpe) else f"{sharpe:.2f}", border=True)
with metric_columns[4]:
    st.metric("Signal changes", str(metrics["total_signal_changes"]), border=True)

spread = metrics["spread"]
rolling_mean = metrics["rolling_mean"]
rolling_std = metrics["rolling_std"]
cumulative_strategy = metrics["cumulative_strategy"]
cumulative_spread = metrics["cumulative_spread"]
drawdown = metrics["drawdown"]
trades = metrics["trades"]
trade_results = metrics["trade_results"]

figure = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=(
        "Normalised prices",
        "Spread and trading bands",
        "Cumulative performance",
        "Strategy drawdown",
    ),
)

normalised = prices / prices.iloc[0] * 100
for column in normalised.columns:
    figure.add_trace(
        go.Scatter(x=normalised.index, y=normalised[column], name=column),
        row=1,
        col=1,
    )

figure.add_trace(
    go.Scatter(x=spread.index, y=spread, name="Spread", line={"color": "#344054"}),
    row=2,
    col=1,
)
figure.add_trace(
    go.Scatter(
        x=spread.index,
        y=rolling_mean + threshold * rolling_std,
        name="Upper band",
        line={"color": "#98A2B3", "dash": "dot"},
    ),
    row=2,
    col=1,
)
figure.add_trace(
    go.Scatter(
        x=spread.index,
        y=rolling_mean - threshold * rolling_std,
        name="Lower band",
        line={"color": "#98A2B3", "dash": "dot"},
    ),
    row=2,
    col=1,
)
figure.add_trace(
    go.Scatter(
        x=cumulative_strategy.index,
        y=np.exp(cumulative_strategy) * 100,
        name="Strategy",
        line={"color": "#1570EF"},
    ),
    row=3,
    col=1,
)
if not benchmark.empty:
    benchmark_normalised = benchmark / benchmark.iloc[0] * 100
    figure.add_trace(
        go.Scatter(
            x=benchmark_normalised.index,
            y=benchmark_normalised,
            name="NIFTY 50",
            line={"color": "#F79009", "dash": "dash"},
        ),
        row=3,
        col=1,
    )
figure.add_trace(
    go.Scatter(
        x=drawdown.index,
        y=drawdown * 100,
        name="Drawdown",
        fill="tozeroy",
        line={"color": "#F04438"},
    ),
    row=4,
    col=1,
)
figure.add_trace(
    go.Scatter(
        x=cumulative_spread.index,
        y=np.exp(cumulative_spread) * 100,
        name="Spread value",
        line={"color": "#98A2B3"},
    ),
    row=3,
    col=1,
)

long_entries = trades.loc[trades["Action"] == "Long spread", "Date"]
short_entries = trades.loc[trades["Action"] == "Short spread", "Date"]
figure.add_trace(
    go.Scatter(
        x=long_entries,
        y=spread.reindex(long_entries),
        mode="markers",
        name="Long entry",
        marker={"color": "#12B76A", "size": 8, "symbol": "triangle-up"},
    ),
    row=2,
    col=1,
)
figure.add_trace(
    go.Scatter(
        x=short_entries,
        y=spread.reindex(short_entries),
        mode="markers",
        name="Short entry",
        marker={"color": "#F04438", "size": 8, "symbol": "triangle-down"},
    ),
    row=2,
    col=1,
)

figure.update_layout(
    height=1000,
    template="plotly_white",
    hovermode="x unified",
    margin={"l": 55, "r": 180, "t": 55, "b": 35},
    legend={
        "orientation": "v",
        "x": 1.02,
        "y": 1,
        "xanchor": "left",
        "yanchor": "top",
        "font": {"size": 10},
    },
)
figure.update_yaxes(showgrid=True, gridcolor="#F2F4F7")
st.plotly_chart(figure, width="stretch")

st.subheader("Performance summary")
summary_columns = st.columns(5)
with summary_columns[0]:
    st.metric("Annualised volatility", f"{metrics['volatility']:.2f}%")
with summary_columns[1]:
    st.metric("Final capital", f"₹{metrics['final_capital']:,.0f}")
with summary_columns[2]:
    st.metric("Trading costs", f"{metrics['trading_cost']:.2f}%")
with summary_columns[3]:
    st.metric("Completed trades", f"{len(trade_results):,}")
with summary_columns[4]:
    if trade_results.empty:
        trade_win_rate = 0.0
    else:
        trade_win_rate = (trade_results["Return"] > 0).mean() * 100
    st.metric("Trade win rate", f"{trade_win_rate:.1f}%")

st.subheader("Recent signal changes")
st.dataframe(
    trades.head(12),
    column_config={
        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
    },
    hide_index=True,
    alt="Recent pair-trading signal changes",
)

st.subheader("Completed trades")
if trade_results.empty:
    st.caption("No completed trades are available for this date range and configuration.")
else:
    st.dataframe(
        trade_results.sort_values("Exit date", ascending=False),
        column_config={
            "Entry date": st.column_config.DateColumn("Entry date", format="YYYY-MM-DD"),
            "Exit date": st.column_config.DateColumn("Exit date", format="YYYY-MM-DD"),
            "Return": st.column_config.NumberColumn("Return", format="%.2f%%"),
        },
        hide_index=True,
        alt="Completed pair-trading results",
    )

export_data = prices.join(
    pd.DataFrame(
        {
            "Spread": metrics["spread"],
            "Z-score": metrics["z_score"],
            "Position": metrics["position"],
            "Strategy value": metrics["strategy_curve"],
            "Drawdown": metrics["drawdown"] * 100,
        }
    )
)
if not benchmark.empty:
    export_data["NIFTY 50"] = benchmark.reindex(export_data.index)

st.download_button(
    "Download analysis data",
    data=export_data.to_csv(index_label="Date").encode("utf-8"),
    file_name="pair_trading_analysis.csv",
    mime="text/csv",
    icon=":material/download:",
)

st.caption(
    f"Hedge ratio: {metrics['hedge_ratio']:.4f} · "
    f"Data source: Yahoo Finance · Cached for 15 minutes"
)

if run_research:
    st.subheader("Research analysis")
    try:
        research = calculate_research_metrics(
            prices,
            metrics["spread"],
            window,
            forecast_days,
        )
    except Exception as exc:
        st.error(
            "Research analysis failed. Confirm that the selected range contains "
            f"enough clean observations. Details: {exc}"
        )
    else:
        st.caption(
            "Research diagnostics are historical estimates, not investment advice. "
            "A p-value below 0.05 is commonly used as a screening threshold."
        )
        research_columns = st.columns(5)
        with research_columns[0]:
            pvalue = research["cointegration_pvalue"]
            st.metric(
                "Cointegration p-value",
                "—" if pd.isna(pvalue) else f"{pvalue:.4f}",
            )
        with research_columns[1]:
            pvalue = research["adf_pvalue"]
            st.metric("ADF p-value", "—" if pd.isna(pvalue) else f"{pvalue:.4f}")
        with research_columns[2]:
            pvalue = research["kpss_pvalue"]
            st.metric("KPSS p-value", "—" if pd.isna(pvalue) else f"{pvalue:.4f}")
        with research_columns[3]:
            half_life = research["half_life"]
            st.metric(
                "Spread half-life",
                "—" if pd.isna(half_life) else f"{half_life:.1f} days",
            )
        with research_columns[4]:
            volatility = research["forecast_volatility"]
            st.metric(
                "Spread volatility",
                "—" if pd.isna(volatility) else f"{volatility:.4f}",
            )

        research_figure = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=False,
            vertical_spacing=0.15,
            subplot_titles=("Rolling hedge ratio", "ARIMA spread forecast"),
        )
        research_figure.add_trace(
            go.Scatter(
                x=research["rolling_hedge"].index,
                y=research["rolling_hedge"],
                name="Rolling hedge ratio",
            ),
            row=1,
            col=1,
        )
        forecast_index = pd.date_range(
            start=spread.index[-1] + pd.Timedelta(days=1),
            periods=forecast_days,
            freq="B",
        )
        research_figure.add_trace(
            go.Scatter(
                x=spread.index[-window:],
                y=spread.iloc[-window:],
                name="Observed spread",
            ),
            row=2,
            col=1,
        )
        research_figure.add_trace(
            go.Scatter(
                x=forecast_index,
                y=research["forecast"],
                name="ARIMA forecast",
                line={"color": "#1570EF", "dash": "dash"},
            ),
            row=2,
            col=1,
        )
        research_figure.update_layout(
            height=650,
            template="plotly_white",
            hovermode="x unified",
            margin={"l": 55, "r": 180, "t": 55, "b": 35},
            legend={
                "orientation": "v",
                "x": 1.02,
                "y": 1,
                "xanchor": "left",
                "yanchor": "top",
                "font": {"size": 10},
            },
        )
        st.plotly_chart(
            research_figure,
            width="stretch",
        )
        forecast_table = pd.DataFrame(
            {
                "Forecast date": forecast_index,
                "Forecast spread": research["forecast"].to_numpy(),
                "Forecast z-score": research["forecast_z"].to_numpy(),
            }
        )
        st.dataframe(
            forecast_table,
            column_config={
                "Forecast date": st.column_config.DateColumn(
                    "Forecast date",
                    format="YYYY-MM-DD",
                ),
                "Forecast spread": st.column_config.NumberColumn(
                    "Forecast spread",
                    format="%.5f",
                ),
                "Forecast z-score": st.column_config.NumberColumn(
                    "Forecast z-score",
                    format="%.2f",
                ),
            },
            hide_index=True,
            alt="ARIMA spread forecast and forecast z-score",
        )
