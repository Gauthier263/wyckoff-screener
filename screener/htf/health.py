"""health.py — état des sources de données du biais HTF.

`python -m screener.htf.health` interroge chaque source et dit laquelle répond, avec un
échantillon de la donnée. À lancer quand un rapport de biais signale une brique manquante.
"""
from __future__ import annotations

import time

import pandas as pd

from .. import data as D
from ..clock import fmt
from . import sources as S


def _row(name: str, fn) -> dict:
    t0 = time.time()
    try:
        ok, detail = fn()
    except Exception as e:  # une source en panne ne casse jamais le diagnostic
        ok, detail = False, f"{type(e).__name__}: {e}"
    return {"source": name, "ok": "oui" if ok else "non",
            "s": round(time.time() - t0, 1), "detail": detail}


def _ohlcv():
    ex = D.get_exchange("binance")
    df = D.fetch_ohlcv(ex, "BTC/USDT", "1d", limit=400)
    return len(df) > 100, f"{len(df)} bougies 1D, dernière {fmt(df.index[-1])}, close {df['close'].iloc[-1]:,.0f}"


def _oi():
    df = D.fetch_open_interest("BTC/USDT", "1h", limit=200, source="binance")
    if df is None or len(df) == 0:
        return False, "aucune série"
    s = df["oi"] if isinstance(df, pd.DataFrame) else df
    return True, f"{len(s)} barres 1h, dernière {fmt(s.index[-1])}, {s.iloc[-1]:,.0f} BTC"


def _perp_delta():
    s = D.fetch_perp_taker_delta("BTC/USDT", "1h", limit=200)
    if s is None or s.empty:
        return False, "aucune série"
    return True, f"{len(s)} barres 1h, dernière {fmt(s.index[-1])}, delta {s.iloc[-1]:+,.0f} BTC"


def _liq_realized():
    df = S.fetch_realized_liquidations("BTC", 240, 50)
    if df.empty:
        return False, "aucun cluster"
    top = df.loc[df["notional"].astype(float).idxmax()]
    return True, (f"{len(df)} clusters 4h, plus gros {top['price']:,.0f} "
                  f"({float(top['notional'])/1e6:.1f} M$, {top['dominant_side']})")


def _hyperliquid():
    df = S.fetch_hyperliquid_positions("BTC", top_n=200)
    if df.empty:
        return False, "aucune position"
    with_liq = df["liq_px"].notna().sum()
    return True, (f"{len(df)} positions BTC ({int((df['side'] == 'long').sum())} longs / "
                  f"{int((df['side'] == 'short').sum())} shorts), {with_liq} avec prix de "
                  f"liquidation, notionnel {df['notional'].sum()/1e6:.0f} M$")


def _deribit():
    opts = S.fetch_deribit_options("BTC")
    if opts.empty:
        return False, "aucune option"
    mp = S.max_pain(opts)
    return True, f"{len(opts)} options, {opts['expiry'].nunique()} expirations, max pain global {mp:,.0f}"


def _macro():
    df = S.fetch_macro_calendar()
    if df.empty:
        return False, "aucun événement à fort impact cette semaine"
    nxt = df[df["time"] > pd.Timestamp.now(tz="UTC")]
    if nxt.empty:
        return True, f"{len(df)} événements, tous passés"
    r = nxt.iloc[0]
    return True, f"{len(df)} événements US, prochain {r['title']} le {fmt(r['time'])}"


def _yahoo():
    out = []
    for sym in ("^GSPC", "NVDA", "BTC=F"):
        df = S.fetch_yahoo(sym, "1d", "1mo")
        out.append(f"{sym} {len(df)} barres" + (f" close {df['close'].iloc[-1]:,.1f}" if len(df) else ""))
    return all("0 barres" not in o for o in out), " | ".join(out)


def _fng():
    s = S.fetch_fear_greed(30)
    if s.empty:
        return False, "aucune valeur"
    return True, f"{len(s)} jours, aujourd'hui {s.iloc[-1]:.0f}"


CHECKS = [("OHLCV BTC (ccxt)", _ohlcv), ("OI coin (Coinalyze)", _oi),
          ("Delta perp (Coinalyze)", _perp_delta),
          ("Liquidations réalisées (SmartMoney)", _liq_realized),
          ("Positions réelles (Hyperliquid)", _hyperliquid),
          ("Options (Deribit)", _deribit), ("Calendrier macro", _macro),
          ("Actions / CME (Yahoo)", _yahoo), ("Fear & Greed", _fng)]


def report() -> pd.DataFrame:
    return pd.DataFrame([_row(n, f) for n, f in CHECKS])


def main():
    df = report()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
