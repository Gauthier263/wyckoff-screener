"""
test_decouple.py — Vérifie le classement découplage × dynamique autonome.

Scénario synthétique :
  - BTC, ETH : marches aléatoires → définissent la « beta crypto ».
  - COUP : ~ 1.2 × beta crypto + bruit  → fortement corrélé (doit mal scorer).
  - AUTO : marche indépendante avec dérive → décorrélé + dynamique propre (top).
  - DEAD : prix figé → décorrélation artificielle (doit être écarté).
  - USDC : stablecoin → exclu d'office.
"""
import numpy as np
import pandas as pd

from screener.decouple import crypto_beta, log_returns, rank_decoupled


def _frame(returns: np.ndarray, index: pd.DatetimeIndex, start: float = 100.0) -> pd.DataFrame:
    close = start * np.exp(np.cumsum(returns))
    idx = index[: len(close)]
    return pd.DataFrame({"open": close, "high": close, "low": close,
                         "close": close, "volume": 1.0}, index=idx)


def _build():
    rng = np.random.default_rng(7)
    n = 300
    idx = pd.date_range("2025-01-01", periods=n + 1, freq="4h", tz="UTC")

    r_btc = rng.normal(0, 0.02, n)
    r_eth = rng.normal(0, 0.02, n)
    bench = 0.5 * (r_btc + r_eth)

    r_coup = 1.2 * bench + rng.normal(0, 0.002, n)          # quasi colinéaire
    r_auto = 0.004 + rng.normal(0, 0.02, n)                  # dérive propre, indépendante
    r_dead = np.zeros(n)                                     # prix figé
    r_usdc = rng.normal(0, 0.0005, n)

    return {
        "BTC/USDT": _frame(r_btc, idx),
        "ETH/USDT": _frame(r_eth, idx),
        "COUP/USDT": _frame(r_coup, idx),
        "AUTO/USDT": _frame(r_auto, idx),
        "DEAD/USDT": _frame(r_dead, idx),
        "USDC/USDT": _frame(r_usdc, idx),
    }


def test_autonomous_ranks_above_coupled():
    out = rank_decoupled(_build(), rolling=30, min_score=-10)
    assert not out.empty
    syms = list(out["symbol"])
    assert "AUTO/USDT" in syms and "COUP/USDT" in syms
    assert syms.index("AUTO/USDT") < syms.index("COUP/USDT")
    # L'actif autonome est nettement moins corrélé que le colinéaire.
    auto = out.set_index("symbol").loc["AUTO/USDT"]
    coup = out.set_index("symbol").loc["COUP/USDT"]
    assert abs(auto["corr"]) < abs(coup["corr"])
    assert coup["r2"] > 0.8


def test_dead_and_stable_excluded():
    out = rank_decoupled(_build(), rolling=30)
    syms = set(out["symbol"])
    assert "DEAD/USDT" not in syms     # série figée écartée
    assert "USDC/USDT" not in syms     # stablecoin exclu
    assert "BTC/USDT" not in syms      # constituant du panier
    assert "ETH/USDT" not in syms


def test_relative_strength_column():
    frames = _build()
    idx = frames["AUTO/USDT"].index
    rng = np.random.default_rng(3)
    rs_auto = _frame(0.003 + rng.normal(0, 0.01, len(idx) - 1), idx)
    out = rank_decoupled(frames, rolling=30, rs_frames={"AUTO": rs_auto}, min_score=-10)
    row = out.set_index("symbol").loc["AUTO/USDT"]
    assert not np.isnan(row["rs_btc_%"])
    # Pas de paire /BTC fournie pour COUP → colonne NaN.
    assert np.isnan(out.set_index("symbol").loc["COUP/USDT"]["rs_btc_%"])


def test_crypto_beta_falls_back_to_btc():
    frames = _build()
    returns = {s: log_returns(df) for s, df in frames.items()}
    del returns["ETH/USDT"]
    bench = crypto_beta(returns)
    pd.testing.assert_series_equal(bench, returns["BTC/USDT"], check_names=False)
