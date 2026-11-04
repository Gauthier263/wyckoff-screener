"""
Tests synthétiques du graphe interactif (interactive.py) — hors-ligne.

Séquence d'accumulation fabriquée (SC → AR → ST → SOS) + notes d'analyse : on vérifie
les bornes auto (BB/BH), la fusion des notes (niveaux, zones, événements), les pastilles
cliquables du texte, le décalage horaire CEST et l'écriture d'une page autonome.
"""
import json

import numpy as np
import pandas as pd

from screener.features import add_features
from screener.interactive import build_interactive_html, build_model, render_text
from screener.window import detect_window_structure


def _drift(n, base, vol=1000.0, seed=0):
    """Barres calmes (même générateur que test_window)."""
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        rows.append([o, max(o, c) + abs(rng.normal(0, 0.3)), min(o, c) - abs(rng.normal(0, 0.3)),
                     c, vol * rng.uniform(0.8, 1.1)])
    return rows


def _df():
    rows = _drift(80, 100.0, seed=1)                       # base pour vol_ma/ATR
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]           # SC
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]            # AR
    rows += _drift(4, 102.0, vol=600.0, seed=2)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]              # ST
    rows += _drift(3, 97.5, vol=600.0, seed=3)
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]           # SOS
    rows += _drift(2, 104.0, vol=700.0, seed=4)
    idx = pd.date_range("2026-11-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


NOTES = {
    "title": "Démo",
    "levels": [{"id": "N1", "price": 97.8, "label": "creek", "reason": "low du SOS", "kind": "demand"}],
    "zones": [{"id": "M1", "from": "04/11 11:00", "to": "04/11 13:00", "label": "test", "kind": "range"}],
    "events": [{"id": "X1", "name": "Test", "time": "04/11 12:00", "kind": "pivot", "where": "low"}],
    "text": "### Cadre\nPlancher {BB}, plafond {BH}, {SC} puis {SOS} ; zone {M1}, niveau {N1}, inconnu {ZZ}.",
}


def test_model_auto_levels_and_events():
    df = _df()
    struct = detect_window_structure(df, lookback=20)
    assert struct.bias == "accumulation"
    m = build_model("TEST/USDT", "1h", df, struct)
    ids = {lv["id"] for lv in m["levels"]}
    assert {"BB", "BH"} <= ids
    bb = next(lv for lv in m["levels"] if lv["id"] == "BB")
    assert bb["price"] == 95.0                              # plancher = low du SC
    sc = next(e for e in m["events"] if e["id"] == "SC")
    assert sc["where"] == "low" and sc["price"] == 95.0
    assert len(m["candles"]) == len(df) and m["first"] <= len(df) - 80   # ≥ 80 bougies visibles
    assert 'data-ref="SC"' in m["text_html"]                # texte auto avec pastilles


def test_notes_merge_zones_and_cest_shift():
    df = _df()
    m = build_model("TEST/USDT", "1h", df, detect_window_structure(df, lookback=20), notes=NOTES)
    # heure CEST des notes → barre UTC −2h ; l'axe reçoit l'heure CEST « étiquetée UTC »
    x1 = next(e for e in m["events"] if e["id"] == "X1")
    assert x1["label"] == "04/11 12:00"
    assert x1["time"] == int(pd.Timestamp("2026-11-04 12:00", tz="UTC").timestamp())
    z = m["zones"][0]
    assert z["i1"] - z["i0"] == 2 and z["lo"] <= z["hi"]
    n1 = next(lv for lv in m["levels"] if lv["id"] == "N1")
    assert n1["color"] == "#22a861"                          # demand = vert (palette CLAUDE.md)
    h = m["text_html"]
    for rid in ("BB", "BH", "SC", "SOS", "M1", "N1"):
        assert f'data-ref="{rid}"' in h
    assert "{ZZ}" in h                                       # référence inconnue laissée telle quelle
    assert "<h3>Cadre</h3>" in h


def test_render_text_escapes_and_shapes():
    refs = {"N1": dict(type="level", color="#000", chip="N1 1"),
            "SC": dict(type="event", color="#000", chip="SC")}
    h = render_text("<b>x</b> **gras** {N1} {SC}\n- item {SC}", refs)
    assert "&lt;b&gt;" in h and "<strong>gras</strong>" in h
    assert 'class="ref sq"' in h and 'class="ref dot"' in h and "<li>" in h


def test_html_is_self_contained(tmp_path):
    df = _df()
    out = tmp_path / "chart.html"
    build_interactive_html("TEST/USDT", "1h", df, str(out),
                           struct=detect_window_structure(df, lookback=20), notes=NOTES)
    page = out.read_text(encoding="utf-8")
    assert "Lightweight Charts" in page                      # librairie inlinée (hors-ligne)
    assert "<script src=" not in page
    data = page.split("const D = ", 1)[1].split(";\nconst LW", 1)[0]
    assert json.loads(data)["title"] == "Démo"


def test_thumbnail_under_first_mention_only():
    refs = {"M1": dict(type="zone", color="#000", chip="M1 rebond")}
    h = render_text("### Titre {M1}\n- rebond {M1}\n- encore {M1}\n\nParagraphe {M1}", refs)
    assert h.count('class="thumb"') == 1                    # une seule vignette par zone
    assert '<li>rebond <button' in h and 'data-zone="M1"></div></li>' in h
