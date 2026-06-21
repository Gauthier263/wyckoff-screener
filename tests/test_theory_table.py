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


def test_build_theory_html(tmp_path):
    th = Thresholds(climax_vol=2.5, sos_vol=1.4, test_vol=0.8, wide_spread_atr=1.2)
    out = build_theory_html(th, out_path=str(tmp_path / "memo.html"))
    assert os.path.exists(out)
    doc = open(out, encoding="utf-8").read()
    # les deux schémas, tous les événements (Phase A→D), la colonne OI et les seuils
    for token in ("ACCUMULATION", "DISTRIBUTION", "SC", "BC", "AR", "ST", "SOS", "SOW",
                  "SPRING", "UTAD", "LPS", "LPSY", "OI attendu", "Validé si", "Invalidé si"):
        assert token in doc
    assert "×2.5" in doc and "×1.4" in doc and "×0.8" in doc and "1.2 ATR" in doc
