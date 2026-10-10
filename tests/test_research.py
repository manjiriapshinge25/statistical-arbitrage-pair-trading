import numpy as np
import pandas as pd

from src.research import calculate_research_metrics


def make_prices(periods: int = 220) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=periods, freq="D")
    base = np.linspace(100, 120, periods)
    return pd.DataFrame(
        {
            "Asset A": base * (1 + 0.04 * np.sin(np.arange(periods) / 8)),
            "Asset B": base,
        },
        index=index,
    )


def test_research_metrics_include_forecast_outputs() -> None:
    prices = make_prices()
    spread = np.log(prices["Asset A"]) - np.log(prices["Asset B"])

    result = calculate_research_metrics(prices, spread, window=30, forecast_days=5)

    assert np.isfinite(result["cointegration_pvalue"])
    assert len(result["forecast"]) == 5
    assert len(result["forecast_z"]) == 5
    assert len(result["rolling_hedge"]) == len(prices)
