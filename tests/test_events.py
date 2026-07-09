"""
Tests sur données synthétiques : on fabrique des plages avec un spring ou un UTAD
clairs, et on vérifie que les détecteurs les retrouvent. Aucune connexion réseau.

    pytest -q
"""
import numpy as np
import pandas as pd

from screener.events import detect_events
from screener.features import add_features, detect_trading_range, swing_points


def _range_base(n=100, low=100.0, high=110.0, seed=0):
    """Construit n barres oscillant proprement dans [low, high]."""
    rng = np.random.default_rng(seed)
    mid = (low + high) / 2
    amp = (high - low) / 2 * 0.8
    closes = mid + amp * np.sin(np.linspace(0, 6 * np.pi, n)) + rng.normal(0, 0.2, n)
    rows = []
    for c in closes:
        o = c + rng.normal(0, 0.1)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        h = min(h, high)          # contenu dans la plage
        l = max(l, low)
        rows.append([o, h, l, c, rng.uniform(900, 1100)])
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)


def _append(df, o, h, l, c, v):
    idx = df.index[-1] + (df.index[-1] - df.index[-2])
    return pd.concat([df, pd.DataFrame([[o, h, l, c, v]],
                     columns=["open", "high", "low", "close", "volume"], index=[idx])])


def _analyze(df):
    df = add_features(df, vol_ma=20, atr_period=14)
    df = swing_points(df)
    tr = detect_trading_range(df, lookback=80, buffer=5)
    return tr, detect_events(df, tr, buffer=5)


def test_range_is_valid():
    tr, _ = _analyze(_range_base())
    assert tr.is_valid
    assert tr.low < tr.high


def test_spring_detected():
    df = _range_base()
    # barre de spring : plonge sous 100 puis clôture nettement à l'intérieur
    df = _append(df, 100.5, 101.0, 97.5, 100.6, 1000)
    tr, events = _analyze(df)
    names = [e.name for e in events]
    assert "SPRING" in names, names


def test_utad_detected():
    df = _range_base()
    # upthrust : pique au-dessus de 110 puis clôture sous la résistance
    df = _append(df, 109.5, 112.5, 109.0, 109.4, 1000)
    tr, events = _analyze(df)
    names = [e.name for e in events]
    assert "UTAD" in names, names


def test_sos_detected():
    df = _range_base()
    # cassure haussière franche avec volume et clôture haute
    df = _append(df, 110.0, 113.0, 109.8, 112.8, 2500)
    tr, events = _analyze(df)
    names = [e.name for e in events]
    assert "SOS" in names, names


def test_neutral_range_has_few_events():
    tr, events = _analyze(_range_base(seed=3))
    # une plage calme ne doit pas crouler sous les signaux de cassure
    breakout = [e for e in events if e.name in ("SOS", "SOW", "SPRING", "UTAD")]
    assert len(breakout) == 0, [e.name for e in events]


# ── Climax, tests et back-ups (SC / BC / ST / LPS / LPSY) ──────────────────────
# Ces détecteurs n'étaient exercés qu'indirectement via window.py ; on couvre ici
# directement les branches de detect_events (barre large volumique au climax, test
# à volume sec près d'une borne, back-up après cassure).

def test_sc_selling_climax():
    df = _range_base()
    # barre large + volume climactique au support, clôture haute (reprise de la demande)
    df = _append(df, 100.2, 103.0, 100.0, 102.5, 3000)
    _, events = _analyze(df)
    assert "SC" in [e.name for e in events], [e.name for e in events]


def test_no_sc_when_volume_normal():
    df = _range_base()
    # même géométrie mais volume normal → pas de climax
    df = _append(df, 100.2, 103.0, 100.0, 102.5, 1000)
    _, events = _analyze(df)
    assert "SC" not in [e.name for e in events]


def test_bc_buying_climax():
    df = _range_base()
    # barre large + volume climactique à la résistance, clôture basse (l'offre absorbe)
    df = _append(df, 109.8, 110.0, 107.0, 107.5, 3000)
    _, events = _analyze(df)
    assert "BC" in [e.name for e in events], [e.name for e in events]


def test_st_secondary_test_near_support():
    df = _range_base()
    # barre étroite à volume sec collée au support → test secondaire (accumulation)
    df = _append(df, 100.5, 100.8, 100.2, 100.6, 650)
    _, events = _analyze(df)
    sts = [e for e in events if e.name == "ST" and e.bias == "accumulation"]
    assert sts, [e.name for e in events]


def test_no_st_when_volume_high():
    df = _range_base()
    # même barre near-support mais volume élevé → ce n'est pas un test « sec »
    df = _append(df, 100.5, 100.8, 100.2, 100.6, 2000)
    _, events = _analyze(df)
    assert "ST" not in [e.name for e in events]


def test_lps_backup_after_sos():
    df = _range_base()
    # cassure franche (SOS) puis repli à volume sec tenant au-dessus de la résistance
    df = _append(df, 110.0, 113.0, 109.8, 112.8, 2500)   # SOS
    df = _append(df, 112.0, 111.6, 110.3, 111.2, 650)    # LPS (back-up)
    _, events = _analyze(df)
    names = [e.name for e in events]
    assert "SOS" in names and "LPS" in names, names


def test_lpsy_backup_after_sow():
    df = _range_base()
    # cassure baissière (SOW) puis rebond faible à volume sec sous le support
    df = _append(df, 100.0, 100.2, 97.0, 97.2, 2500)     # SOW
    df = _append(df, 98.0, 99.5, 98.5, 98.8, 650)        # LPSY (rebond faible)
    _, events = _analyze(df)
    names = [e.name for e in events]
    assert "SOW" in names and "LPSY" in names, names
