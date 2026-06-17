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

from screener.data import build_universe, scan_universe
from screener.decouple import (
    crypto_beta,
    human,
    is_tokenized_stock,
    log_returns,
    most_decoupled,
    rank_decoupled,
    select_view,
    strongest_dynamics,
)


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


def _build_plus():
    """_build() + une action tokenisée, un pump aberrant et un listing récent."""
    frames = _build()
    rng = np.random.default_rng(11)
    n = 300
    idx = pd.date_range("2025-01-01", periods=n + 1, freq="4h", tz="UTC")
    frames["rNVDA/USDT"] = _frame(0.003 + rng.normal(0, 0.02, n), idx)    # action tokenisée
    frames["MOON/USDT"] = _frame(0.05 + rng.normal(0, 0.02, n), idx)      # pump aberrant
    frames["NEW/USDT"] = _frame(0.004 + rng.normal(0, 0.02, 100), idx)    # historique court
    return frames


def test_is_tokenized_stock():
    assert is_tokenized_stock("rAAPL")
    assert is_tokenized_stock("rNVDA")
    assert is_tokenized_stock("preOPAI")
    assert is_tokenized_stock("NVDAON")       # straggler curé
    assert not is_tokenized_stock("BTC")
    assert not is_tokenized_stock("RSR")       # crypto en majuscules
    assert not is_tokenized_stock("rsETH")     # casse mixte crypto (LST)
    assert not is_tokenized_stock("SOL")


def test_tokenized_stock_excluded():
    out = rank_decoupled(_build_plus(), rolling=30, min_score=-10)
    assert "rNVDA/USDT" not in set(out["symbol"])


def test_outlier_idio_return_capped():
    frames = _build_plus()
    assert "MOON/USDT" not in set(rank_decoupled(frames, rolling=30, min_score=-10)["symbol"])
    loose = rank_decoupled(frames, rolling=30, min_score=-10, max_idio_ret=1e12)
    assert "MOON/USDT" in set(loose["symbol"])    # sans plafond, l'aberration revient


def test_min_history_guard():
    frames = _build_plus()
    assert "NEW/USDT" not in set(rank_decoupled(frames, rolling=30, min_score=-10)["symbol"])
    short = rank_decoupled(frames, rolling=30, min_score=-10, min_bars=50)
    assert "NEW/USDT" in set(short["symbol"])     # seuil abaissé → réintégré


def test_two_families_views():
    ranked = rank_decoupled(_build(), rolling=30, min_score=-10)
    dec = most_decoupled(ranked, corr_max=0.5, corr_p90_max=1.0)
    dyn = strongest_dynamics(ranked, top=5)
    assert "AUTO/USDT" in set(dec["symbol"])      # décorrélé + dynamique positive
    assert "COUP/USDT" not in set(dec["symbol"])  # trop corrélé pour la famille découplée
    assert dyn.iloc[0]["symbol"] == "AUTO/USDT"   # meilleure dérive propre


def test_select_view_dispatch():
    ranked = rank_decoupled(_build(), rolling=30, min_score=-10)
    assert select_view(ranked, "score", top=2).equals(ranked.head(2).reset_index(drop=True))
    assert "AUTO/USDT" in set(select_view(ranked, "dynamics", top=5)["symbol"])
    dec = select_view(ranked, "decoupled", top=5)
    assert "COUP/USDT" not in set(dec["symbol"])   # corr ~0.99 écarté de la vue découplée


class _FakeEx:
    """Exchange minimal : seul fetch_tickers est utilisé par build_universe."""
    def fetch_tickers(self):
        return {
            "BTC/USDT": {"quoteVolume": 100},
            "rNVDA/USDT": {"quoteVolume": 9999},   # action tokenisée très liquide
            "HYPE/USDT": {"quoteVolume": 50},
            "ETHUP/USDT": {"quoteVolume": 80},     # token à levier
            "SOL/BTC": {"quoteVolume": 70},        # mauvaise quote
        }


def test_build_universe_excludes_tokenized_and_leverage():
    uni = build_universe(_FakeEx(), quote="USDT", top_n=10)
    assert "rNVDA/USDT" not in uni    # action tokenisée écartée malgré le volume
    assert "ETHUP/USDT" not in uni    # levier écarté
    assert "SOL/BTC" not in uni       # quote != USDT
    assert uni == ["BTC/USDT", "HYPE/USDT"]   # triées par volume décroissant


def test_scan_universe_returns_volumes():
    uni, vol = scan_universe(_FakeEx(), quote="USDT", top_n=10)
    assert uni == ["BTC/USDT", "HYPE/USDT"]
    assert vol["HYPE"] == 50 and vol["BTC"] == 100
    assert "rNVDA" not in vol         # action tokenisée absente de la map volume


def test_volume_and_mcap_columns():
    frames = _build()
    vol = {"AUTO": 1_500_000.0, "COUP": 900_000.0}
    mc = {"AUTO": 250_000_000.0}      # clé en majuscules (ticker)
    out = rank_decoupled(frames, rolling=30, min_score=-10, vol_map=vol, mcap_map=mc)
    row = out.set_index("symbol").loc["AUTO/USDT"]
    assert row["vol_24h"] == 1_500_000.0
    assert row["mcap"] == 250_000_000.0
    assert np.isnan(out.set_index("symbol").loc["COUP/USDT"]["mcap"])  # absent → NaN


def test_human_formatter():
    assert human(2_400_000) == "2.4M"
    assert human(16_400_000_000) == "16.4B"
    assert human(168_400) == "168.4K"
    assert human(float("nan")) == "—"
    assert human(0) == "—"


def test_crypto_beta_falls_back_to_btc():
    frames = _build()
    returns = {s: log_returns(df) for s, df in frames.items()}
    del returns["ETH/USDT"]
    bench = crypto_beta(returns)
    pd.testing.assert_series_equal(bench, returns["BTC/USDT"], check_names=False)
