from datetime import date, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=900, show_spinner=False, max_entries=20)
def download_prices(
    start: date,
    end: date,
    first_ticker: str,
    second_ticker: str,
    first_label: str,
    second_label: str,
) -> pd.DataFrame:
    data = yf.download(
        [first_ticker, second_ticker],
        start=start,
        end=end + timedelta(days=1),
        auto_adjust=True,
        progress=False,
    )
    if data.empty:
        return pd.DataFrame()

    prices = data["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    available = [
        ticker for ticker in (first_ticker, second_ticker) if ticker in prices
    ]
    if len(available) != 2:
        return pd.DataFrame()
    prices = prices.loc[:, [first_ticker, second_ticker]].dropna()
    prices.columns = [first_label, second_label]
    return prices


@st.cache_data(ttl=900, show_spinner=False, max_entries=20)
def download_benchmark(start: date, end: date) -> pd.Series:
    data = yf.download(
        "^NSEI",
        start=start,
        end=end + timedelta(days=1),
        auto_adjust=True,
        progress=False,
    )
    if data.empty:
        return pd.Series(dtype=float, name="NIFTY 50")

    benchmark = data["Close"]
    if isinstance(benchmark, pd.DataFrame):
        benchmark = benchmark.iloc[:, 0]
    return benchmark.dropna().rename("NIFTY 50")
