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


def test_render_text_escapes_and_neutral_refs():
    refs = {"N1": dict(type="level", color="#000", chip="N1 1"),
            "SC": dict(type="event", color="#000", chip="SC")}
    h = render_text("<b>x</b> **gras** {N1} {SC}\n- item {SC}", refs)
    assert "&lt;b&gt;" in h and "<strong>gras</strong>" in h
    assert h.count('class="ref"') == 3 and "<li>" in h
    assert "<i></i>" not in h and "--c:" not in h          # aucune pastille de couleur


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
    h = render_text("### Titre {M1}\n- rebond {M1}\n- encore {M1}\n\nParagraphe {M1}", refs, thumbs_on=True)
    assert h.count('class="thumb"') == 1                    # une seule vignette par zone
    assert '<li>rebond <button' in h and 'data-zone="M1"></div></li>' in h


def test_canonical_format_slots_verdict_theory_view():
    """Format canonique : tables placées dans le texte, verdict/sens, ΔOI calculé, théorie
    auto depuis les Thresholds, vue initiale bornée par `view`."""
    df = _df()
    oi = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0,
                       "close": np.linspace(100, 110, len(df))}, index=df.index)
    notes = {
        "bias": "accumulation", "page_title": "Démo 1h",
        "view": {"from": "04/11 00:00", "to": "04/11 20:00"},
        "events": [{"id": "S1", "name": "SOS ?", "theory_of": "SOS", "time": "04/11 12:00",
                    "where": "high", "verdict": "tentative", "sense": "OI en baisse"}],
        "text": "### 2. Lecture\n[[events]]\n### 5. Niveaux\n[[levels]]",
    }
    m = build_model("TEST/USDT", "1h", df, notes=notes, oi_ohlc=oi, min_bars=10)
    assert '<div class="slot" data-slot="events"></div>' in m["text_html"]
    assert '<div class="slot" data-slot="levels"></div>' in m["text_html"]
    e = m["events"][0]
    assert e["verdict"] == "tentative" and e["sense"] == "OI en baisse"
    assert e["oi_chg"] is not None and e["oi_chg"] > 0          # calculé depuis oi_ohlc
    assert "×1.3" in e["theory"] or "1.3" in e["theory"]       # seuil SOS issu des Thresholds
    assert m["last_i"] < len(df) - 1 and m["first"] <= m["last_i"]
    assert m["page_title"] == "Démo 1h"


def test_level_line_starts_at_its_origin_bar():
    """Le pointillé d'un niveau part du sommet/creux qui le définit (auto ou `from`)."""
    df = _df()
    hi_ts = df["high"].idxmax()
    notes = {"levels": [
        {"id": "N1", "price": float(df["high"].max()), "label": "sommet"},      # auto
        {"id": "N2", "price": 1.0, "label": "lointain"},                        # aucun match
        {"id": "N3", "price": 100.0, "label": "forcé", "from": "04/11 05:00"}]}
    m = build_model("TEST/USDT", "1h", df, notes=notes, min_bars=10)
    lv = {l["id"]: l for l in m["levels"]}
    assert lv["N1"]["t0"] == int(hi_ts.timestamp()) + 2 * 3600
    assert lv["N2"]["t0"] is None
    assert lv["N3"]["t0"] == int(pd.Timestamp("2026-11-04 03:00", tz="UTC").timestamp()) + 2 * 3600


def test_no_thumbnail_by_default():
    """Par défaut, aucune vignette sous les mouvements : le graphe principal suffit."""
    m = build_model("TEST/USDT", "1h", _df(), notes=NOTES)
    assert 'class="thumb"' not in m["text_html"]


def test_table_text_drops_reference_braces():
    from screener.interactive import _plain
    assert _plain("entre dans la plage {M2} puis **{SOW}**") == "entre dans la plage M2 puis SOW"


def test_macro_sketch_rendered_in_place():
    """`[[macro]]` → petit schéma SVG de la tendance macro (segments hausse/baisse, niveaux)."""
    notes = {"text": "### 1. Contexte macro\n[[macro]]\nTexte.",
             "macro": {"points": [{"date": "10/25", "price": 126000, "label": "ATH"},
                                  {"date": "07/26", "price": 57800, "label": "bas"},
                                  {"date": "09/26", "price": 87400, "label": "LH"},
                                  {"date": "11/26", "price": 73900, "label": "now"}],
                       "lines": [{"price": 74968, "label": "pivot"}], "caption": "Primaire baissière"}}
    m = build_model("TEST/USDT", "1h", _df(), notes=notes, min_bars=10)
    h = m["text_html"]
    assert '<svg class="macro"' in h and 'data-slot="macro"' not in h
    assert h.count('class="mdn"') == 2 and h.count('class="mup"') == 1
    assert "Primaire baissière" in h and "75k pivot" in h


def test_phase_sketch_and_acronyms():
    """`[[phase]]` → schéma de l'épisode Wyckoff (bandes de phases, plage) ; noms complets."""
    from screener.interactive import _full_name
    notes = {"text": "### 1. Contexte\n[[phase]]",
             "phase": {"tf": "Daily", "title": "Distribution",
                       "points": [{"label": "BC", "price": 87000}, {"label": "AR", "price": 82000},
                                  {"label": "ST", "price": 86800}, {"label": "ici", "price": 74000}],
                       "range": {"hi": 87000, "lo": 80000},
                       "phases": [{"from": 0, "to": 2, "label": "A"}, {"from": 2, "to": 3, "label": "E"}]}}
    h = build_model("TEST/USDT", "1h", _df(), notes=notes, min_bars=10)["text_html"]
    assert '<svg class="phase"' in h and h.count('class="pband') == 2 and "Daily · Distribution" in h
    assert _full_name({"theory_of": "SOW"}).startswith("Sign of Weakness")
    assert _full_name({"name": "ST-haut"}).startswith("Secondary Test")
    assert _full_name({"name": "Plancher"}) == ""
