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
