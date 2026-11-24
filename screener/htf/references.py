"""references.py — points de contrôle pour valider la carte de liquidité.

Relevés des cartes Hyblock publiées par CrypNuevo entre janvier et novembre 2026,
transcrits depuis `research/crypnuevo_tweets.md`. Ils servent de **jeu de validation** :
le rejeu (`screener.htf.validate`) gèle nos données à chaque date et mesure l'écart.

Ce ne sont pas des vérités absolues. Ce sont les lectures d'un professionnel sur un outil
payant dont la méthode n'est pas publiée, relevées à l'œil sur des captures. Les niveaux
valent à environ 0,5 % près, les montants en dollars dépendent de son réglage « max
liquidity setting » et ne se transposent pas à nos quantités en coin. On s'en sert pour
mesurer un **placement**, pas pour recopier un chiffre.

Champs
------
- `asof`        : horodatage UTC de la capture (à défaut, celui du tweet).
- `price`       : prix BTC affiché sur la capture, quand il est lisible.
- `kind`        : `heatmap_htf` (lookback 1 mois, 15 min), `heatmap_ltf` (7 jours, 5 min),
                  `levels` (Liquidation Levels + Delta), `open_positions` (profil d'OI).
- `clusters`    : amas de liquidations, `side` = côté liquidé (`long` = sous le prix,
                  `short` = au-dessus), `status` = `pending` (annoncé) ou `hit` (déclaré
                  consommé sur la capture), `rank` = 1 pour le plus dense.
- `walls`       : murs de positions ouvertes (profil d'OI).
- `thin_air`    : zones annoncées sans positions.
- `counts`      : nombre de niveaux de liquidation distincts, par côté.
- `delta_busd`  : delta de liquidations cumulé en milliards de dollars, tel qu'il l'affiche.
- `note`        : sa phrase, en résumé.
"""
from __future__ import annotations

REFERENCES = [
    {"asof": "2026-01-04T16:12:00Z", "price": 91_165, "kind": "heatmap_htf",
     "clusters": [{"low": 91_000, "high": 91_500, "side": "short", "status": "hit"},
                  {"low": 95_800, "high": 96_200, "side": "short", "status": "pending",
                   "rank": 1}],
     "note": "liquidations 91-91,5k consommées le 03/01, prochaines à 96k"},

    {"asof": "2026-01-18T18:40:00Z", "price": 95_203, "kind": "heatmap_htf",
     "clusters": [{"low": 95_000, "high": 96_000, "side": "short", "status": "hit"},
                  {"low": 85_800, "high": 86_200, "side": "long", "status": "pending",
                   "rank": 1},
                  {"low": 87_800, "high": 88_200, "side": "long", "status": "pending"},
                  {"low": 84_000, "high": 85_000, "side": "long", "status": "pending"}],
     "note": "shorts du haut consommés, des longs apparaissent à 86k"},

    {"asof": "2026-01-25T16:09:00Z", "price": 88_700, "kind": "heatmap_htf",
     "clusters": [{"low": 86_100, "high": 86_500, "side": "long", "status": "pending",
                   "rank": 1}],
     "note": "HTF : liquidations clairement en bas, à 86,3k"},
    {"asof": "2026-01-25T16:09:00Z", "price": 88_700, "kind": "heatmap_ltf",
     "clusters": [{"low": 91_200, "high": 91_600, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 92_800, "high": 93_200, "side": "short", "status": "pending"},
                  {"low": 86_100, "high": 86_500, "side": "long", "status": "pending"}],
     "note": "LTF : un peu de carburant en haut à 91,4k"},

    {"asof": "2026-02-08T17:35:00Z", "price": 71_121, "kind": "heatmap_ltf",
     "clusters": [{"low": 71_800, "high": 72_200, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 76_000, "high": 77_000, "side": "short", "status": "pending"},
                  {"low": 79_300, "high": 79_700, "side": "short", "status": "pending"},
                  {"low": 80_300, "high": 80_700, "side": "short", "status": "pending"}],
     "note": "shorts empilés entre 72k et 80,5k après la mèche à 60k"},

    {"asof": "2026-04-05T18:53:00Z", "price": 67_285, "kind": "heatmap_htf",
     "clusters": [{"low": 63_700, "high": 64_600, "side": "long", "status": "pending",
                   "rank": 1},
                  {"low": 72_000, "high": 73_500, "side": "short", "status": "pending"}],
     "note": "liquidations HTF à 64-64,5k, carburant pour aller plus bas"},

    {"asof": "2026-04-12T21:57:00Z", "price": 71_303, "kind": "heatmap_htf",
     "clusters": [{"low": 64_000, "high": 64_500, "side": "long", "status": "pending",
                   "rank": 1},
                  {"low": 72_500, "high": 74_000, "side": "short", "status": "hit"}],
     "note": "la bande 64-64,5k devrait tirer le prix vers le bas du range"},

    {"asof": "2026-04-26T22:01:00Z", "price": 75_800, "kind": "heatmap_htf",
     "clusters": [{"low": 79_700, "high": 80_000, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 70_000, "high": 70_400, "side": "long", "status": "pending"}],
     "note": "liquidations des deux côtés : 80k en haut, 70k au mid-range"},

    {"asof": "2026-05-10T19:56:00Z", "price": 81_296, "kind": "heatmap_ltf",
     "clusters": [{"low": 82_900, "high": 83_200, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 78_500, "high": 79_200, "side": "long", "status": "pending"},
                  {"low": 77_000, "high": 77_400, "side": "long", "status": "pending"}],
     "note": "plus de carburant en bas, mais les shorts de 83,2k partiront d'abord"},

    {"asof": "2026-05-21T22:49:00Z", "price": 77_644, "kind": "heatmap_ltf",
     "clusters": [{"low": 79_300, "high": 79_700, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 78_200, "high": 78_600, "side": "short", "status": "pending"}],
     "note": "liquidations à 79,4k, pile sur les range highs"},

    {"asof": "2026-06-07T16:22:00Z", "price": 62_361, "kind": "heatmap_htf",
     "clusters": [{"low": 64_500, "high": 64_900, "side": "long", "status": "hit"},
                  {"low": 61_800, "high": 62_200, "side": "long", "status": "hit"},
                  {"low": 78_500, "high": 80_500, "side": "short", "status": "pending",
                   "rank": 1}],
     "note": "toutes les liquidations de longs consommées ; il ne reste que les shorts à 80k"},

    {"asof": "2026-07-05T17:04:00Z", "price": 62_600, "kind": "levels",
     "counts": {"long": 443, "short": 67}, "delta_busd": 14.0,
     "clusters": [{"low": 57_500, "high": 62_000, "side": "long", "status": "pending",
                   "rank": 1},
                  {"low": 63_500, "high": 65_000, "side": "short", "status": "pending"}],
     "note": "14 Md$ de liquidations de longs accumulées : latéral ou petit repli"},

    {"asof": "2026-07-06T14:25:00Z", "price": 61_956, "kind": "levels",
     "counts": {"long": 370, "short": 198}, "delta_busd": 5.0,
     "note": "delta reset : les 14 Md$ retombent à 5 Md$"},

    {"asof": "2026-07-12T19:17:00Z", "price": 64_038, "kind": "heatmap_ltf",
     "clusters": [{"low": 64_700, "high": 65_100, "side": "short", "status": "pending",
                   "rank": 1}],
     "note": "amas 64,7-65,1k juste au-dessus du prix"},
    {"asof": "2026-07-12T19:17:00Z", "price": 64_038, "kind": "levels",
     "delta_busd": 3.0,
     "clusters": [{"low": 66_200, "high": 66_600, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 64_900, "high": 65_300, "side": "short", "status": "pending"},
                  {"low": 64_300, "high": 64_700, "side": "short", "status": "pending"}],
     "note": "niveaux les plus fournis : 66,4k / 65,1k / 64,5k ; delta négligeable"},

    {"asof": "2026-08-03T01:22:00Z", "price": 63_400, "kind": "heatmap_ltf",
     "clusters": [{"low": 62_000, "high": 62_400, "side": "long", "status": "hit"},
                  {"low": 65_500, "high": 66_000, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 61_800, "high": 62_200, "side": "long", "status": "pending"}],
     "note": "62,2k consommé, le gros est désormais au-dessus"},

    {"asof": "2026-08-09T11:25:00Z", "price": 64_814, "kind": "heatmap_htf",
     "clusters": [{"low": 61_500, "high": 61_900, "side": "long", "status": "pending",
                   "rank": 1},
                  {"low": 65_800, "high": 66_200, "side": "short", "status": "pending"},
                  {"low": 66_800, "high": 67_200, "side": "short", "status": "pending"}],
     "note": "bande forte sous le double creux, à 61,7k"},

    {"asof": "2026-08-16T08:53:00Z", "price": 63_072, "kind": "heatmap_htf",
     "clusters": [{"low": 61_400, "high": 61_800, "side": "long", "status": "pending",
                   "rank": 1},
                  {"low": 65_800, "high": 66_200, "side": "short", "status": "pending"}],
     "note": "liquidité en construction sous le creux local, jusqu'à 61,6k"},

    {"asof": "2026-09-20T09:44:00Z", "price": 80_156, "kind": "levels",
     "counts": {"long": 312, "short": 121}, "delta_busd": 17.0,
     "clusters": [{"low": 73_000, "high": 78_000, "side": "long", "status": "pending",
                   "rank": 1}],
     "note": "17 Md$ de longs : risque moyen de repli (élevé au-delà de 25 Md$)"},

    {"asof": "2026-09-27T10:35:00Z", "price": 84_508, "kind": "heatmap_ltf",
     "clusters": [{"low": 85_100, "high": 85_500, "side": "short", "status": "pending",
                   "rank": 1},
                  {"low": 82_300, "high": 82_800, "side": "long", "status": "pending"}],
     "note": "85,3k est la zone la plus dense ; 82,5k plus large et moins dense"},

    {"asof": "2026-09-29T06:30:00Z", "price": 83_838, "kind": "heatmap_ltf",
     "clusters": [{"low": 82_500, "high": 82_800, "side": "long", "status": "hit"},
                  {"low": 85_100, "high": 85_500, "side": "short", "status": "pending",
                   "rank": 1}],
     "note": "stops sous le support pris, cap sur 85,3k"},

    {"asof": "2026-10-25T20:25:00Z", "price": 80_066, "kind": "heatmap_ltf",
     "clusters": [{"low": 80_500, "high": 80_900, "side": "short", "status": "hit"},
                  {"low": 80_000, "high": 80_400, "side": "short", "status": "hit"},
                  {"low": 78_600, "high": 79_000, "side": "long", "status": "pending",
                   "rank": 1}],
     "note": "prochaines liquidations à 78,8k, elles seront probablement touchées"},

    {"asof": "2026-11-08T04:14:00Z", "price": 75_885, "kind": "open_positions",
     "walls": [76_600],
     "note": "mur d'OI à 76,6k : résistance de court terme"},
    {"asof": "2026-11-08T04:14:00Z", "price": 75_885, "kind": "heatmap_htf",
     "clusters": [{"low": 79_300, "high": 79_700, "side": "short", "status": "hit"},
                  {"low": 73_000, "high": 74_700, "side": "long", "status": "pending",
                   "rank": 1}],
     "note": "amas 73-74,7k, la zone la plus fournie ; sera touchée le 12/11"},

    {"asof": "2026-11-15T21:35:00Z", "price": 65_016, "kind": "levels",
     "counts": {"long": 144, "short": 606}, "delta_busd": 18.0,
     "note": "18 Md$ de shorts : risque moyen de squeeze (pic à 24 Md$ à 62k)"},

    {"asof": "2026-11-22T05:11:00Z", "price": 58_924, "kind": "open_positions",
     "walls": [58_600], "thin_air": [(62_800, 65_800)],
     "note": "mur 58,6k difficile à casser ; au-dessus de 60,6k, peu d'OI"},
    {"asof": "2026-11-22T05:11:00Z", "price": 58_924, "kind": "heatmap_ltf",
     "clusters": [{"low": 65_500, "high": 66_500, "side": "short", "status": "pending",
                   "rank": 1}],
     "note": "le gros des liquidations est en haut, à 66k"},
]


def by_kind(kind: str) -> list:
    return [r for r in REFERENCES if r["kind"] == kind]


def rank1(ref: dict) -> "dict | None":
    """L'amas que la capture désigne comme le plus dense, s'il y en a un."""
    for c in ref.get("clusters", []):
        if c.get("rank") == 1:
            return c
    return None
