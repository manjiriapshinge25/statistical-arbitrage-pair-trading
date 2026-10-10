import pandas as pd
import streamlit as st

from src.backtest import calculate_backtest_metrics
from src.page_helpers import load_page_prices, sidebar_inputs


st.title("Backtest")
st.caption("Evaluate the selected mean-reversion strategy with execution costs and slippage.")
settings = sidebar_inputs(include_strategy=True)
prices = load_page_prices(settings)
if len(prices) <= settings["window"]:
    st.error(f"The selected range needs more than {settings['window']} observations.")
    st.stop()
metrics = calculate_backtest_metrics(prices, **{key: settings[key] for key in (
    "window", "threshold", "exit_z", "stop_loss_z", "max_holding_days",
    "allocation_pct", "transaction_cost_bps", "slippage_bps", "initial_capital",
)})

columns = st.columns(5)
for column, label, value in zip(
    columns,
    ["Strategy return", "Maximum drawdown", "Sharpe ratio", "Final capital", "Trading costs"],
    [f"{metrics['strategy_return']:.2f}%", f"{metrics['max_drawdown']:.2f}%", "—" if pd.isna(metrics["sharpe"]) else f"{metrics['sharpe']:.2f}", f"₹{metrics['final_capital']:,.0f}", f"{metrics['trading_cost']:.2f}%"],
):
    with column:
        st.metric(label, value)

st.line_chart(
    pd.DataFrame({"Strategy value": metrics["strategy_curve"], "Drawdown": metrics["drawdown"] * 100}),
    y_label="Percent",
    x_label="Date",
)
st.subheader("Signal changes")
st.dataframe(metrics["trades"].head(30), hide_index=True, alt="Backtest signal changes")
