"""Test synthétique : le mémo reflète les seuils + l'OI, et rend bien un HTML."""
import os

from screener.events import Thresholds
from screener.theory_table import build_theory_html, theory_rows


def test_theory_rows_reflect_thresholds_and_oi():
    th = Thresholds(climax_vol=2.5, sos_vol=1.4, test_vol=0.8, wide_spread_atr=1.2)
    for bias in ("accumulation", "distribution"):
        rows = theory_rows(bias, th)
        evs = [r["ev"] for r in rows]
        # séquence Phase A→D complète
        for e in (["SC", "SPRING", "SOS", "LPS"] if bias == "accumulation"
                  else ["BC", "UTAD", "SOW", "LPSY"]):
            assert e in evs
        blob = " ".join(r["volx"] + r["oi"] + r["valide"] for r in rows)
        assert "×2.5" in blob and "×1.4" in blob and "×0.8" in blob
        # l'OI figure bien, et l'AR exige un OI en repli
        ar = next(r for r in rows if r["ev"] == "AR")
        assert "OI" in ar["valide"] and "repli" in ar["valide"].lower()


def test_theory_rows_include_cvd():
    """V2 : chaque ligne porte une attente CVD, et SOS/SOW exigent un CVD franc."""
    th = Thresholds()
    for bias in ("accumulation", "distribution"):
        rows = theory_rows(bias, th)
        for r in rows:
            assert r.get("cvd"), f"CVD manquant pour {r['ev']} ({bias})"
        signe = "SOS" if bias == "accumulation" else "SOW"
        sgn = next(r for r in rows if r["ev"] == signe)
        assert "FRANC" in sgn["cvd"].upper()
        # le climax doit décrire l'absorption
        climax = next(r for r in rows if r["ev"] in ("SC", "BC"))
        assert "absorption" in climax["cvd"].lower()


def test_theory_rows_absorption_column():
    """Chaque ligne porte l'absorption attendue ; SOS/SOW = honnête (≈0), Spring = abs>0."""
    th = Thresholds()
    for bias in ("accumulation", "distribution"):
        rows = theory_rows(bias, th)
        for r in rows:
            assert r.get("absorp"), f"absorp manquant pour {r['ev']} ({bias})"
        signe = "SOS" if bias == "accumulation" else "SOW"
        sgn = next(r for r in rows if r["ev"] == signe)
        # SOS/SOW = mouvement honnête = absorption NÉGATIVE (pas ≈0), distincte du spring (>0)
        assert "< 0" in sgn["absorp"] and "HONNÊTE" in sgn["absorp"]
        spring = next(r for r in rows if r["ev"] in ("SPRING", "UTAD"))
        assert "> 0" in spring["absorp"]


def test_event_cards_no_trap_but_spring_detail():
    """Le « piège » des fiches event est retiré ; Spring/UTAD ont le détail (micro LTF + types)."""
    out = build_theory_html(Thresholds(), out_path=None) if False else None
    import tempfile, os
    p = build_theory_html(Thresholds(), out_path=os.path.join(tempfile.mkdtemp(), "m.html"))
    doc = open(p, encoding="utf-8").read()
    assert "Piège / invalidation" not in doc          # retiré des fiches event
    assert "Piège / caveat" in doc                     # conservé sur les fiches INDICE
    assert "Absorption (indice)" in doc                # colonne table
    assert "Micro-comportement sur TF inférieure" in doc
    assert 'Spring « #3 »' in doc and "terminal shakeout" in doc
    assert "Spring vs SOS vs vraie cassure" in doc
    assert "Les types d'upthrust" in doc
    assert doc.count(">Absorption<") >= 12             # ligne absorption dans les fiches event


def test_build_theory_html(tmp_path):
    th = Thresholds(climax_vol=2.5, sos_vol=1.4, test_vol=0.8, wide_spread_atr=1.2)
    out = build_theory_html(th, out_path=str(tmp_path / "memo.html"))
    assert os.path.exists(out)
    doc = open(out, encoding="utf-8").read()
    # les deux schémas, tous les événements (Phase A→D), colonnes OI/CVD et les seuils
    for token in ("ACCUMULATION", "DISTRIBUTION", "SC", "BC", "AR", "ST", "SOS", "SOW",
                  "SPRING", "UTAD", "LPS", "LPSY", "OI attendu", "CVD attendu",
                  "Validé si", "Invalidé si"):
        assert token in doc
    assert "×2.5" in doc and "×1.4" in doc and "×0.8" in doc and "1.2 ATR" in doc


def test_build_theory_html_v2_sections(tmp_path):
    """V2 : les 4 blocs (fondations, tables, narratifs, indices) sont présents."""
    out = build_theory_html(Thresholds(), out_path=str(tmp_path / "memo.html"))
    doc = open(out, encoding="utf-8").read()
    # blocs
    for anchor in ('id="fondations"', 'id="tables"', 'id="events"', 'id="indices"'):
        assert anchor in doc
    # fondations : 3 lois, opérateur composite, phases, hiérarchie
    for token in ("opérateur composite", "effort vs résultat", "cause et effet",
                  "Phase A", "Phase E", "volume → OI → tierces"):
        assert token in doc
    # narratif par événement : récit + indices, pour les events clés
    for token in ("Ce qui se passe", "Qui est en jeu", "Buying Climax",
                  "Upthrust After Distribution", "Selling Climax"):
        assert token in doc
    # théorie par indice : les indicateurs (dont absorption/no-demand)
    for token in ("Cumulative Volume Delta", "Close Location Value", "Open Interest",
                  "Funding rate", "Ratio Long/Short", "Liquidations", "Average True Range",
                  "effort vs résultat", "No-demand"):
        assert token in doc
    # une fiche par événement (≥ 12) et par indice (9, dont absorption)
    assert doc.count("card event") >= 12
    assert doc.count("card indic") == 9
