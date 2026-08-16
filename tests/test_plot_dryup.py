"""Smoke test du rendu SupplyDryup (hors-ligne : df + OI fournis, aucun réseau)."""
import os

import matplotlib
matplotlib.use("Agg")
import pandas as pd

from screener.window import detect_supply_dryup
from screener.plot import plot_supply_dryup
from test_window import _df, _spring_coil


def test_plot_supply_dryup_smoke(tmp_path):
    df = _df(_spring_coil())
    dry = detect_supply_dryup(df, lookback=40)
    assert dry.is_valid  # coil synthétique valide (cf. test_window)

    ohlcv = df[["open", "high", "low", "close", "volume"]]
    # OI coin factice (bougies plates) sur l'index des barres → panneau OI sans réseau
    oi = pd.DataFrame({"open": df["close"], "high": df["close"], "low": df["close"],
                       "close": df["close"]}, index=df.index)

    out = plot_supply_dryup("BTC/USDT", "1h", dry, str(tmp_path / "dryup.png"),
                            df=ohlcv, oi_ohlc=oi)
    assert os.path.exists(out) and os.path.getsize(out) > 0
