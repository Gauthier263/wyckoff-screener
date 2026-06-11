"""Test synthétique : le mémo reflète les seuils + l'OI, et rend bien un PNG."""
import os

from screener.events import Thresholds
from screener.theory_table import build_theory_image, theory_rows


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


def test_build_theory_image_png(tmp_path):
    out = build_theory_image(Thresholds(), out_path=str(tmp_path / "memo.png"))
    assert os.path.exists(out)
    with open(out, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"  # signature PNG
