import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.backtest import calculate_backtest_metrics
from src.page_helpers import load_page_prices, sidebar_inputs
from src.research import calculate_research_metrics


st.title("Pair analysis")
st.caption("Test whether the selected pair has a stable, mean-reverting relationship.")
settings = sidebar_inputs()
prices = load_page_prices(settings)
if len(prices) < 80:
    st.error("Select a longer date range; at least 80 observations are needed.")
    st.stop()
metrics = calculate_backtest_metrics(
    prices, 60, 2.0, 0.5, 4.0, 120, 100, 10.0, 5.0, 100_000
)
research = calculate_research_metrics(prices, metrics["spread"], 60, 5)

st.info("Screening guide: cointegration and ADF p-values below 0.05, with KPSS above 0.05, support stationarity. These are historical diagnostics, not investment advice.")
columns = st.columns(5)
for column, label, key in zip(
    columns,
    ["Cointegration p-value", "ADF p-value", "KPSS p-value", "Half-life", "Hedge ratio"],
    ["cointegration_pvalue", "adf_pvalue", "kpss_pvalue", "half_life", "hedge_ratio"],
):
    value = research[key] if key in research else metrics[key]
    with column:
        st.metric(label, "—" if pd.isna(value) else f"{value:.4f}" if "value" in key else f"{value:.2f}")

chart = go.Figure()
chart.add_trace(go.Scatter(x=research["rolling_hedge"].index, y=research["rolling_hedge"], name="Rolling hedge ratio"))
chart.update_layout(template="plotly_white", height=420, yaxis_title="Hedge ratio", margin={"l": 55, "r": 30, "t": 40, "b": 35})
st.plotly_chart(chart, width="stretch")

spread_chart = go.Figure()
spread_chart.add_trace(go.Scatter(x=metrics["spread"].index, y=metrics["spread"], name="Spread"))
spread_chart.add_trace(go.Scatter(x=metrics["spread"].index, y=metrics["rolling_mean"], name="Rolling mean"))
spread_chart.update_layout(template="plotly_white", height=420, yaxis_title="Log spread", margin={"l": 55, "r": 30, "t": 40, "b": 35})
st.plotly_chart(spread_chart, width="stretch")
