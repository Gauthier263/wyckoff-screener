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
             _mk("XAU", True, 5e6), _mk("AAPL", True, 2e6), _mk("SMALL", False, 0.1e6)]
    markets = {s: m for s, m, _ in specs}
    tickers = {s: t for s, _, t in specs}
    return _StubEx(markets, tickers)


def test_universe_ranked_and_all_included():
    u = build_futures_universe(_ex(), top_n=10)
    assert u == ["BTC/USDT:USDT", "ETH/USDT:USDT", "XAU/USDT:USDT", "AAPL/USDT:USDT", "SMALL/USDT:USDT"]


def test_exclude_rwa():
    u = build_futures_universe(_ex(), include_rwa=False)
    assert "XAU/USDT:USDT" not in u and "AAPL/USDT:USDT" not in u
    assert "BTC/USDT:USDT" in u


def test_only_rwa():
    u = build_futures_universe(_ex(), only_rwa=True)
    assert set(u) == {"XAU/USDT:USDT", "AAPL/USDT:USDT"}


def test_min_volume_filter():
    u = build_futures_universe(_ex(), min_vol_musd=1.0)
    assert "SMALL/USDT:USDT" not in u        # 0.1M < 1M → écarté
    assert "AAPL/USDT:USDT" in u             # 2M ≥ 1M → gardé
