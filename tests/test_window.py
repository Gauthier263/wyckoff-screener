"""
Tests synthétiques du détecteur de structure sur fenêtre (window.py).

On fabrique une séquence d'accumulation propre (SC → AR → ST → SOS) et son miroir
de distribution, puis on vérifie que `detect_window_structure` retrouve le bon
schéma, l'ordre des événements, et remplit théorie + justification. Hors-ligne.
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.window import detect_supply_dryup, detect_window_structure


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _drift(n, base, vol=1000.0, seed=0):
    """Barres calmes proches de `base` (volume normal, spread étroit)."""
    rng = np.random.default_rng(seed)
    rows = []
    c = base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def test_accumulation_sequence():
    rows = _drift(40, 100.0, seed=1)                       # base pour vol_ma/ATR
    # SC : grosse barre vendeuse qui fait un plus-bas et clôture haut, volume x3
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]
    # AR : rebond auto, volume en repli
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]
    rows += _drift(4, 102.0, vol=600.0, seed=2)            # dérive haute, volume sec
    # ST : retour près du plancher (95.x) sur volume sec, barre étroite, creux plus haut
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]
    rows += _drift(3, 97.5, vol=600.0, seed=3)
    # SOS : poussée large et volumique, clôture haute
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]
    rows += _drift(2, 104.0, vol=700.0, seed=4)

    struct = detect_window_structure(_df(rows), lookback=20)
    assert struct.bias == "accumulation"
    assert struct.is_valid
    names = [e.name for e in struct.events]
    assert names[0] == "SC"
    assert "SOS" in names
    assert {"SC", "AR"}.issubset(set(names))
    # chaque événement porte théorie + justification volume/spread
    for e in struct.events:
        assert e.theory and "vol" in e.why


def test_accumulation_spring_and_lps():
    """Séquence complète Phase A→D : SC → AR → ST → SPRING → SOS → LPS.

    Vérifie le resserrement de l'AR (rebond réflexe immédiat, volume en repli) et la
    reconnaissance du Spring (fausse cassure sous le plancher) puis du LPS (back-up sec)."""
    rows = _drift(40, 100.0, seed=11)                      # warmup vol_ma/ATR (~1000)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]           # SC : climax, plancher 95.0
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]            # AR : rebond réflexe, volume en repli (<1×)
    rows += _drift(2, 101.5, vol=600.0, seed=12)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]              # ST : test sec, creux plus haut
    rows += _drift(8, 99.0, vol=650.0, seed=13)            # Phase B (lows > 95)
    rows += [[96.0, 96.2, 94.2, 95.8, 900.0]]              # SPRING : sous 95.0 puis clôture rentrée
    rows += _drift(1, 97.0, vol=600.0, seed=14)
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]           # SOS : JAC large + volumique
    rows += _drift(1, 102.0, vol=700.0, seed=15)
    rows += [[102.0, 102.5, 100.5, 101.8, 500.0]]          # LPS : back-up sec, creux plus haut
    rows += _drift(2, 102.0, vol=700.0, seed=16)

    struct = detect_window_structure(_df(rows), lookback=20)
    names = [e.name for e in struct.events]
    assert struct.bias == "accumulation" and struct.is_valid
    assert names[0] == "SC"
    for ev in ("AR", "ST", "SPRING", "SOS", "LPS"):
        assert ev in names, f"{ev} manquant : {names}"
    # ordre chronologique respecté
    assert names == sorted(names, key=lambda nm: [e.ts for e in struct.events if e.name == nm][0])
    # l'AR validé porte bien un volume en repli (< 1×)
    ar = next(e for e in struct.events if e.name == "AR")
    assert ar.vol_ratio < 1.0


def test_ar_gated_by_open_interest():
    """L'AR n'est validé que si l'OI est EN REPLI (débouclage), en plus du volume."""
    rows = _drift(40, 100.0, seed=1)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]          # SC
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]           # AR (volume en repli)
    rows += _drift(4, 102.0, vol=600.0, seed=2)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]             # ST
    rows += _drift(3, 97.5, vol=600.0, seed=3)
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]          # SOS
    rows += _drift(2, 104.0, vol=700.0, seed=4)
    df = _df(rows)
    n = len(df)
    rising = pd.DataFrame({"oi": np.linspace(1000, 2000, n)}, index=df.index)
    falling = pd.DataFrame({"oi": np.linspace(2000, 1000, n)}, index=df.index)

    up = detect_window_structure(df, lookback=20, oi=rising)
    dn = detect_window_structure(df, lookback=20, oi=falling)
    assert "AR" not in [e.name for e in up.events]        # OI en hausse → AR refusé
    assert "AR" in [e.name for e in dn.events]            # OI en repli → AR validé
    ar = next(e for e in dn.events if e.name == "AR")
    assert ar.oi_chg < 0                                   # ΔOI annoté (négatif)


def test_distribution_sequence():
    rows = _drift(40, 100.0, seed=5)
    # BC : grosse barre acheteuse qui fait un plus-haut et clôture bas, volume x3
    rows += [[100.0, 105.0, 99.6, 100.4, 3200.0]]
    # AR : repli auto, volume en repli
    rows += [[100.4, 100.6, 97.0, 97.4, 800.0]]
    rows += _drift(4, 98.0, vol=600.0, seed=6)
    # ST : retour près du plafond (104.x) sur volume sec, barre étroite, sommet plus bas
    rows += [[103.6, 104.4, 103.2, 103.8, 500.0]]
    rows += _drift(3, 102.5, vol=600.0, seed=7)
    # SOW : cassure baissière large et volumique, clôture basse
    rows += [[102.0, 102.2, 95.5, 95.8, 2600.0]]
    rows += _drift(2, 96.0, vol=700.0, seed=8)

    struct = detect_window_structure(_df(rows), lookback=20)
    assert struct.bias == "distribution"
    assert struct.is_valid
    names = [e.name for e in struct.events]
    assert names[0] == "BC"
    assert "SOW" in names


def test_no_structure_on_flat_drift():
    struct = detect_window_structure(_df(_drift(80, 100.0, seed=9)), lookback=30)
    assert struct.bias == "neutral"
    assert not struct.is_valid


def _markup(n, start, end, vol, seed):
    """Tendance haussière franche (sert de contexte AVANT le coil : hors bande → exclue
    du coil endogène, et fournit l'historique vol_ma/ATR)."""
    rng = np.random.default_rng(seed)
    rows = []
    step = (end - start) / n
    c = start
    for _ in range(n):
        o = c
        c = c + step + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.4))
        l = min(o, c) - abs(rng.normal(0, 0.4))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def _spring_coil(seed_a=21, seed_b=22, seed_c=23, vscale=1.0):
    """Coil d'accumulation générique APRÈS un markup (sans contexte macro imposé) : tests
    successifs à volume décroissant qui tiennent, un spring sous ~98 puis son test à volume
    sec, l'ATR qui se contracte. `vscale` multiplie les volumes (invariance d'échelle)."""
    v = lambda x: x * vscale
    rows = _markup(26, 90.0, 100.0, vol=v(1000.0), seed=seed_a)   # markup préalable → hors coil
    # coil autour de 98..101, oscillations qui se resserrent, volume qui s'assèche
    rows += [[100.0, 101.4, 98.2, 98.6, v(1500.0)]]         # test 1 (vol élevé, large)
    rows += _drift(3, 99.6, vol=v(950.0), seed=seed_b)
    rows += [[99.6, 100.1, 98.3, 98.9, v(850.0)]]           # test 2 (vol moindre)
    rows += _drift(3, 99.3, vol=v(650.0), seed=seed_c)
    rows += [[99.0, 99.4, 98.35, 99.0, v(520.0)]]           # test 3 (vol sec, creux tenu)
    rows += _drift(2, 99.1, vol=v(480.0), seed=seed_a + 1)
    rows += [[98.6, 98.8, 97.1, 98.7, v(760.0)]]            # SPRING : sous 98 puis clôture rentrée
    rows += [[98.7, 98.95, 97.6, 98.9, v(400.0)]]           # test du spring : vol sec, creux plus haut
    rows += _drift(3, 99.3, vol=v(460.0), seed=seed_b + 1)
    return rows


def test_supply_dryup_coil_with_spring():
    """Coil générique d'accumulation avec assèchement de l'offre : le détecteur repère le
    coil de façon endogène, compte les tests réussis, isole le spring + son test, et sort un
    score élevé — sans aucun contexte macro (pas de back-up to the creek)."""
    df = _df(_spring_coil())
    dry = detect_supply_dryup(df, lookback=40)

    assert dry.coil                              # coil détecté (bande + latéralité)
    assert dry.is_valid                          # ≥ 2 tests + score ≥ 0.5
    assert dry.n_tests >= 2
    assert dry.spring is not None                # Phase C repérée
    assert dry.spring_test is not None
    assert dry.support < 99.0 < dry.resistance   # support/résistance encadrent le prix
    assert dry.score >= 0.5
    # signaux volume renseignés + événements portent théorie/justification
    assert set(dry.signals) == {"s1", "s2", "s3", "s4", "s_spring"}
    assert dry.signals["s_spring"] == 1.0        # spring + test présents
    for e in dry.events:
        assert e.theory and "vol" in e.why


def test_supply_dryup_scale_invariant():
    """Invariance d'échelle de volume : multiplier tous les volumes ne change pas le verdict
    (les signaux sont en ratio) — proxy de robustesse 15m/1h/4h."""
    a = detect_supply_dryup(_df(_spring_coil(vscale=1.0)), lookback=40)
    b = detect_supply_dryup(_df(_spring_coil(vscale=50.0)), lookback=40)
    assert a.is_valid and b.is_valid
    assert abs(a.score - b.score) < 1e-9
    assert a.n_tests == b.n_tests


def test_supply_dryup_breakout_not_spring():
    """Une bougie qui pénètre la borne mais CLÔTURE de l'autre côté de la plage (cassure /
    breakout climactique, ex. ONT ×17.3) n'est PAS un spring : il doit reclôturer DANS la plage."""
    rows = [[90 + k * (9 / 40), 90 + k * (9 / 40) + 0.2, 90 + k * (9 / 40) - 0.2,
             90 + k * (9 / 40), 1000.0] for k in range(40)]           # markup warmup
    rows += [
        [99.4, 99.60, 98.00, 98.50, 1200.0],    # test1 support≈98
        [98.6, 99.55, 98.50, 99.20, 900.0],
        [99.2, 99.60, 98.05, 98.55, 700.0],     # test2
        [98.6, 99.50, 98.40, 99.10, 600.0],
        [99.1, 99.55, 98.02, 98.60, 500.0],     # test3
        [98.7, 99.50, 98.45, 99.15, 480.0],
        [98.5, 100.80, 97.00, 100.60, 3000.0],  # CASSURE : dip sous support puis close AU-DESSUS résistance
        [100.6, 101.00, 100.20, 100.80, 800.0],
    ]
    dry = detect_supply_dryup(_df(rows), lookback=40)
    assert dry.spring is None                    # clôture hors plage → cassure, pas spring
    # garde-fou : un vrai spring (clôture DANS la plage, clv 0.94) reste détecté
    assert detect_supply_dryup(_df(_spring_coil()), lookback=40).spring is not None


def _coil_with_dip(dip_bar):
    """Coil déterministe (support ≈ 98) avec UNE barre qui pique sous le support."""
    rows = [[90 + k * (9 / 40), 90 + k * (9 / 40) + 0.2, 90 + k * (9 / 40) - 0.2,
             90 + k * (9 / 40), 1000.0] for k in range(40)]
    rows += [
        [99.5, 100.0, 98.00, 98.40, 1500.0],
        [98.6, 99.60, 98.50, 99.30, 1200.0],
        [99.3, 99.80, 98.05, 98.50, 900.0],
        [98.6, 99.50, 98.40, 99.20, 700.0],
        [99.2, 99.60, 98.02, 98.45, 500.0],
        [98.5, 99.40, 98.30, 99.10, 480.0],
        dip_bar,
        [98.2, 99.00, 98.00, 98.90, 460.0],
        [98.9, 99.50, 98.60, 99.20, 500.0],
    ]
    return rows


def test_supply_dryup_bullish_body_not_spring():
    """Un gros CORPS haussier qui pique sous le support (petite mèche) n'est PAS un spring —
    juste une bougie haussière (cf. META). Seule une MÈCHE de rejet dominante l'est."""
    # corps haussier : mèche basse 0.7 / range 1.6 = 0.44 < 0.5 → pas un rejet (clv 0.94 pourtant)
    body = [98.10, 99.00, 97.40, 98.90, 800.0]
    assert detect_supply_dryup(_df(_coil_with_dip(body)), lookback=40).spring is None
    # pin-bar : mèche basse 1.4 / range 1.6 = 0.88 ≥ 0.5 → vrai rejet
    pin = [98.85, 99.00, 97.40, 98.80, 800.0]
    assert detect_supply_dryup(_df(_coil_with_dip(pin)), lookback=40).spring is not None


def test_supply_dryup_bias_specific():
    """Un coil d'accumulation (offre qui s'assèche, demande dessous) ne doit PAS valider en
    lecture distribution : le signal directionnel (asymétrie proxy-CVD) coupe le mauvais biais."""
    df = _df(_spring_coil())
    assert detect_supply_dryup(df, lookback=40, bias="accumulation").is_valid
    assert not detect_supply_dryup(df, lookback=40, bias="distribution").is_valid


def test_supply_dryup_no_false_positive_on_noise():
    """Aucun faux positif sur du bruit pur (marche aléatoire) : ni coil actionnable, ni score."""
    valid = [s for s in range(12)
             if detect_supply_dryup(_df(_drift(60, 100.0, seed=s)), lookback=40).is_valid]
    assert valid == [], f"faux positifs sur bruit : seeds {valid}"


def test_supply_dryup_none_on_trend():
    """Pas de coil sur une tendance franche (bande trop haute en ATR) → non valide."""
    rows = _drift(20, 100.0, seed=9)
    c = 100.0
    for k in range(30):                          # markup soutenu, aucune latéralité
        c += 2.0
        rows.append([c - 1.5, c + 0.5, c - 2.0, c, 1000.0])
    dry = detect_supply_dryup(_df(rows), lookback=40)
    assert not dry.coil
    assert not dry.is_valid
