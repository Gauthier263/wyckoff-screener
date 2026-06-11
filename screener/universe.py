"""
universe.py — Univers multi-classes du screener (crypto + actions + matières premières).

Ce module ne contient *que* des données : la liste des actifs suivis, leur ticker
selon la source (ccxt pour le crypto, Yahoo Finance pour actions/MP), et le couple
de timeframes Wyckoff adapté à chaque classe. Aucune logique d'analyse ici.

Choix de timeframes (cf. discussion) :
  - crypto      : 4h (contexte) × 1h (déclencheur) — marché 24/7, l'intraday est fiable.
  - action      : 1D (contexte) × 4h (déclencheur) — sessions de ~6h30 + gaps : le
                  contexte journalier évite les faux climax d'ouverture.
  - matière 1ère: 1D × 4h — futures quasi-24h, mais volume intraday moins propre.

Les tickers Yahoo crypto utilisent la convention `-USD` (parfois suffixée d'un
identifiant numérique quand le symbole entre en collision avec une action, ex.
`PEPE24478-USD`). Les tickers ccxt utilisent `BASE/USDT`.
"""
from __future__ import annotations

from dataclasses import dataclass

# Timeframes analysés *séparément* par classe (pas de confluence : on varie les TF pour
# ne pas passer à côté d'une structure visible sur l'une et pas l'autre).
#   crypto       : H1 et H4 (marché 24/7, l'intraday est fiable via ccxt).
#   action / MP  : H4 et D1 (Wyckoff actions = daily ; le H4 capte les structures plus fines).
TF_SET_BY_CLASS: dict[str, tuple[str, ...]] = {
    "crypto": ("1h", "4h"),
    "equity": ("4h", "1d"),
    "commodity": ("4h", "1d"),
}

# Suffixes Yahoo des places dont l'intraday est inexploitable (volume lacunaire :
# Tokyo Σ1h/1d ≈ 0.5, Corée ≈ 0.7 avec barres nulles) → analyse D1 uniquement.
_NO_INTRADAY_SUFFIXES = (".KS", ".T")


@dataclass(frozen=True)
class Asset:
    name: str            # libellé affiché (base crypto ou nom de société)
    cls: str             # crypto | equity | commodity
    yahoo: str           # ticker Yahoo Finance
    ccxt: str | None = None  # symbole ccxt (crypto uniquement), ex. BTC/USDT

    def timeframes(self) -> tuple[str, ...]:
        """TF analysés pour cet actif : le jeu de sa classe, moins l'intraday quand
        la place ne fournit pas de volume horaire fiable (KR/JP → D1 seul)."""
        tfs = TF_SET_BY_CLASS[self.cls]
        if self.cls == "equity" and self.yahoo.endswith(_NO_INTRADAY_SUFFIXES):
            return tuple(tf for tf in tfs if tf in ("1d", "1wk"))
        return tfs


# --------------------------------------------------------------------------- #
# Crypto — 46 paires exploitables (vérifiées sur Yahoo). Format : (base, yahoo, ccxt)
# --------------------------------------------------------------------------- #
_CRYPTO: list[tuple[str, str, str]] = [
    ("NEAR", "NEAR-USD", "NEAR/USDT"),
    ("SUI", "SUI20947-USD", "SUI/USDT"),
    ("DOGE", "DOGE-USD", "DOGE/USDT"),
    ("ADA", "ADA-USD", "ADA/USDT"),
    ("BNB", "BNB-USD", "BNB/USDT"),
    ("ENA", "ENA-USD", "ENA/USDT"),
    ("XLM", "XLM-USD", "XLM/USDT"),
    ("PEPE", "PEPE24478-USD", "PEPE/USDT"),
    ("ONDO", "ONDO-USD", "ONDO/USDT"),
    ("LINK", "LINK-USD", "LINK/USDT"),
    ("TAO", "TAO22974-USD", "TAO/USDT"),
    ("XPL", "XPL-USD", "XPL/USDT"),
    ("FIL", "FIL-USD", "FIL/USDT"),
    ("AVAX", "AVAX-USD", "AVAX/USDT"),
    ("BCH", "BCH-USD", "BCH/USDT"),
    ("TON", "TON-USD", "TON/USDT"),
    ("AAVE", "AAVE-USD", "AAVE/USDT"),
    ("LTC", "LTC-USD", "LTC/USDT"),
    ("ASTER", "ASTER36341-USD", "ASTER/USDT"),
    ("TRX", "TRX-USD", "TRX/USDT"),
    ("DOT", "DOT-USD", "DOT/USDT"),
    ("TRUMP", "TRUMP35336-USD", "TRUMP/USDT"),
    ("INJ", "INJ-USD", "INJ/USDT"),
    ("RENDER", "RENDER-USD", "RENDER/USDT"),
    ("PUMP", "PUMP36507-USD", "PUMP/USDT"),
    ("TIA", "TIA-USD", "TIA/USDT"),
    ("H", "H-USD", "H/USDT"),
    ("PENGU", "PENGU34466-USD", "PENGU/USDT"),
    ("ORDI", "ORDI-USD", "ORDI/USDT"),
    ("APT", "APT21794-USD", "APT/USDT"),
    ("SHIB", "SHIB-USD", "SHIB/USDT"),
    ("SAHARA", "SAHARA-USD", "SAHARA/USDT"),
    ("HBAR", "HBAR-USD", "HBAR/USDT"),
    ("ICP", "ICP-USD", "ICP/USDT"),
    ("XMR", "XMR-USD", "XMR/USDT"),
    ("EPIC", "EPIC-USD", "EPIC/USDT"),
    ("VIRTUAL", "VIRTUAL-USD", "VIRTUAL/USDT"),
    ("BONK", "BONK-USD", "BONK/USDT"),
    ("UNI", "UNI7083-USD", "UNI/USDT"),
    ("FET", "FET-USD", "FET/USDT"),
    ("SEI", "SEI-USD", "SEI/USDT"),
    ("OP", "OP-USD", "OP/USDT"),
    ("CHZ", "CHZ-USD", "CHZ/USDT"),
    ("ALLO", "ALLO-USD", "ALLO/USDT"),
    ("WIF", "WIF-USD", "WIF/USDT"),
    ("FARTCOIN", "FARTCOIN-USD", "FARTCOIN/USDT"),
]

# --------------------------------------------------------------------------- #
# Actions — 90 valeurs (tickers Yahoo vérifiés). Suffixes : .KS Corée, .T Tokyo.
# --------------------------------------------------------------------------- #
_EQUITY: dict[str, str] = {
    "CoreWeave": "CRWV", "Qualcomm": "QCOM", "Alphabet": "GOOGL", "Broadcom": "AVGO",
    "Redwire": "RDW", "USA Rare Earth": "USAR", "Bloom Energy": "BE", "Coinbase": "COIN",
    "POET Technologies": "POET", "Coherent": "COHR", "Robinhood": "HOOD", "Nokia": "NOK",
    "Microsoft": "MSFT", "Meta": "META", "Taiwan Semiconductor": "TSM", "Samsung": "005930.KS",
    "Credo Technology": "CRDO", "Firefly Aerospace": "FLY", "Ondas Holdings": "ONDS",
    "Apple": "AAPL", "Palantir": "PLTR", "AXT Inc": "AXTI", "Amazon": "AMZN",
    "AST SpaceMobile": "ASTS", "Rigetti Computing": "RGTI", "Oracle": "ORCL", "Hyundai": "005380.KS",
    "Western Digital": "WDC", "IonQ": "IONQ", "Dell": "DELL", "Applied Digital": "APLD",
    "NuScale Power": "SMR", "ASML": "ASML", "Alibaba": "BABA", "Cisco": "CSCO", "Oklo": "OKLO",
    "Kopin": "KOPN", "D-Wave Quantum": "QBTS", "IBM": "IBM", "Ouster": "OUST",
    "Super Micro Computer": "SMCI", "BlackBerry": "BB", "Reddit": "RDDT", "ServiceNow": "NOW",
    "Snowflake": "SNOW", "Vertiv": "VRT", "Lightwave Logic": "LWLG", "Red Cat Holdings": "RCAT",
    "Eli Lilly": "LLY", "AppLovin": "APP", "MP Materials": "MP", "Futu Holdings": "FUTU",
    "Applied Materials": "AMAT", "KLA Corporation": "KLAC", "Kratos Defense": "KTOS",
    "UnitedHealth": "UNH", "Berkshire Hathaway": "BRK-B", "Walmart": "WMT", "AeroVironment": "AVAV",
    "Seagate": "STX", "Palo Alto Networks": "PANW", "SiTime": "SITM", "Joby Aviation": "JOBY",
    "Axon Enterprise": "AXON", "NIO": "NIO", "Arqit Quantum": "ARQQ", "ConocoPhillips": "COP",
    "Quantum Computing": "QUBT", "GameStop": "GME", "GE Aerospace": "GE", "Occidental Petroleum": "OXY",
    "EHang": "EH", "Costco": "COST", "McDonald's": "MCD", "Netflix": "NFLX", "JD.com": "JD",
    "Exxon Mobil": "XOM", "RTX Corporation": "RTX", "Lockheed Martin": "LMT", "Eaton": "ETN",
    "Doosan Robotics": "454910.KS", "Northrop Grumman": "NOC", "NetApp": "NTAP",
    "Archer Aviation": "ACHR", "Doosan Enerbility": "034020.KS", "Sumitomo Electric": "5802.T",
    "Advantest": "6857.T", "Tokyo Electron": "8035.T", "Lasertec": "6920.T", "Kioxia": "285A.T",
}

# --------------------------------------------------------------------------- #
# Matières premières — futures Yahoo (8).
# --------------------------------------------------------------------------- #
_COMMODITY: dict[str, str] = {
    "Gold": "GC=F", "Silver": "SI=F", "WTI Crude": "CL=F", "Brent Crude": "BZ=F",
    "Platinum": "PL=F", "Palladium": "PA=F", "Copper": "HG=F", "Natural Gas": "NG=F",
}

# Demandés mais écartés, avec raison (transparence).
EXCLUDED: dict[str, str] = {
    "OpenAI": "société privée — non cotée",
    "Infleqtion": "fusion SPAC non finalisée — pas de ticker public stable",
    "LAB": "aucune correspondance Yahoo fiable (collision avec Zero1 Labs)",
    "OPN": "absent de Yahoo Finance",
    "BABY": "Yahoo ne référence que BabySwap, pas Babylon",
    "BEAT": "aucune correspondance Yahoo fiable",
    "HOME": "ticker Yahoo sans historique intraday",
    "BILL": "Yahoo ne référence que BilliCat",
    "BSB": "absent de Yahoo Finance",
}


def build_assets(classes: tuple[str, ...] | None = None) -> list[Asset]:
    """Construit la liste d'`Asset` pour les classes demandées (toutes par défaut)."""
    classes = classes or ("crypto", "equity", "commodity")
    out: list[Asset] = []
    if "crypto" in classes:
        out += [Asset(b, "crypto", y, c) for b, y, c in _CRYPTO]
    if "equity" in classes:
        out += [Asset(n, "equity", t) for n, t in _EQUITY.items()]
    if "commodity" in classes:
        out += [Asset(n, "commodity", t) for n, t in _COMMODITY.items()]
    return out
