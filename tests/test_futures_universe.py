"""Test hors-ligne de build_futures_universe (stub d'exchange) : filtres RWA + liquidité."""
from screener.data import build_futures_universe


class _StubEx:
    def __init__(self, markets, tickers):
        self.markets = markets
        self._t = tickers

    def fetch_tickers(self, params=None):
        return self._t


def _mk(base, rwa, vol):
    sym = f"{base}/USDT:USDT"
    m = {"symbol": sym, "base": base, "swap": True, "settle": "USDT", "active": True,
         "info": {"isRwa": "true" if rwa else "false"}}
    return sym, m, {"quoteVolume": vol}


def _ex():
    specs = [_mk("BTC", False, 100e6), _mk("ETH", False, 50e6),
             _mk("XAU", True, 5e6), _mk("AAPL", True, 2e6), _mk("SMALL", False, 0.1e6),
             _mk("QQQ", True, 8e6), _mk("TQQQ", True, 3e6),   # indices (paniers) → exclus
             _mk("AMZU", True, 4e6)]                          # mono-action à levier → gardée
    markets = {s: m for s, m, _ in specs}
    tickers = {s: t for s, _, t in specs}
    return _StubEx(markets, tickers)


def test_universe_ranked_and_indices_excluded_by_default():
    u = build_futures_universe(_ex(), top_n=10)
    assert "QQQ/USDT:USDT" not in u and "TQQQ/USDT:USDT" not in u   # indices exclus
    assert "AMZU/USDT:USDT" in u                                    # mono-action à levier gardée
    assert "AAPL/USDT:USDT" in u and "XAU/USDT:USDT" in u           # action & métal gardés


def test_include_indices():
    u = build_futures_universe(_ex(), top_n=10, exclude_index=False)
    assert "QQQ/USDT:USDT" in u and "TQQQ/USDT:USDT" in u


def test_exclude_rwa():
    u = build_futures_universe(_ex(), include_rwa=False)
    assert "XAU/USDT:USDT" not in u and "AAPL/USDT:USDT" not in u
    assert "BTC/USDT:USDT" in u


def test_only_rwa():
    # RWA hors indices : métal (XAU), action (AAPL), mono-action à levier (AMZU) — pas QQQ/TQQQ
    u = build_futures_universe(_ex(), only_rwa=True)
    assert set(u) == {"XAU/USDT:USDT", "AAPL/USDT:USDT", "AMZU/USDT:USDT"}


def test_min_volume_filter():
    u = build_futures_universe(_ex(), min_vol_musd=1.0)
    assert "SMALL/USDT:USDT" not in u        # 0.1M < 1M → écarté
    assert "AAPL/USDT:USDT" in u             # 2M ≥ 1M → gardé
