"""Test synthétique : le mémo « rappel théorie » se construit et reflète les seuils."""
import os

from screener.events import Thresholds
from screener.theory_table import build_theory_html


def test_build_theory_html(tmp_path):
    th = Thresholds(climax_vol=2.5, sos_vol=1.4, test_vol=0.8, wide_spread_atr=1.2)
    out = build_theory_html(th, out_path=str(tmp_path / "memo.html"))
    assert os.path.exists(out)
    doc = open(out, encoding="utf-8").read()

    # Les deux schémas et tous les événements (Phase A→D) sont présents.
    for token in ("ACCUMULATION", "DISTRIBUTION", "SC", "BC", "AR", "ST", "SOS", "SOW",
                  "SPRING", "UTAD", "LPS", "LPSY"):
        assert token in doc
    # Les seuils courants sont injectés (pas de valeurs en dur).
    assert "×2.5" in doc and "×1.4" in doc and "×0.8" in doc and "1.2 ATR" in doc
    # Colonnes de validité présentes.
    assert "Validé si" in doc and "Invalidé si" in doc
