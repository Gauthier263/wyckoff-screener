"""Tests hors-ligne des parsers de `screener.htf.sources` (aucun appel réseau)."""
import pandas as pd

from screener.htf import sources as S


def test_parse_leaderboard_trie_par_equity_et_tronque():
    payload = {"leaderboardRows": [
        {"ethAddress": "0xa", "accountValue": "100"},
        {"ethAddress": "0xb", "accountValue": "9000"},
        {"ethAddress": "0xc", "accountValue": "500"},
        {"accountValue": "1e9"},            # sans adresse -> ignoré
        {"ethAddress": "0xd", "accountValue": "n/a"},  # valeur illisible -> ignoré
    ]}
    assert S._parse_leaderboard(payload, top_n=2) == ["0xb", "0xc"]
    assert S._parse_leaderboard({}, 5) == []


def test_parse_clearinghouse_signe_et_prix_de_liquidation():
    states = [
        {"assetPositions": [
            {"position": {"coin": "BTC", "szi": "-2.5", "entryPx": "60000",
                          "liquidationPx": "75000", "leverage": {"type": "cross", "value": 20}}},
            {"position": {"coin": "ETH", "szi": "10", "entryPx": "2000",
                          "liquidationPx": "1500", "leverage": {"type": "iso", "value": 5}}},
        ]},
        {"assetPositions": [
            {"position": {"coin": "BTC", "szi": "4", "entryPx": "58000",
                          "liquidationPx": None, "leverage": {"type": "iso", "value": 3}}},
            {"position": {"coin": "BTC", "szi": "0", "entryPx": "1"}},  # position close
        ]},
    ]
    df = S._parse_clearinghouse(states, "BTC")
    assert len(df) == 2
    assert list(df["side"]) == ["short", "long"]
    assert df.loc[0, "liq_px"] == 75000.0
    assert pd.isna(df.loc[1, "liq_px"])     # pas de prix de liquidation renvoyé
    assert df.loc[0, "notional"] == 2.5 * 60000


def test_parse_clearinghouse_vide():
    df = S._parse_clearinghouse([], "BTC")
    assert df.empty and "liq_px" in df.columns


def test_parse_realized_liquidations_trie_par_prix():
    payload = {"clusters": [
        {"price": 61000.0, "notional": 1.0, "long_notional": 1.0, "short_notional": 0.0,
         "count": 3, "dominant_side": "long"},
        {"price": 59000.0, "notional": 2.0, "long_notional": 0.0, "short_notional": 2.0,
         "count": 5, "dominant_side": "short"},
    ]}
    df = S._parse_realized_liquidations(payload)
    assert list(df["price"]) == [59000.0, 61000.0]
    assert S._parse_realized_liquidations(None).empty


def test_parse_deribit_et_max_pain():
    payload = {"result": [
        {"instrument_name": "BTC-26MAR27-60000-C", "open_interest": 100, "mark_iv": 50,
         "underlying_price": 61000},
        {"instrument_name": "BTC-26MAR27-60000-P", "open_interest": 20, "mark_iv": 50,
         "underlying_price": 61000},
        {"instrument_name": "BTC-26MAR27-70000-C", "open_interest": 5, "mark_iv": 55,
         "underlying_price": 61000},
        {"instrument_name": "BTC-PERPETUAL", "open_interest": 1},   # pas une option
    ]}
    opts = S._parse_deribit_options(payload)
    assert len(opts) == 3
    assert set(opts["type"]) == {"call", "put"}
    # 60000 : calls hors monnaie (0) + puts hors monnaie (0) = douleur nulle -> minimum
    assert S.max_pain(opts) == 60000.0
    walls = S.strike_walls(opts, top_n=1)
    assert walls.loc[0, "strike"] == 60000.0
    assert walls.loc[0, "oi"] == 120.0
    assert S.max_pain(pd.DataFrame()) is None


def test_parse_macro_calendar_filtre_devise_et_impact():
    payload = [
        {"title": "CPI m/m", "country": "USD", "date": "2026-11-24T08:30:00-05:00",
         "impact": "High", "forecast": "0.2%", "previous": "0.3%"},
        {"title": "Retail Sales", "country": "NZD", "date": "2026-11-24T16:45:00-05:00",
         "impact": "High"},
        {"title": "Crude Inventories", "country": "USD", "date": "2026-11-25T10:30:00-05:00",
         "impact": "Low"},
        {"title": "sans date", "country": "USD", "impact": "High"},
    ]
    df = S._parse_macro_calendar(payload)
    assert len(df) == 1 and df.loc[0, "title"] == "CPI m/m"
    assert df.loc[0, "time"].tzname() == "UTC"
    assert len(S._parse_macro_calendar(payload, currencies=(), impacts=())) == 3


def test_parse_yahoo_chart():
    payload = {"chart": {"result": [{
        "timestamp": [1795000000, 1795086400],
        "indicators": {"quote": [{"open": [1, 2], "high": [3, 4], "low": [0.5, 1.5],
                                  "close": [2, 3], "volume": [10, 20]}]}}]}}
    df = S._parse_yahoo_chart(payload)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 2 and df["close"].iloc[-1] == 3
    assert S._parse_yahoo_chart({}).empty


def test_parse_fear_greed_ordonne():
    payload = {"data": [{"value": "11", "timestamp": "1795392000"},
                        {"value": "20", "timestamp": "1795305600"}]}
    s = S._parse_fng(payload)
    assert list(s) == [20.0, 11.0]          # réordonné du plus ancien au plus récent
    assert S._parse_fng({}).empty
