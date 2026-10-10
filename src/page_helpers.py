from datetime import date, timedelta

import streamlit as st

from src.config import PAIR_PRESETS, STRATEGY_PRESETS
from src.data import download_prices


def sidebar_inputs(include_strategy: bool = False) -> dict[str, object]:
    today = date.today()
    with st.sidebar:
        st.header("Analysis settings")
        pair_choice = st.selectbox("Trading pair", [*PAIR_PRESETS, "Custom pair"], key="shared_pair")
        if pair_choice == "Custom pair":
            first_ticker = st.text_input("First ticker", "HDFCBANK.NS", key="shared_first_ticker")
            second_ticker = st.text_input("Second ticker", "KOTAKBANK.NS", key="shared_second_ticker")
            first_label = st.text_input("First label", "First asset", key="shared_first_label")
            second_label = st.text_input("Second label", "Second asset", key="shared_second_label")
        else:
            first_ticker, second_ticker, first_label, second_label = PAIR_PRESETS[pair_choice]
        start_date = st.date_input("From", today - timedelta(days=365 * 3), key="shared_start")
        end_date = st.date_input("To", today, key="shared_end")
        values = {
            "first_ticker": first_ticker.strip().upper(),
            "second_ticker": second_ticker.strip().upper(),
            "first_label": first_label.strip() or "First asset",
            "second_label": second_label.strip() or "Second asset",
            "start_date": start_date,
            "end_date": end_date,
        }
        if include_strategy:
            preset_name = st.selectbox("Strategy preset", [*STRATEGY_PRESETS, "Custom"], key="shared_strategy")
            preset = STRATEGY_PRESETS.get(preset_name, STRATEGY_PRESETS["Balanced"])
            if preset_name == "Custom":
                values.update(
                    window=st.slider("Rolling window", 20, 180, 60, 10, key="shared_window"),
                    threshold=st.slider("Entry z-score", 1.0, 3.5, 2.0, 0.1, key="shared_threshold"),
                    exit_z=st.slider("Exit z-score", 0.0, 1.5, 0.5, 0.1, key="shared_exit"),
                    stop_loss_z=st.slider("Stop-loss z-score", 2.5, 6.0, 4.0, 0.5, key="shared_stop"),
                    max_holding_days=st.number_input("Maximum holding days", 5, 500, 120, 5, key="shared_holding"),
                    allocation_pct=st.slider("Capital allocation", 10, 100, 100, 10, key="shared_allocation"),
                    transaction_cost_bps=st.number_input("Transaction cost (bps)", 0.0, 100.0, 10.0, 1.0, key="shared_cost"),
                    slippage_bps=st.number_input("Slippage (bps)", 0.0, 100.0, 5.0, 1.0, key="shared_slippage"),
                )
            else:
                values.update(preset)
            values["initial_capital"] = st.number_input("Initial capital", 1_000.0, 100_000_000.0, 100_000.0, 10_000.0, key="shared_capital")
    return values


def load_page_prices(settings: dict[str, object]):
    if settings["start_date"] >= settings["end_date"]:
        st.error("Choose a valid date range.")
        st.stop()
    if not settings["first_ticker"] or not settings["second_ticker"]:
        st.error("Enter both ticker symbols.")
        st.stop()
    if settings["first_ticker"] == settings["second_ticker"]:
        st.error("Choose two different ticker symbols.")
        st.stop()
    try:
        prices = download_prices(
            settings["start_date"],
            settings["end_date"],
            settings["first_ticker"],
            settings["second_ticker"],
            settings["first_label"],
            settings["second_label"],
        )
    except Exception as exc:
        st.error(f"Data download failed: {exc}")
        st.stop()
    if prices.empty:
        st.error("No price data was returned for the selected pair.")
        st.stop()
    return prices
