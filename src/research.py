import numpy as np
import pandas as pd
import streamlit as st
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, coint, kpss
from pandas.tseries.offsets import BDay


@st.cache_data(ttl=900, show_spinner=False, max_entries=20)
def calculate_research_metrics(
    prices: pd.DataFrame,
    spread: pd.Series,
    window: int,
    forecast_days: int,
) -> dict[str, object]:
    first_asset, second_asset = prices.columns[:2]
    log_prices = np.log(prices)
    cointegration_stat, cointegration_pvalue, _ = coint(
        log_prices[first_asset],
        log_prices[second_asset],
    )
    adf_stat, adf_pvalue, _, _, _, _ = adfuller(
        spread.dropna(),
        autolag="AIC",
        result_object=False,
    )
    try:
        kpss_stat, kpss_pvalue, _, _ = kpss(
            spread.dropna(),
            regression="c",
            nlags="auto",
            result_object=False,
        )
    except ValueError:
        kpss_stat, kpss_pvalue = np.nan, np.nan

    lagged_spread = spread.shift(1).dropna()
    spread_change = spread.diff().dropna()
    aligned_lagged = lagged_spread.reindex(spread_change.index)
    mean_reversion_speed = np.polyfit(
        aligned_lagged.dropna(),
        spread_change.reindex(aligned_lagged.dropna().index),
        1,
    )[0]
    half_life = (
        -np.log(2) / mean_reversion_speed
        if mean_reversion_speed < 0
        else np.nan
    )

    rolling_hedge = (
        log_prices[first_asset].rolling(window).cov(log_prices[second_asset])
        / log_prices[second_asset].rolling(window).var()
    )
    clean_spread = spread.dropna()
    model = ARIMA(
        clean_spread.reset_index(drop=True),
        order=(1, 0, 0),
        trend="c",
    ).fit()
    forecast_values = model.forecast(steps=forecast_days)
    forecast_index = pd.date_range(
        start=clean_spread.index[-1] + BDay(1),
        periods=forecast_days,
        freq="B",
    )
    forecast = pd.Series(
        np.asarray(forecast_values, dtype=float),
        index=forecast_index,
        name="forecast",
    )
    recent_mean = spread.rolling(window).mean().iloc[-1]
    recent_std = spread.rolling(window).std().iloc[-1]
    forecast_z = (forecast - recent_mean) / recent_std

    return {
        "cointegration_stat": cointegration_stat,
        "cointegration_pvalue": cointegration_pvalue,
        "adf_stat": adf_stat,
        "adf_pvalue": adf_pvalue,
        "kpss_stat": kpss_stat,
        "kpss_pvalue": kpss_pvalue,
        "half_life": half_life,
        "rolling_hedge": rolling_hedge,
        "forecast": forecast,
        "forecast_z": forecast_z,
        "forecast_volatility": spread_change.rolling(window).std().iloc[-1],
    }
