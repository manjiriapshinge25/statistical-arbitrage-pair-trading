import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.backtest import calculate_backtest_metrics
from src.page_helpers import load_page_prices, sidebar_inputs
from src.research import calculate_research_metrics


st.title("Forecasting")
st.caption("Review the experimental ARIMA spread forecast for the selected pair.")
settings = sidebar_inputs()
with st.sidebar:
    forecast_days = st.slider("Forecast horizon", 1, 20, 5, key="forecast_page_days")
prices = load_page_prices(settings)
if len(prices) < 80:
    st.error("Select a longer date range; at least 80 observations are needed.")
    st.stop()
metrics = calculate_backtest_metrics(prices, 60, 2.0, 0.5, 4.0, 120, 100, 10.0, 5.0, 100_000)
research = calculate_research_metrics(prices, metrics["spread"], 60, forecast_days)

st.warning("Forecasts are statistical estimates, not guaranteed price predictions or investment advice.")
columns = st.columns(3)
with columns[0]:
    st.metric("Forecast horizon", f"{forecast_days} trading days")
with columns[1]:
    latest_z = research["forecast_z"].iloc[0]
    st.metric("First forecast z-score", "—" if pd.isna(latest_z) else f"{latest_z:.2f}")
with columns[2]:
    volatility = research["forecast_volatility"]
    st.metric("Recent spread volatility", "—" if pd.isna(volatility) else f"{volatility:.4f}")

figure = go.Figure()
figure.add_trace(go.Scatter(x=metrics["spread"].index, y=metrics["spread"], name="Historical spread"))
figure.add_trace(go.Scatter(x=research["forecast"].index, y=research["forecast"], name="ARIMA forecast", mode="lines+markers"))
figure.update_layout(template="plotly_white", height=500, hovermode="x unified", margin={"l": 55, "r": 30, "t": 40, "b": 35})
st.plotly_chart(figure, width="stretch")
st.dataframe(
    pd.DataFrame({"Forecast spread": research["forecast"], "Forecast z-score": research["forecast_z"]}),
    hide_index=False,
    alt="ARIMA spread forecast",
)
