"""
universe.py — Univers du screener (données seules, aucune logique d'analyse).

Deux sources, toutes deux via ccxt (marchés 24/7, volume crypto-natif) :
  - **Binance** (spot, mirror) : les 46 vraies cryptos.
  - **Bitget** (perp futures USDT) : actions tokenisées, métaux et matières premières
    — équivalents « futures » des sous-jacents, en paires USDT continues.

Tous les actifs sont analysés en **H1 et H4** (séparément), comme du crypto : ces
perps tradent en continu, donc pas de séance ni de recalage de volume.
"""
from __future__ import annotations

from dataclasses import dataclass

# Tous les actifs sont des paires 24/7 → mêmes timeframes pour toutes les classes.
TIMEFRAMES: tuple[str, ...] = ("1h", "4h")


@dataclass(frozen=True)
class Asset:
    name: str            # libellé affiché (base de la paire)
    cls: str             # crypto | equity | metal | commodity
    symbol: str          # symbole ccxt
    source: str          # binance | bitget

    def timeframes(self) -> tuple[str, ...]:
        return TIMEFRAMES


# --------------------------------------------------------------------------- #
# Crypto — 46 paires spot Binance (BASE/USDT)
# --------------------------------------------------------------------------- #
_CRYPTO = [
    "NEAR", "SUI", "DOGE", "ADA", "BNB", "ENA", "XLM", "PEPE", "ONDO", "LINK",
    "TAO", "XPL", "FIL", "AVAX", "BCH", "TON", "AAVE", "LTC", "ASTER", "TRX",
    "DOT", "TRUMP", "INJ", "RENDER", "PUMP", "TIA", "H", "PENGU", "ORDI", "APT",
    "SHIB", "SAHARA", "HBAR", "ICP", "XMR", "EPIC", "VIRTUAL", "BONK", "UNI",
    "FET", "SEI", "OP", "CHZ", "ALLO", "WIF", "FARTCOIN",
]

# --------------------------------------------------------------------------- #
# Actions tokenisées — 35 perps Bitget (BASE/USDT:USDT)
# --------------------------------------------------------------------------- #
_EQUITY = [
    "RKLB", "SNDK", "CBRS", "MU", "LITE", "MRVL", "AAOI", "INTC", "NBIS", "ARM",
    "SKHYNIX", "ASTS", "RDW", "QNTSTOCK", "NVDA", "COHR", "TSLA", "USAR", "CRWV",
    "CRCL", "QCOM", "BE", "DELL", "QBTS", "INFQ", "MSTR", "AXTI", "ORCL", "SMCI",
    "GOOGL", "KOPN", "LWLG", "POET", "HOOD", "ONDS",
]

# --------------------------------------------------------------------------- #
# Métaux — 7 perps Bitget
# --------------------------------------------------------------------------- #
_METAL = ["XAU", "XAG", "XAUT", "PAXG", "XPT", "COPPER", "XPD"]

# --------------------------------------------------------------------------- #
# Matières premières — 3 perps Bitget
# --------------------------------------------------------------------------- #
_COMMODITY = ["CL", "BZ", "NATGAS"]


def _crypto_assets() -> list[Asset]:
    return [Asset(b, "crypto", f"{b}/USDT", "binance") for b in _CRYPTO]


def _bitget_assets(bases: list[str], cls: str) -> list[Asset]:
    return [Asset(b, cls, f"{b}/USDT:USDT", "bitget") for b in bases]


def build_assets(classes: tuple[str, ...] | None = None) -> list[Asset]:
    """Construit la liste d'`Asset` pour les classes demandées (toutes par défaut)."""
    classes = classes or ("crypto", "equity", "metal", "commodity")
    out: list[Asset] = []
    if "crypto" in classes:
        out += _crypto_assets()
    if "equity" in classes:
        out += _bitget_assets(_EQUITY, "equity")
    if "metal" in classes:
        out += _bitget_assets(_METAL, "metal")
    if "commodity" in classes:
        out += _bitget_assets(_COMMODITY, "commodity")
    return out
