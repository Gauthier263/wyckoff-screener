# CrypNuevo — méthode extraite (base du skill biais HTF)

Source : `research/crypnuevo_tweets.md` (158 entrées, 01/01 → 22/11/2026). But : traduire sa méthode
en critères **automatisables** pour l'outil de biais 1D/4h (BTC), sans copier aveuglément ses conclusions.

## 1. Son pipeline de décision (ordre constant dans les « Sunday update »)

| Étape | Ce qu'il regarde | Règle qu'il applique |
|---|---|---|
| 1. Cadre HTF | Range 1D/1W (highs, lows, **mid-range**), ranges emboîtés (60–80k puis 75–81k), 1W50EMA | Ne trade **que les extrêmes** ; mid-range = pas de trade, mais cible de TP / résistance |
| 2. Tendance | **1W50EMA** (indicateur de tendance), 1D50EMA, 4h50EMA ; clôture 1W au-dessus/en dessous | Sous la 1W50EMA = biais baissier ; la perdre/reprendre change la cible (mid-range) |
| 3. Carte de liquidité | Mèches (50 %/100 %, 1h→1W), heatmap Hyblock HTF (1 mois/15 min) et LTF (7 j/5 min), Liquidation Levels + **Delta**, Open Positions (murs d'OI / thin air), Liquidity Pools (imbalance de grosses bougies), liquidité sous double creux / trendline | « La liquidité est un aimant » ; LTF plus fiable que HTF ; un amas touché ne sert plus |
| 4. Ordre du chemin | Quelle liquidité d'abord ? (« efficient move ») | Faux mouvement vers la liquidité proche (liquidity run, faux mouvement du lundi), puis la cible principale ; à 50/50 → « trade the second move » |
| 5. Comportement | Déviation, Three Taps (timing du 3ᵉ), W, sweep, Bart Simpson ; **mèches sans progression** = MM qui accumulent/distribuent ; **bougies vertes à fort volume rejetées sur résistance** = construction de shorts ; sur-extension vs EMA → retour aux EMA ; EMAs qui rattrapent / tunnel 4H50–1D50 | Lecture de l'intention du MM via volume + mèches |
| 6. Confirmation | **Acceptance** (clôtures / consolidation, S/R flip avec retest), jamais une mèche ; clôture 1W | Trigger d'entrée + invalidation **définis avant** ; sortie B/E |
| 7. Catalyseurs / timing | FOMC, CPI/PPI, PCE, résultats S&P (NVDA…), géopolitique, fériés US, ouverture des futures lundi, corrélation SPX/NVDA, saisonnalité (septembre), sentiment contrarian | Le catalyseur fixe la fenêtre, pas la direction |
| 8. Risque | 2–4 entrées échelonnées (15–25 % puis 70 % max), levier x4, TP sur zones de liquidité | — |

## 2. Correspondance avec notre doctrine Wyckoff (il n'emploie pas les termes)

| CrypNuevo | Wyckoff / VSA (notre code) |
|---|---|
| Range deviation (sous les lows / au-dessus des highs) | Spring / UTAD |
| Three Taps (low forms / swept / retest) | SC → spring → ST / LPS (et miroir BC → UTAD → LPSY) |
| Bougies vertes à fort volume rejetées sur résistance | BC / UTAD, offre qui absorbe (`absorption` per-barre) |
| Mèches sans progression | Absorption / test (`no_supply` / `no_demand`) |
| Acceptance (push + retest) | SOS + LPS (« breakout = SOS seulement après back-up ») |
| Mid-range | Milieu de plage (creek / ice) |
| Liquidity run / faux mouvement du lundi | Upthrust / spring de session |

→ Le skill peut parler **les deux langues** : ses niveaux de liquidité + nos étiquettes Wyckoff.

## 3. Règles quantifiables relevées (à tester, pas à croire)

- Mèche longue → **50 % rempli** « tôt ou tard » ; revisiter le 50 % après remplissage → 100 % probable ; délai cité 5–8 bougies hebdo (1W) ou ~1 semaine (4h/1h).
- **Exception (22/11)** : mèche sur-étendue **sous les range lows due aux liquidations** → peut rester non remplie (V-shape).
- Delta de liquidations (Hyblock, réglage « max liquidity ») : ~17–18 Md$ = risque moyen, > 25–30 Md$ = risque élevé de squeeze ; « delta reset » (14 → 5 Md$) = rééquilibrage.
- 3ᵉ tap trop proche du 2ᵉ → pas assez de liquidité → rupture plus probable.
- Gap CME rempli sous ~1 semaine — **obsolète** : CME BTC en 24/7 depuis fin mai 2026 (plus de nouveaux gaps).
- Sur-extension (ex. −25 % en 4 semaines) → rebond vers les EMA (+12 % réalisé vs +15 % attendu, juin).

## 4. Automatisable avec nos données gratuites

| Critère | Source | Faisabilité |
|---|---|---|
| Ranges 1D/1W emboîtés, mid-range, déviation, Three Taps, acceptance | ccxt OHLCV | Oui (détecteurs + tests synthétiques) |
| Mèches multi-TF 50 %/100 %, statut rempli/non | ccxt | Oui |
| EMA 50 (4h/1D/1W), sur-extension, tunnel | ccxt | Oui |
| Bougies volume sur résistance, mèches sans progression | `features.py` (VSA, absorption) | Déjà là |
| Heatmap / niveaux / delta de liquidations | Reconstruction Coinalyze (OI coin + delta perp) + Hyperliquid (positions réelles) + SmartMoney (liquidations réalisées) | À construire, valider vs ses captures datées |
| Open Positions (murs d'OI, thin air) | Reconstruction Coinalyze | À construire |
| Calendrier macro, SPX/NVDA | source calendrier gratuite à trouver, Yahoo | À tester |

## 5. Jeu de test : ses prévisions BTC datées

~40 prévisions BTC avec niveaux et issue documentée (ex. 06/01 → 80,6k atteint le 30/01 ; 08/11 → amas 74,7–73k touché le 12/11 ;
31/05 → setup faux, reconnu le 03/06 ; 15/11 → range lows 60k puis déviation à 55,1k). Double usage :
1. **Rejeu** : notre outil, figé à la date du tweet, retrouve-t-il ses niveaux (murs, amas, mèches, ranges) ?
2. **Lecture froide de son track record** : taux de réussite mesuré sur les prix réels, pas son « 34/34 » auto-déclaré.
