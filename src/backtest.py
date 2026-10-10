import numpy as np
import pandas as pd


def calculate_backtest_metrics(
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
    hedge_ratio = np.polyfit(log_prices[second_asset], log_prices[first_asset], 1)[0]
    spread = log_prices[first_asset] - hedge_ratio * log_prices[second_asset]
    rolling_mean = spread.rolling(window).mean()
    rolling_std = spread.rolling(window).std()
    z_score = (spread - rolling_mean) / rolling_std

    signal = pd.Series(0.0, index=prices.index)
    current_position = 0.0
    holding_days = 0
    for timestamp, z_value in z_score.items():
        if pd.isna(z_value):
            continue
        if current_position == 0:
            if z_value < -threshold:
                current_position, holding_days = 1.0, 0
            elif z_value > threshold:
                current_position, holding_days = -1.0, 0
        else:
            holding_days += 1
            if (
                abs(z_value) <= exit_z
                or abs(z_value) >= stop_loss_z
                or holding_days >= max_holding_days
            ):
                current_position, holding_days = 0.0, 0
        signal.loc[timestamp] = current_position

    position = signal.shift(1).fillna(0)
    spread_change = spread.diff()
    gross_return = position * np.expm1(spread_change)
    turnover = position.diff().abs().fillna(position.abs())
    cost_rate = (transaction_cost_bps + slippage_bps) / 10000
    trading_cost = turnover * cost_rate
    strategy_change = allocation_pct / 100 * gross_return - trading_cost
    equity_curve = initial_capital * (1 + strategy_change.fillna(0)).cumprod()
    strategy_curve = equity_curve / initial_capital * 100
    drawdown = strategy_curve / strategy_curve.cummax() - 1
    trades = pd.DataFrame(
        {
            "Date": position.index[turnover > 0],
            "Action": position.loc[turnover > 0].map(
                {1.0: "Long spread", -1.0: "Short spread", 0.0: "Flat"}
            ).values,
            "Z-score": z_score.loc[turnover > 0].values,
        }
    ).sort_values("Date", ascending=False)

    return {
        "spread": spread,
        "rolling_mean": rolling_mean,
        "rolling_std": rolling_std,
        "z_score": z_score,
        "position": position,
        "strategy_change": strategy_change,
        "strategy_curve": strategy_curve,
        "equity_curve": equity_curve,
        "drawdown": drawdown,
        "trades": trades,
        "hedge_ratio": hedge_ratio,
        "strategy_return": (equity_curve.iloc[-1] / initial_capital - 1) * 100,
        "max_drawdown": drawdown.min() * 100,
        "sharpe": (
            strategy_change.mean() / strategy_change.std() * np.sqrt(252)
            if strategy_change.std()
            else np.nan
        ),
        "trading_cost": trading_cost.sum() * 100,
        "final_capital": equity_curve.iloc[-1],
    }
