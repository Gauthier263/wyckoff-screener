# Mémo Deep Focus Test Composite Operator

*Le CO teste avant de payer : à quoi sert chaque test Wyckoff, comment le vérifier, comment le trader. BTC perps H1/H4 et or. Rédigé le 31/10/2026 pour Gauthier. Aide à la décision discrétionnaire, jamais d'exécution automatique.*

Le test est le contrôle-qualité de la campagne : le Composite Operator (CO) revient sur une zone où l'offre s'est montrée et mesure ce qu'il en reste avant de marquer les prix. La doctrine compare le volume du test à celui de **l'action testée** (climax, spring, saut), pas à une moyenne mobile. Elle ne valide le test que par la **réponse** qui suit. Ce mémo reprend chaque test phase par phase, en accumulation puis en miroir distribution, avec une fiche au format identique. Il ajoute l'économie qui pousse le CO à tester, une grille de diagnostic de maturité, un playbook et un errata du premier mémo (`docs/memo_tests_CO.md`). Les seuils chiffrés du screener sont des **heuristiques internes** : aucune source primaire ne donne de multiples de volume ni de fractions d'ATR.

## Sommaire

1. Cadre : trois sens du mot « test », sources, conventions, grille universelle de validité
2. Penser comme le CO / market maker : l'économie de la campagne
3. Fiches de tests — accumulation (Phases A → E)
4. Micro-tests VSA : barre de test, no supply, no demand
5. Fiches de tests — distribution (miroir)
6. Distinctions rigoureuses et divergences des sources
7. Diagnostic de l'état d'une consolidation
8. Playbook de trading par setup
9. Seuils du screener et écarts doctrine ↔ code
10. Errata du premier mémo
11. Conclusion : ce que ce mémo change
12. Glossaire FR/EN
13. Bibliographie commentée

## L'essentiel en 15 lignes

1. **Un test mesure, il ne construit pas** : la cause naît de l'absorption (climax, Phase B), le test vérifie qu'il ne reste plus d'offre avant le markup ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)).
2. **Trois sens du mot** : chez Wyckoff (1910–1932), toute sonde dont la réponse révèle l'équilibre offre/demande ; chez SMI/WA, un retour à spread et volume réduits ; chez Williams, une barre de marquage baissier qui reprend sur faible volume.
3. **Référence de volume = l'événement testé** : vol(test) < vol(spring), vol(ST) < vol(SC), vol(BU) < vol(saut). Le filtre `vol_ratio ≤ 0.85` (×MA20) est une convention du screener.
4. **Un test réussi prouve l'absence d'offre, pas la présence de demande** : il faut une réponse haussière en 1–3 barres. Sans réponse, Williams parle de *negative action*, donc de faiblesse, pas d'un signal neutre.
5. **Test volumique = test raté par défaut**, avec re-test attendu (forme en « W »). Mais Williams admet des tests à fort volume en futures et sur *bad news* : sur perps, l'OI en coin départage.
6. **Springs : numérotation stable** chez SMI, Fraser et Villahermosa. #3 = léger et sec, pas de test requis ; #2 = modéré et volumique, on achète le test ; #1 = shakeout / terminal shakeout, test obligatoire (et Fraser : ne pas l'acheter).
7. **Vocabulaire en couches** : *test*, *secondary reaction*, *terminal shake-out*, *upthrust*, *springboard* sont de Wyckoff ; *spring*, *creek*, *JAC*, *back-up*, *ice*, *UTAD* viennent de l'ère SMI/Evans ; les schémas A–E sont postérieurs à 1934.
8. **« LPS » a au moins quatre sens** selon l'auteur. Le mémo sépare le LPS de Phase C, le LPS de Phase D dans la plage, et le BU/BUEC (LPS sur l'ancienne résistance).
9. **On n'achète pas une cassure** ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)). Elle devient JAC/SOS majeur seulement après tenue + BU sec ; sinon c'est un UT/UTAD.
10. **Le LPSY peut se faire sur volume faible ou fort** (Pruden) : son critère robuste est le spread étroit + l'échec sous la résistance (sommet plus bas, rejet sous la glace).
11. **Économie du CO** : l'impact croît en racine carrée de la taille (1 % du volume quotidien ≈ 0,1 σ) et reste en partie permanent. Le CO accumule donc passivement dans les flux forcés (climax, stops, liquidations) et ne marque qu'après avoir vérifié l'offre.
12. **Stops et liquidations sont le carburant des springs/UTAD** (Osler), mais les effets mesurés sont modestes (≈ 4–5 points de pourcentage). Un test est une inclinaison de probabilité plus un point de risque défini, pas une certitude.
13. **Maturité** = séquence accomplie + gradient de volume décroissant sur les creux + Phase B ≥ Phase A + test de Phase C sec + réponse. Dans un downtrend, la plage est une redistribution par défaut.
14. **Neuf tests d'achat** : la plus ancienne liste trouvée est dans le cours de 1937 (Wyckoff Associates, posthume). L'ordre courant (Pruden 2007 / StockCharts) est réordonné et fusionne PS + SC + ST.
15. **Screener** : les seuils sont des heuristiques. Écarts majeurs : `narrow_spread_atr` n'est utilisé par aucun détecteur, il n'y a pas de détecteur « test du spring », les types de spring ne sont pas classés, et SOS/LPS sont étiquetés sans tenue ni BU.

## 1. Cadre : ce qu'est un test, d'où viennent les mots, comment lire ce mémo

### 1.1 Trois traditions donnent trois sens au mot « test »

| Tradition | Définition du test | Citation clé | Source |
|---|---|---|---|
| **Wyckoff 1910–1932** (classique) | Toute **action** d'un gros opérateur dont la **réponse** révèle l'équilibre : achat-sonde, vente-sonde, marquage d'un titre meneur, raid, retrait du soutien, enquête sur le carnet, nouvelles | « Large operators often test the market for a stock by buying 5,000 to 25,000 shares in order to see how easily they can buy it, or by selling a similar quantity to ascertain how well the market will absorb their selling. » | Cours 1937, §8M p.1 ([archive.org](https://archive.org/details/WyckoffMethodOfTapeReading)) |
| | Le petit trader lit gratuitement les tests des autres | « You, sitting at the ticker, can observe at once whether these tests bring a bullish or bearish response; and you are just as free to act upon them as if you had made them yourself. » | Division *Tape Reading* ©1932, TR §10 p.6 ([archive.org](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)) |
| **SMI / Wyckoff Analytics** (moderne) | Retour vers une zone d'action (SC, spring, borne franchie) sur spread et volume réduits, creux plus haut | « Large operators always test the market for supply throughout a TR (e.g., STs and springs) and at key points during a price advance. If considerable supply emerges on a test, the market is often not ready to be marked up. » | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) |
| **Fraser** (StockCharts) | Toute action climactique appelle un test, à toutes les échelles | « A Climax is an Action. Such an Action must be Tested. » · « The Test is a visual question: Is the majority of the selling exhausted? » | [Fraser, Action – Test (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test) |
| **VSA — Williams** | Marquage à la baisse dans une zone d'offre antérieure, qui reprend pour clôturer haut, sur volume plus faible | « Testing is by far the most important of the low volume buy signals. » (p.34) | [Master the Markets, 4ᵉ éd.](https://www.tradeguider.com/mtm_251058.pdf) |

> **À retenir** — Le test moderne (retour sec vers le low du SC ou du spring) n'est qu'un cas particulier du test classique. Chez Wyckoff, « test » désigne toute sonde dont on lit la réponse ; il n'emploie jamais *secondary test* mais *secondary reaction* ([Cours 1937, §7M](https://archive.org/details/WyckoffMethodOfTapeReading)).

### 1.2 Les sources se superposent en couches, et leurs labels aussi

| Couche | Auteurs et textes | Apport sur les tests | Statut dans ce mémo |
|---|---|---|---|
| Wyckoff (1910–1932 ; cours révisé 1934, 1936–37) | *Studies in Tape Reading* (1910, « Rollo Tape »), *How I Trade* (1922), Cours ©1931–33, division *Tape Reading* ©1932 | test = sonde ; *secondary reaction* ; *terminal shake-out* ; *springboard* ; Composite Man ; neuf tests (pages de 1937) | Texte intégral OCR lu |
| Lefèvre / Livermore (1923) | *Reminiscences of a Stock Operator* | *testing order*, *feeling-out plays*, coût des sondes | Texte Gutenberg lu |
| Evans / SMI (≈ années 1950–1970) | Conférences *Evans Echoes*, glossaire SMI, blog de Jim O'Brien | spring #1/#2/#3, creek/JAC/back-up, ice, UTAD | Glossaire et blog lus ; **aucun texte primaire d'Evans** |
| Forte (1994) → Pruden & von Lichtenstein (2006) → Pruden (2007) | « The Anatomy of a Trading Range » ; *Market Technician* n°55 ; *The Three Skills of Top Trading* | schémas A–E, légendes, cas Nokia, points d'entrée 8/10/12/14 | Article 2006 lu ; **livre 2007 non consulté** |
| Wyckoff Analytics / StockCharts (Bogomazov, Lipsett, schémas édités par Pruden) | Tutoriel ChartSchool, PDF WA, article S&C 2014 | ST in Phase B, spring & test, LPS/BU, neuf tests adaptés de Pruden 2007 | Lu (WA et StockCharts = une seule source) |
| Fraser (blog *Wyckoff Power Charting*, 2015–2022) | ~20 articles | Action–Test, types de spring et entrées, LPS de Phase C, JAC/BUEC, distribution | Lu |
| Villahermosa (article 2018, site 2026) | *TheTicker* n°1 ; tradingwyckoff.com | UA, ST as SOW, mSOW, mSOS, typologie des LPS, FTI | PDF 2018 lu ; site lu en partie (anti-bot sur la page Spring) |
| Weis (2013) | *Trades About to Happen* (extrait de l'éditeur) | provenance des schémas et du vocabulaire | Introduction seulement |
| VSA : Williams (1993/2000/2009), TradeGuider/Holmes (2011), Coulling | *Master the Markets* 4ᵉ éd. ; glossaire des indicateurs TG ; ch. 5 de Coulling | barre de test, no supply/no demand, re-test, background, test en marché haussier | PDF lus |
| Microstructure (1985–2026) | Kyle, Tóth/Bouchaud, Osler, Avellaneda–Stoikov, etc. | fondements économiques (analogies) | Articles et abstracts |

> **Piège** — Weis rappelle que les modèles et le vocabulaire imagé sont postérieurs à Wyckoff : « Wyckoff never used such terminology; however, that does not make them forbidden or useless » ; les schémas « were added after his death » ([Weis 2013, extrait](https://content.e-bookshelf.de/media/reading/L-802008-2fe9f872b5.pdf)). Il met aussi en garde contre les « cookie prints » plaqués sur le prix.

### 1.3 Conventions de lecture

**Étiquettes de fiabilité** (utilisées partout) : **[D]** documenté (doctrine ou fait établi, sourcé) · **[H]** heuristique interne du screener (non sourcée) · **[I]** inférence ou analogie (raisonnement, non testé) · **[NV]** non vérifié (source vue en extrait ou inaccessible).

| Convention (CLAUDE.md) | Application aux tests |
|---|---|
| **Top-down** | Déclarer le contexte HTF (Daily/H4) avant d'étiqueter. Une plage dans un downtrend est une **redistribution par défaut**. On tient les deux scénarios jusqu'à la sortie de plage, avec des étiquettes conditionnelles (« test de résistance = SOS *ou* UTAD selon la tenue »). Un breakout n'est un SOS qu'après tenue + back-up. Dès que le prix fait l'inattendu, on re-questionne le cadre. |
| **Fractal** | Déclarer la TF et la structure avant d'étiqueter. Un ST in B sur H4 peut être une accumulation complète sur H1 ([Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/)). On étiquette relativement à la plage de **cette** structure. |
| **Ordre de lecture** | ① volume/spread (effort vs résultat) → ② OI **en coin** (le volume ouvre-t-il ou ferme-t-il des positions ?) → ③ tierces (ratio long/short, funding, liquidations) **seulement si l'OI est ambigu**. Puis on lit OI + tierces ensemble pour en tirer un sens commun. |
| **OI en coin** | ΔOI_USD % ≈ ΔOI_coin % + Δprix % : l'OI en USD monte sur un rallye même quand les positions baissent. Cas BTC 64 800 : OI USD +0,81 % mais OI coin −0,36 %, ce qui implique un prix ≈ +1,17 %, donc du short covering [D, arithmétique sur les champs Binance `sumOpenInterest` / `sumOpenInterestValue`] ([Binance API](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics)). |
| **Données tierces** | Ratio L/S Binance = **nombre de comptes**, pas taille ([Binance](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio)). Flux de liquidations : « only the latest one liquidation order within 1000ms will be pushed », donc les totaux sont des **planchers** ([Binance](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams)). Funding positif = les longs paient ([Binance FAQ](https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031)). Coinalyze : `convert_to_usd` = « false » par défaut ([Coinalyze API](https://api.coinalyze.net/v1/doc/)). |
| **Niveaux justifiés** | Chaque prix-clé est suivi, entre parenthèses, de l'événement ou de la borne qui le définit. |
| **Code couleur** | Ronds = événements : 🟢 demande/force (SC, SOS, JAC) · 🔴 offre (BC, SOW, ST as SOW, no demand) · 🟠 piège (UA/UT, UTAD, upthrust) · 🔵 bornes et tests de borne (AR, ST, LPS, BU, LPSY) · 🟣 Phase C (spring, test du spring, LPS de Phase C, test de l'UTAD). Carrés = niveaux : 🟦 bornes de plage (low du SC, high de l'AR, creek, glace) · 🟪 pivot de Phase C (low du spring, high de l'UTAD testé) · 🟩 objectif haussier / niveau de demande · 🟥 résistance / offre / objectif baissier · 🟧 extrême d'un piège (high d'un UT/UA). |

**Seuils du screener** (`config.yaml`, tous **[H]**) : `climax_vol ≥ ×2.0` · `sos_vol ≥ ×1.3` · `wide_spread_atr ≥ 1.3` · `narrow_spread_atr ≤ 0.7` · `test_vol ≤ ×0.85` · `pen_atr ≥ 0.1` ATR · `reclaim_clv 0.5` (CLV = (C−L)/(H−L), 0 = clôture au plus bas, 1 = au plus haut). « Test raté ≈ ≥ ×1.5 » est une convention du projet (CLAUDE.md), sans source. Section 9 : où chaque seuil est (ou n'est pas) appliqué dans le code.

### 1.4 La grille universelle de validité d'un test sépare le nécessaire, la qualité et la validation

Le premier mémo exigeait cinq conditions « toutes nécessaires ». Les sources hiérarchisent plutôt : **trois conditions nécessaires**, **trois critères de qualité**, **une validation**.

<!-- FIG:test_validity -->

| # | Condition | Ce que disent les sources | Proxy screener | Statut |
|---|---|---|---|---|
| 1 | **Cause en amont** : climax, spring, shakeout, SOS, absorption | « Testing is a good sign of strength (as long as you have strength in the background) » ; même test avec de la distribution derrière « means little » ([MTM p.34, p.110](https://www.tradeguider.com/mtm_251058.pdf)) | position dans la séquence (`window.py`) | **Nécessaire** [D] |
| 2 | **Lieu** : retour vers la zone d'action (low du SC ou du spring, borne franchie) | « Any down-move dipping into an area of previous selling (previous high volume level)… » ([MTM p.35](https://www.tradeguider.com/mtm_251058.pdf)) ; « Watch for tests of high‐volume or "vertical" areas » ([Weis](https://content.e-bookshelf.de/media/reading/L-802008-2fe9f872b5.pdf)) | distance à la borne | **Nécessaire** [D] |
| 3 | **Volume < volume de l'action testée**, et en baisse d'un passage à l'autre | « the volume is less than on the Spring day » ([Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)) ; « an even lower-volume test of that spring » ([WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)) | `vol_ratio ≤ 0.85` = filtre secondaire ; ratio vol_test/vol_action à ajouter | **Nécessaire** [D] + [H] |
| 4 | **Spread** : étroit à l'échelle du swing (Wyckoff). À l'échelle d'une barre VSA : mèche de marquage + clôture haute, sans exigence de range étroit | « A high quality test is one that unfolds on narrowing price spreads and decreasing volumes » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) vs « If the spread is narrow it will have less impact » (indicateur TG « Basic Test », [Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)) | `spread_atr ≤ 0.7` (**non appliqué** par le code) | Qualité [D] |
| 5 | **Creux** : plus haut que le creux testé = haute qualité ; léger sous-percement sur volume plus faible = qualité moindre ; plus bas **et** plus volumique = rejet | « A successful Test can occur above, at, or below the Selling Climax low and still be successful » ([Fraser, Action – Test (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)) ; « The lowest quality tests are those that make a lower low than the spring and are done on higher volume » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) | low(test) vs low(action) | Qualité / rejet [D] |
| 6 | **Clôture** milieu ou haut de barre | « close on, or near the high » (fort) ; « middle or high » (permissif) ([MTM](https://www.tradeguider.com/mtm_251058.pdf)) | `clv ≥ 0.5` | Qualité [D] + [H] |
| 7 | **Réponse** : hausse dans 1–3 barres | « Any testing that does not respond immediately with higher prices, or certainly during the next day or so, can be considered an indication of weakness » ; *negative action* si rien en « two or three days (or bars) » ([MTM p.35, p.152](https://www.tradeguider.com/mtm_251058.pdf)) ; « Tests need TWO BARS » ([TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)) | non implémentée | **Validation** [D] |
| 8 | **Overlay crypto** : OI coin plat ou ↓ | aucune source classique ne traite de l'OI | `oi_chg` (`window.py`) | Convention projet [I] ; OI↑ = ambigu → tierces |

> **Penser comme le CO** — Le test répond à une seule question : « si je cesse de soutenir, qui vend encore ? ». Un volume faible dit « presque personne », et cela coûte peu à vérifier. Un volume fort dit « quelqu'un, mais je ne sais pas combien », donc je reviendrai.

## 2. Penser comme le CO : une grosse position coûte cher à construire, d'où le test

Wyckoff présente le Composite Man comme une fiction utile : « all the fluctuations in the market and in all the various stocks should be studied as if they were the result of one man's operations » ([Cours 1937, §9M p.1, page ©1931](https://archive.org/details/WyckoffMethodOfTapeReading)). Il le dit lui-même : « There is no Composite Operator » ; l'effet combiné des banquiers, pools, gros opérateurs, *floor traders* et du public est simplement « of the same effect as if it were produced by one man's operations » ([TR §10 pp.4–5](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)). Cette section dit ce que la microstructure **établit** et ce qui reste une **analogie** quand on l'applique aux tests.

### 2.1 Le CO connaît sa position mais pas l'offre des autres

| Le CO sait | Le CO ignore | Comment il comble l'écart | Source |
|---|---|---|---|
| Sa taille, son prix de revient, ses ordres de camouflage | L'offre latente des autres : stops sous les creux, longs piégés plus haut, autres opérateurs | **Sondes** : achat ou vente de 5 000–25 000 actions « to see how easily they can buy it » ou « how well the market will absorb their selling » | [Cours §8M p.1](https://archive.org/details/WyckoffMethodOfTapeReading) [D] |
| Où il a placé des ordres de soutien | Si le titre tient seul | **Retrait du soutien** : Keene « would leave the market absolutely alone, to see how it would take care of itself » | [Lefèvre, ch. XX](https://www.gutenberg.org/ebooks/60979) [D] |
| Le niveau où il veut monter | La quantité offerte au-dessus | **Enquête sur le carnet** : « How much is offered in the next five points up? » | [Cours §14M p.4](https://archive.org/details/WyckoffMethodOfTapeReading) [D] |
| Les secteurs qu'il pourrait mener | Si le public suivra | **Marquage d'un meneur** : « First he tests out the rails by advancing Union Pacific one or two points. He observes how much response is given » | [TR §9 p.4](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks) [D] |
| Ce qu'il doit encore acheter | Le prix de l'offre résiduelle | **Raids** : « he drives several stocks downward to weaken the market so he can complete his purchases on the reaction. These drives are also his tests. » | [TR §10 p.2](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks) [D] |
| — | Ce que montrera le carnet | La liquidité est surtout **latente** : « most of the volume is latent and not revealed » | [Tóth et al. 2011](https://arxiv.org/pdf/1105.1694) [D] |

Les sondes ont un coût. Livermore : « In the course of accumulating my full line I might chip out fifty or sixty thousand dollars in these feeling-out plays of mine. This looks like a very expensive testing, but it wasn't. » ([Lefèvre, ch. X](https://www.gutenberg.org/ebooks/60979)). Wyckoff en tire la règle du lecteur : « A small operator is unable to test the market in this way before he takes a position, but by a close study of his charts, he is able to estimate the comparative strength or weakness » ([Cours §8M p.1](https://archive.org/details/WyckoffMethodOfTapeReading)).

### 2.2 L'impact en racine carrée oblige à accumuler lentement et passivement

| Mécanisme | Fait établi [D] | Lecture CO (analogie [I]) |
|---|---|---|
| **Loi en racine carrée des métaordres** | Δ(Q) = Y·σ·√(Q/V), Y d'ordre 1, exposant δ entre 0,4 et 0,7 ; « trading one hundredth of the daily volume moves the price by a tenth of its daily volatility » ([Tóth et al. 2011](https://arxiv.org/pdf/1105.1694)). Confirmée sur Bitcoin avec plus d'un million de métaordres, « which holds on four decades » ([Donier & Bonart](https://arxiv.org/abs/1412.4503)). Peu dépendante du calendrier d'exécution ([Bouchaud 2024](https://bouchaud.substack.com/p/the-square-root-law-of-market-impact)) | Une grosse position ne s'achète pas vite : elle s'étale dans le temps, d'où la **plage**. Calcul illustratif (σ quotidien BTC supposé à 3 %, Y = 1) : 1 % du volume quotidien ≈ +0,30 % ; 10 % ≈ +0,95 %. Le coût total croît comme Q^1,5 : doubler la taille multiplie le coût par ≈ 2,8 |
| **Impact en partie permanent** | Après exécution, l'impact se stabilise vers **≈ 2/3 du pic** ([Farmer et al.](https://arxiv.org/abs/1102.5457)), y compris pour des métaordres passifs en ordres limites (Said et al. 2018, [NV], extrait) | Marquer avec de l'offre encore présente, c'est acheter contre son propre impact. Si l'offre latente revient quand il cesse d'acheter, le prix retombe et le CO garde un stock payé trop cher : c'est **ce que le test évite** |
| **Kyle (1985)** | Le bruit des autres « provides camouflage which conceals his trading from market makers » ; dans le modèle à une période, l'initié révèle la moitié de son information ([Kyle 1985](https://www.econometricsociety.org/publications/econometrica/1985/11/01/continuous-auctions-and-insider-trading) ; [notes](https://ronming1303.github.io/documents/Kyle_1985_.pdf)) | Le CO se cache dans le volume des autres : climax, paniques, chasses aux stops |
| **Fourniture vs prise de liquidité** | Les traders informés à information durable préfèrent les **ordres limites** ([Kaniel & Liu 2006](https://ideas.repec.org/a/ucp/jnlbus/v79y2006i4p1867-1914.html)) et sont plus actifs « when measured stock liquidity is high » ([Collin-Dufresne & Fos](https://www.nber.org/papers/w18452)) | Le CO achète **passivement dans les flux forcés** (SC, spring) puis **devient agressif** au SOS/JAC, quand son horizon raccourcit |
| **Flux net vs volume brut** | La variation de prix est linéaire dans le déséquilibre d'ordres (OFI), avec une pente inversement proportionnelle à la profondeur ([Cont, Kukanov & Stoikov](https://arxiv.org/abs/1011.6402)) | **Effort sans résultat** : volume brut élevé, déséquilibre net ≈ 0 parce que des offres passives absorbent les ventes, donc le prix stagne. C'est l'absorption de Phase B |
| **Passif n'est pas invisible** | 44 % du volume d'ordres est caché sur Euronext-Paris ([Bessembinder et al.](https://papers.ssrn.com/ab_id=956476)) ; les icebergs sont détectés ([Frey & Sandås](https://gfk-cfs.de/media//08_48.pdf)) ; les HFT s'adossent puis suivent les ordres informés ([van Kervel & Menkveld](https://econpapers.repec.org/RePEc:bla:jfinan:v:74:y:2019:i:3:p:1091-1137)) | L'absorption laisse des traces : volume groupé sur les bas, flux acheteur net négatif pendant que le prix tient |
| **Almgren–Chriss** | Plus le trader est averse au risque, plus l'exécution est concentrée au début ([modèle](https://en.wikipedia.org/wiki/Almgren%E2%80%93Chriss_model)) | CO patient → plage longue ; CO pressé → accumulation courte et violente (cf. Phase B courte = « urgency », [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)) |

### 2.3 L'inventaire du market maker explique une partie de SC → AR → ST

| Fait établi [D] | Lecture (analogie [I]) |
|---|---|
| Prix de réservation r = s − q·γ·σ²·(T−t) : long d'inventaire, le teneur de marché cote plus bas pour vendre ([Avellaneda & Stoikov](https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf)) | **SC** : les fournisseurs de liquidité absorbent la vente forcée et finissent longs. **AR** : rebond mécanique. **ST** : ils écoulent l'inventaire, leurs cotations plafonnent le rallye et laissent revenir le prix vers la zone du climax, sur volume plus faible |
| Un choc d'inventaire de 100 000 $ crée une pression de prix moyenne de 0,28 %, de demi-vie 0,92 jour (NYSE) ([Hendershott & Menkveld](https://econpapers.repec.org/RePEc:eee:jfinec:v:114:y:2014:i:3:p:405-423)) | Si une vraie demande absorbe cet inventaire au ST (volume faible, tenue au-dessus du SC), le surplomb disparaît : c'est équivalent à « offre épuisée » |
| Une baisse sur fort volume est plus souvent suivie de rendements plus élevés ([Campbell, Grossman & Wang 1993](https://dash.harvard.edu/bitstream/1/3128710/2/campbell_trading.pdf)) ; les rendements des échanges de partage de risque s'inversent, ceux des échanges spéculatifs se prolongent ([Llorente et al. 2002](https://econpapers.repec.org/RePEc:oup:rfinst:v:15:y:2002:i:4:p:1005-1047)) | Climax (liquidité forcée) → retournement (SC → AR). SOS (flux informé) → continuation |

> **À retenir** — Deux lectures du même test peuvent être vraies ensemble : le CO sonde l'offre, et les intermédiaires ramènent leur inventaire à zéro. Le volume départage en partie : un retour **plus calme** que le climax est compatible avec les deux, un retour qui **gonfle** le volume à la baisse n'est compatible avec aucune et signale une offre nouvelle. En perps, les teneurs de marché sont algorithmiques et couverts spot/perp : leurs demi-vies d'inventaire sont probablement bien plus courtes que celles du NYSE [NV]. En H4, un test reflète donc surtout les flux des participants (stops, liquidations, accumulation).

### 2.4 Les cascades de stops d'Osler fournissent la liquidité du spring et de l'upthrust

| Résultat [D] | Chiffres | Source |
|---|---|---|
| Les niveaux de support/résistance publiés arrêtent le cours plus souvent que des niveaux arbitraires | **60,8 % vs 56,2 %** de rebonds, contre 10 000 jeux de niveaux arbitraires ; plus de 70 % des niveaux finissent par 0, 96 % par 0 ou 5 ; pouvoir prédictif d'au moins cinq jours ouvrés | [Osler 2000](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf) |
| Les *take-profit* se groupent **sur** les chiffres ronds (« partially reflecting barriers ») ; les stops **juste au-delà** : stops acheteurs juste au-dessus, stops vendeurs juste en dessous | 9 667 ordres conditionnels d'une grande banque (1999–2000) | [Osler 2003 (SR 125)](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf) |
| Le franchissement d'un amas de stops accélère la tendance, plus fort et plus longtemps qu'après des *take-profit*, par vagues | 0,061 % vs 0,054 % en 15 min ; « Most results are statistically significant for hours, although not for days » | [Osler 2005 (SR 150)](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf) |
| « Running the stops » est une pratique connue ; déclencher les stops de clients a été sanctionné | FCA 2014 : **1 114 918 000 £** d'amendes à cinq banques, notamment pour avoir tenté de « trigger client 'stop loss' orders » | [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf) ; [FCA](https://www.fca.org.uk/news/press-releases/fca-fines-five-banks-%C2%A311-billion-fx-failings-and-announces-industry-wide) |
| Le *predatory trading* exploite le besoin des autres de réduire leurs positions et fait **dépasser** les prix | — | [Brunnermeier & Pedersen 2005](https://www.princeton.edu/~markus/research/papers/predatory_trading.htm) |
| Les prix du BTC se groupent sur les chiffres ronds | plus de 10 % des prix finissent par 00 | [Urquhart 2017](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html) |

**Spring, pas à pas [I]** : ① le prix perce le 🟦 plancher ; ② les stops vendeurs juste en dessous partent en vagues d'ordres au marché (offre urgente) ; ③ le CO les absorbe avec des ordres d'achat passifs et obtient de la taille sans faire monter le prix ; ④ la clôture revient dans la plage (fort volume, longue mèche basse, CLV haut) ; ⑤ le carburant de stops est **consommé**. **Le test** revient ensuite sur la même zone : si aucune cascade ne repart (volume et spread faibles), l'offre est épuisée. Si une cascade repart (volume et spread qui s'élargissent à la baisse, clôtures faibles), la poche de stops ou l'offre réelle n'était pas vide, et le spring était une cassure. Les « vagues » d'Osler expliquent qu'un seul *flush* ne vide pas toujours un niveau.

> **Piège** — Les mêmes travaux mesurent des effets **modestes** (≈ 4–5 points de pourcentage, des heures plutôt que des jours). Plus un niveau est évident (testé souvent), plus les stops s'y accumulent juste au-delà, et plus la cascade est forte s'il finit par céder. « Les tests multiples renforcent un niveau » et « les niveaux évidents se font chasser » sont vrais en même temps.

### 2.5 En perps, les liquidations sont des stops sans discrétion

| Fait [D] | Implication pour les tests [I] |
|---|---|
| Une liquidation est un ordre au marché forcé ; le flux Binance ne pousse qu'une liquidation par symbole et par seconde ([Binance](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams)) | Les springs/UTAD peuvent dépasser plus loin qu'au comptant ; les volumes de liquidations lus sont des **planchers** |
| 10 octobre 2025 : plus grosse journée de liquidations recensée, ≈ **19,16 Md$** selon le classement CoinGlass ([KuCoin/CoinGlass](https://www.kucoin.com/blog/top-10-largest-crypto-liquidation-events-of-all-time)) ; le *mark price* utilisé pour liquider a sous-réagi par rapport au comptant et aux futures, créant une boucle (Lim, SSRN, [NV] : extrait, page 403) ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278)) | La mécanique des plateformes peut fabriquer une « profondeur de spring » artificielle : ne pas lire la profondeur seule |
| « high crypto carry predicts future price crashes » ; une hausse de 10 % du carry standardisé prédit +22 % de liquidations vendeuses rapportées à l'OI le mois suivant ([BIS WP 1087](https://www.bis.org/publ/work1087.htm) ; [VoxEU](https://cepr.org/voxeu/columns/crypto-carry-market-segmentation-and-price-distortions-digital-asset-markets)) | Funding/carry extrême + OI↑ au SOS = état « longs encombrés » à risque de *flush* |
| Avant sept cascades BTC (2022–2025), seule régularité : « a compression of taker order-flow variance », précurseur « population-level … not a per-event alarm » (prépublication) ([Garcia Seuma 2026](https://arxiv.org/abs/2607.27070)) | Les contractions calmes qui précèdent les tests violents sont réelles en moyenne, mais ce n'est pas un signal d'entrée |
| En 2019, le *wash trading* dépassait 70 % du volume déclaré sur les plateformes non régulées ([Cong et al.](https://nber.org/papers/w30783)) | **Hygiène de venue** : lire le volume sur des marchés crédibles (Binance via Coinalyze par défaut dans le projet) |
| Positions publiques sur Hyperliquid : appels publics à liquider une baleine, mars 2025 (presse, non académique) ([Cointelegraph](https://cointelegraph.com/news/traders-targeting-hyperliquid-whales-significant-positions-trigger-liquidations-10x-research)) | La chasse aux liquidations existe, mais elle est documentée par la presse, pas par la recherche |

### 2.6 Le CO teste parce qu'un markup raté coûte deux fois

| Motif du test | Coût évité | Information obtenue | Risque couvert |
|---|---|---|---|
| Vérifier l'offre résiduelle avant le markup | acheter contre son propre impact ([Tóth](https://arxiv.org/pdf/1105.1694), [Farmer](https://arxiv.org/abs/1102.5457)) | quantité d'offre restante à la zone testée | stock payé trop cher puis campagne à reconstruire plus bas |
| Mesurer la demande qui suivra | marquer seul (« he would there have to play a lone hand », [TR §10](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)) | capacité du public à prendre le relais | markup sans acheteurs pour la distribution future |
| Récolter de la liquidité bon marché | aucun : il **achète** les stops et les ventes paniques ([Wyckoff, §21M](https://archive.org/details/WyckoffMethodOfTapeReading) ; [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)) | profondeur de l'offre forcée | cassure réelle si personne n'absorbe |
| Confirmer la polarité après le saut | rachat d'une sortie ratée | l'ancienne résistance tient-elle ? | upthrust déguisé en SOS |

> **Penser comme le CO** — Le *springboard* de Wyckoff est le **résultat** de tests réussis, pas un test : la position est « on the springboard » quand l'opérateur « has completed his original line and is ready to let the stock advance … because he has mopped up all the floating supply at that level ». Wyckoff le situe **au bas de la plage**, pas à la cassure : « I claim that the beginning of the springboard move is at the bottom of a range of accumulation » ([Cours §14M pp.3–5](https://archive.org/details/WyckoffMethodOfTapeReading)).

### 2.7 Les pools d'avant 1934 sondaient ; aujourd'hui, seule la tromperie est interdite

| Pratique historique (source) | Statut aujourd'hui | Ce qui reste lisible sur un graphe |
|---|---|---|
| Achat ou vente-sonde de 5 000–25 000 actions ([Cours §8M](https://archive.org/details/WyckoffMethodOfTapeReading)) ; *testing order* de Livermore ([Lefèvre ch. VII](https://www.gutenberg.org/ebooks/60979)) | Un ordre réel qui fait bouger le prix n'est pas, en soi, une manipulation ; l'interdit porte sur l'intention de tromper (§9(a)(2) : transactions « for the purpose of inducing the purchase or sale of such security by others ») ([15 U.S.C. §78i](https://www.law.cornell.edu/uscode/text/15/78i)). Ce n'est pas un avis juridique | La réponse prix/volume à un mouvement initié par un gros ordre |
| Ordres de soutien affichés puis annulés : « he cancels all of his buying orders » ([Cours §9M p.5](https://archive.org/details/WyckoffMethodOfTapeReading)) | *Spoofing* interdit (« bidding or offering with the intent to cancel », [7 U.S.C. §6c](https://www.law.cornell.edu/uscode/text/7/6c)) ; JPMorgan, métaux précieux 2008–2016 : **920 M$** ([CFTC 8260-20](https://cftc.gov/PressRoom/PressReleases/8260-20)) ; [MiCA art. 91](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-91-prohibition-market-manipulation), applicable depuis le 30/12/2024 | La **profondeur affichée** peut mentir, le **volume exécuté** ne s'annule pas : c'est l'argument de fond pour « volume d'abord » (or COMEX compris) |
| *Wash sales*, ordres appariés | Interdits (§9(a)(1)) ; crypto : opération *Token Mirrors* (oct. 2024), premières poursuites pénales de teneurs de marché pour *wash trading* ([DOJ](https://www.justice.gov/usao-ma/pr/eighteen-individuals-and-entities-charged-international-operation-targeting-widespread)) | Volume gonflé sur les petites plateformes → éviter d'y lire des tests |
| Raids pour faire paraître la liquidation ([Cours §9M](https://archive.org/details/WyckoffMethodOfTapeReading)) | Interdits s'ils visent à induire autrui (§9(a)(2)) | Aujourd'hui, les **flux forcés** (stops, liquidations) jouent ce rôle sans chef d'orchestre |

Wyckoff meurt le 7 mars 1934. Le *Securities Exchange Act* est promulgué le 6 juin 1934 (§9, 48 Stat. 889) ([LII](https://www.law.cornell.edu/uscode/text/15/78i) ; [Wikipedia](https://en.wikipedia.org/wiki/Richard_Wyckoff)). L'édition 1937 du cours ajoute que même si les pools sont « banned by law », toute opération assez concertée et mieux informée que le public produit « the same effects as pure manipulation » ([Cours §9M p.2, note](https://archive.org/details/WyckoffMethodOfTapeReading)). La recherche tempère le mythe : sur 55 pools de la liste sénatoriale de 1929, « the evidence suggests informed trading rather than manipulation » ([Jiang, Mahoney & Mei](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf) ; [Mahoney 1999](https://ideas.repec.org/a/eee/jfinec/v51y1999i3p343-369.html)).

> **À retenir** — Définition honnête du CO moderne [I] : la somme ① des métaordres informés exécutés par algorithme, ② des fournisseurs de liquidité qui gèrent un inventaire, ③ des anticipateurs d'ordres et HFT, et ④ des flux mécaniques forcés (stops, liquidations). Le Composite Man est une heuristique pour lire leur empreinte **nette**, pas une thèse de complot.

### 2.8 Aucune étude ne valide la méthode entière ; ses briques le sont, modestement

| Brique | Résultat [D] | Source |
|---|---|---|
| Wyckoff comme système | aucun test à comité de lecture trouvé ; le plus proche utilise des régimes « loosely modeled » sur Wyckoff | [arXiv 1812.02527](https://arxiv.org/abs/1812.02527) |
| Supports/résistances = profondeur réelle | ils coïncident avec des pics de profondeur du carnet | [Kavajecz & Odders-White 2004](https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html) |
| Tests répétés | la probabilité de rebond croît avec le nombre de rebonds antérieurs (45–90 s), pas à 180 s ; non rentable après coûts | [Garzarelli et al. 2014](https://ar5iv.labs.arxiv.org/html/1110.5197) |
| Rentabilité des S/R | pas d'excès de rendement face au *buy-and-hold* | [Zapranis & Tsinaslanidis 2012](https://econpapers.repec.org/RePEc:taf:apfiec:v:22:y:2012:i:19:p:1571-1585) |
| Snooping | « the dangers of data snooping are immense » | [Sullivan, Timmermann & White](https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf) |
| Spring seul (backtest amateur) | 41,26 % de gains, −0,13 R en moyenne, n = 1 098 (journalier, stop = low − 1 ATR, objectif 2R) | [PR GitHub papan-saham](https://github.com/augustgerry/papan-saham/pull/89) [NV : page 404] |

> **Penser comme le CO** — Pour un trader H1/H4, un test est une **inclinaison de probabilité plus un point de risque défini** : le stop se place sous le low du spring, là où la poche de stops a déjà été consommée. Le backtester du dépôt (`screener/optimize.py`, IS/OOS et walk-forward) est l'outil pour vérifier sur BTC si « spring + test sec + profil d'OI coin » bat des niveaux arbitraires. Le bootstrap de niveaux arbitraires d'Osler est un bon gabarit de contrôle.

## 3. Fiches de tests — accumulation : chaque transition de phase est gardée par un test

Chaque fiche suit le même ordre : labels selon les sources · question du CO · enjeu · lieu et moment · signature valide · ce que fait le CO selon le résultat · vérification pratique (cases à cocher, **[D]** doctrine / **[H]** heuristique) · overlay crypto (volume → OI coin → tierces) · invalidation · implication de trading · erreurs fréquentes · sources.

<!-- FIG:schema_accumulation -->

| Phase | Test | Ce qui est testé | Volume de référence | Fiche |
|---|---|---|---|---|
| A | 🔵 ST (après le 🟢 SC ; l'🔵 AR sert de contexte) | l'offre résiduelle au prix de la panique | < SC | 3.1 |
| B | 🔵 ST in Phase B (tests répétés de la borne basse) | l'offre flottante encore en mains faibles | < passage précédent (gradient) | 3.2 |
| B | 🟠 UA / UT in B (borne haute) | l'offre au-dessus de l'AR, la réaction de la demande | re-entrée rapide | 3.3 |
| B | 🔴 ST as SOW (creux plus bas) | l'agressivité vendeuse, l'absence d'acheteurs | (volumique = offre) | 3.4 |
| C | 🟣 Spring #3 | l'offre sous le support : absente ? | ≤ creux récents | 3.5 |
| C | 🟣 Spring #2 | l'offre sous le support : présente, pas écrasante | en expansion | 3.6 |
| C | 🟣 Spring #1 / terminal shakeout | l'offre écrasante est-elle absorbée ? | climactique | 3.7 |
| C | 🟣 Test du spring | l'offre restante après le spring | < spring | 3.8 |
| C | 🟣 LPS de Phase C (schéma #2, sans spring) | l'offre sur un creux plus haut | < ST précédents | 3.9 |
| D | 🟢 SOS mineur (dans la plage) | la demande progresse-t-elle quand le CO cesse de plafonner ? | > réactions | 3.10 |
| D | 🔵 LPS successifs (dans la plage) | les acheteurs reviennent-ils plus haut ? | < SOS précédent | 3.11 |
| D | 🟢 JAC / SOS majeur | la demande franchit-elle le creek ? | expansion | 3.12 |
| D→E | 🔵 BU / BUEC | la résistance est-elle devenue support ? | < JAC | 3.13 |
| E | 🔵 Test de continuation (*test in a rising market*) | l'offre est-elle revenue après une poussée ? | faible | 3.14 |
| E | 🔵 Réaccumulation (*stepping stone*) | prises de bénéfices absorbées ou distribution ? | décroissant | 3.15 |

### Phase A — stopper la baisse et poser les bornes

**Contexte : l'🔵 AR.** Après le 🟢 SC, le rebond réflexe fixe la borne haute : « The high of this rally will help define the upper boundary of an accumulation TR » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). Côté distribution, Fraser le décrit « sudden, brief and over quickly » ([Fraser, Distribution Definitions (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-distribution-definitions/)). Wyckoff parle de *technical rally* ([Cours §7M](https://archive.org/details/WyckoffMethodOfTapeReading)). Overlay du projet : un AR authentique est du short covering, donc OI coin ↓ (`window.py` refuse l'AR si l'OI monte) [I].

#### 3.1 🔵 ST — Secondary Test (Phase A)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Wyckoff : *secondary reaction* (le terme « secondary test » n'apparaît pas dans le cours) · StockCharts/WA, Pruden, Fraser, Villahermosa : **ST** · Fraser : « Phase A is fulfilled with a test of the SCLX and is labeled ST » |
| Question posée par le CO | « Reste-t-il une offre significative au prix où le public a paniqué ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO a absorbé le climax à bon prix ; si l'offre ressort lourdement, il doit en absorber davantage. **Information** : l'offre résiduelle au niveau du SC. **Risque** : un SC qui n'arrête rien met le stock du CO sous l'eau |
| Lieu et moment | Après l'AR, retour « in the area of the SC » ; aucune source ne chiffre la distance ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). Les ST multiples sont courants. Le ST clôt la Phase A : low du SC, low du ST et high de l'AR posent les bornes |
| Signature valide | **Volume** : « significantly diminished » face au SC [D] ; priorité de Villahermosa : « the decrease in volume and the narrowing of ranges » [D] ; vs moyenne `vol_ratio ≤ 0.85` [H]. Avec un SC à ×2,0 et un ST à ×0,85, le ST pèse ≤ 42 % du SC [H] (la FAQ du site Villahermosa dit « 40-60% of SC », non doctrinal). **Spread** : plus étroit que celui du SC [D] ; `spread_atr ≤ 0.7` [H] (attention : l'ATR est gonflé par le climax). **Clôture** : non spécifiée par les sources ; `clv ≥ 0.5` [H]. **Creux** : « generally stopping at or above » le low du SC [D]. **Durée** : non chiffrée |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : la plage est posée, le CO démarre l'absorption de Phase B. Wyckoff : si les prix « hold around or above the climax lows while volume at the same time shrinks appreciably, we have an indication that liquidation was completed » ([§7M p.2](https://archive.org/details/WyckoffMethodOfTapeReading)). **Raté** (volume lourd, spread large, clôture basse) : « one can anticipate either new lows or prolonged consolidation » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) ; Fraser (cas ALB) ne compte alors la cause qu'à partir du ST ([Fraser, Segmenting PnF Counts (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-05-segmenting-pnf-counts/)). **Ambigu** (léger sous-percement sur volume faible) : Villahermosa y lit un déséquilibre vendeur, Fraser l'accepte ; on garde les deux lectures |

**Vérification pratique**

- [ ] **[D]** Un arrêt identifiable en amont : SC (volume et spread climactiques, clôture loin du bas) ou, à défaut, une Phase A non climactique (admise par WA et Pruden). Sans arrêt, pas de « ST ».
- [ ] **[D]** L'AR a posé la borne haute avant le retour.
- [ ] **[D]** Volume du ST < volume du SC, spread du ST < spread du SC.
- [ ] **[H]** `vol_ratio ≤ 0.85` ; afficher aussi le ratio vol_ST / vol_SC.
- [ ] **[H]** `spread_atr ≤ 0.7`, en se méfiant de l'ATR gonflé juste après le climax.
- [ ] **[D]** Creux ≥ low du SC. Un sous-percement léger se note « ST sous SC », jamais « spring » (le spring suppose un support « established in Phases A and B »).
- [ ] **[H]** `clv ≥ 0.5`.
- [ ] **[D]** Contexte HTF déclaré : dans un downtrend, la plage reste une redistribution par défaut.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume nettement inférieur au SC, spread rétréci. ② OI coin plat ou ↓ : des positions se ferment, pas de nouveaux shorts agressifs [I]. OI coin ↑ pendant que le prix tient : ambigu (shorts qui s'ouvrent, ou acheteurs passifs qui absorbent). ③ Seulement dans ce cas : ratio L/S ↓ (des shorts entrent), funding ≤ 0 (shorts encombrés), liquidations ≈ 0 (mouvement ordonné). **Synthèse** : OI↑ + L/S↓ + funding négatif + liquidations nulles au ST = des shorts s'ouvrent dans le support. C'est du carburant si la borne tient, mais le ST n'est validé qu'après la réponse |
| Invalidation | Clôture sous le 🟦 low du SC avec volume et spread en expansion : le SC n'a pas stoppé la baisse. On ré-étiquette, et le décompte P&F ne part plus du SC |
| Implication de trading | **Pas d'entrée doctrinale** : « Phase A will not be operationally useful for seeking new trades » ([Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)). On trace 🟦 le plancher (low du SC, borne basse de la plage) et 🟦 le plafond (high de l'AR, borne haute), qui serviront d'invalidation et d'objectif plus tard |
| Erreurs fréquentes | Étiqueter un ST sans SC ; présumer l'accumulation (« it may be accumulation, redistribution or nothing », [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) ; appeler « spring » un sous-percement de Phase A ; juger le volume contre la seule MA20 |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Cours 1937 §7M](https://archive.org/details/WyckoffMethodOfTapeReading) · [Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/) · [Fraser, Let's Review (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-wyckoff-power-charting-lets-review) · [Fraser, Action – Test (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test) |

### Phase B — construire la cause en testant les deux bornes

> **Penser comme le CO** — En Phase B, le CO achète en net et plafonne les avances par des ventes : « may sell 100,000 shares and buy 200,000 shares, resulting in a net accumulation of 100,000 shares » ([Pruden, Fraser & Bogomazov, S&C 2014](https://www.wyckoffanalytics.com/wp-content/uploads/2019/08/V32C08822PRUD.pdf)). Chaque retour sur une borne est un relevé d'inventaire du marché. Les premiers retours sont volumiques ; c'est la **pente** du volume d'un test à l'autre qui renseigne, pas un passage isolé.

#### 3.2 🔵 ST in Phase B — tests répétés de la borne basse

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Schémas StockCharts/WA : **« ST in Phase B »**, dessiné *sous* le low du SC sur le schéma #1 (deux lignes de support) · Villahermosa : « ST in B », étiquette neutre tant que la plage n'est pas résolue · Fraser : « Secondary Tests (ST) are drives downward from the Resistance area toward Support » |
| Question posée par le CO | « Combien d'offre flottante reste-t-il en mains faibles sur la borne basse, et diminue-t-elle à chaque passage ? » |
| Enjeu (coût · information · risque) | **Coût** : c'est le centre de coût de la campagne (acheter en net, revendre les rallyes). **Information** : le gradient d'offre. **Risque** : campagne prolongée ou abandonnée (« Large traders give up on the campaign » / « Phase B Extension », [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)) |
| Lieu et moment | Toute la Phase B, sur ou près du support (lows du SC et du ST) ; plusieurs passages |
| Signature valide | **Volume** : au début, « wide and accompanied by high volume » ; puis « the volume on downswings within the TR tends to diminish » [D] ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). Fraser : ces baisses « typically have high volume (evidence of Supply) » [D]. Le signal est la **tendance**. **Spread** : des oscillations qui se resserrent. **Clôture** : des clôtures qui s'éloignent des bas [I]. **Creux** : le sous-percement fait partie du modèle (schéma #1) [D]. **Durée** : la Phase B doit être plus longue que les Phases A et C ([Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)) [D] ; « sometimes a year or more » sur actions ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** (gradient négatif) : « When it appears that supply is likely to have been exhausted, the stock is ready for Phase C » [D] ; traces : creux de plus en plus secs, rallyes plus faciles. **Raté** (volume croissant sur les creux, clôtures basses) : la Phase B s'allonge, ou la campagne est abandonnée (redistribution). **Ambigu** (volume plat) : Fraser ré-étiquette « Phase C and D as a continuation of Phase B » si l'offre revient ([Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/)) |

**Vérification pratique**

- [ ] **[D]** Chaque passage sur la borne basse est relevé : volume, spread, clôture, creux.
- [ ] **[D]** La pente du volume des creux successifs est négative.
- [ ] **[H]** Le **dernier** passage est à `vol_ratio ≤ 0.85` ; les premiers peuvent dépasser ×1.3 sans rien invalider.
- [ ] **[D]** « Activity bullish » : le volume monte sur les rallyes et baisse sur les réactions (test d'achat de 1937, n°2).
- [ ] **[I]** Le ratio vol(dernier test) / vol(SC) baisse d'un passage à l'autre.
- [ ] **[D]** Durée de la Phase B ≥ durée de la Phase A avant de créditer une Phase C.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Gradient de volume des creux. ② OI coin qui se dégonfle de test en test : débouclage, l'offre ne se réengage pas [I]. OI coin ↑ sur un creux plus bas et volumique : de nouveaux shorts pressent (candidat ST as SOW, fiche 3.4). ③ Si le prix cale avec OI↑ : L/S, funding, liquidations. **Synthèse** : OI↓ + liquidations de longs décroissantes à chaque passage = des mains faibles qui s'épuisent |
| Invalidation | Un volume des baisses qui **grossit** avec l'âge de la plage : « In distribution, volume stays heavy on the way down and often grows as the range gets older » ([WA 2026](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)) |
| Implication de trading | Pas de trade au milieu de la plage. Villahermosa : pour trader les extrêmes de Phase B, descendre d'unité de temps et chercher une accumulation mineure au bas, une distribution mineure au haut ([ST](https://tradingwyckoff.com/en/secondary-test/)). Niveau de travail : 🟦 plancher (low du SC/ST, la borne testée) |
| Erreurs fréquentes | Exiger `test_vol` dès le début de la Phase B (le filtre manque les premiers ST) ; appeler « spring » un creux de Phase B (« The Spring must occur after completing Phase B (after several Secondary Tests). A 'premature' Spring, without cause built, fails much more often », [Villahermosa, Spring](https://tradingwyckoff.com/en/spring-shakeout/) [NV : page derrière anti-bot, citation relevée par l'outil]) ; compter la cause P&F depuis un SC sans absorption (« Over-counting a PnF Accumulation range is a common problem », [Fraser, Segmenting PnF Counts (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-05-segmenting-pnf-counts/)) |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/) · [Fraser, Segmenting PnF Counts (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-05-segmenting-pnf-counts/) · [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/) · [S&C 2014](https://www.wyckoffanalytics.com/wp-content/uploads/2019/08/V32C08822PRUD.pdf) |

#### 3.3 🟠 UA / UT in Phase B — test de la borne haute en accumulation

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA : pic **non étiqueté** au-dessus de l'AR sur le schéma ; le texte parle d'« upthrust-type actions at the upper end of the TR » · Villahermosa : **UA** (*Upthrust Action*) en accumulation, **UT** en distribution, « This is the only difference between these labels » ; **mSOS** si le prix reste au-dessus un moment · Fraser : **UT** même en accumulation (cas MU) · cours crypto WA (Rutigliano 2020) : « UA » sur un schéma de réaccumulation BTC |
| Question posée par le CO | « Combien d'offre se trouve au-dessus de l'AR, et comment réagit la demande quand le prix perce ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO plafonne les avances prématurées (« checking advances in price with short sales », [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) pour ne pas payer plus cher. **Information** : l'offre en surplomb et l'appétit des acheteurs de cassure. **Risque** : une sortie qui tient avant la fin de l'absorption l'obligerait à acheter plus haut |
| Lieu et moment | Phase B, au-dessus du 🟦 high de l'AR ; bref |
| Signature valide | **Prix** : « crosses the previous high created in the stopping action but does not move too far before re-entering within the range, leaving a slight shakeout » ([Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/)) [D]. **Volume** : aucun seuil dans les sources ; « moderate volume » dans la FAQ du site (non doctrinal). **Clôture** : barre de réintégration avec `clv ≤ 0.5` [H]. **Durée** : réintégration rapide (UA/UT) vs plusieurs clôtures au-dessus (mSOS) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** (pour l'accumulateur : réintégration rapide, peu d'offre) : l'absorption continue. Villahermosa : un UA « denotes greater strength to buyers and therefore in the zone of structure lows breakout we favor the Spring instead of the bearish breakout » ([Spring](https://tradingwyckoff.com/en/spring-shakeout/) [NV : page protégée, citation relevée par l'outil]). **Raté** (pour l'accumulateur : chute rapide vers un SOW sous l'AR) : « In Phase B the UT is followed by a rapid decline into a SOW. This puts us on alert that the Distribution is progressing in a hurry » ([Fraser, Just Another Phase (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-just-another-phase/)). **Ambigu** : prix qui reste au-dessus quelque temps = mSOS ; l'étiquette reste conditionnelle |

**Vérification pratique**

- [ ] **[D]** Percée du high de l'AR puis réintégration rapide.
- [ ] **[D]** Position dans la séquence : avant tout test de Phase C, une percée est présumée UA/UT, jamais SOS (Pruden : « you should not buy breakouts » ; règle CLAUDE.md n°3).
- [ ] **[H]** Barre de réintégration `clv ≤ 0.5`.
- [ ] **[I]** Nombre de clôtures au-dessus (acceptation) : à partir de plusieurs, candidat mSOS.
- [ ] **[D]** Volume et spread du repli qui suit : un repli large et volumique vers le support favorise la lecture distribution (UT).
- [ ] **[D]** Contexte HTF déclaré.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume et spread de la percée, puis de la réintégration. ② OI coin ↑ sur la percée puis réintégration : des acheteurs de cassure entrent et deviendront vendeurs, ce qui nourrit la descente vers les bas où le CO rachète [I]. OI coin ↓ sur la percée : simple rachat de shorts de plage, sans demande nouvelle. ③ Liquidations de shorts sur la mèche (stops acheteurs) et funding qui grimpe : la percée a été alimentée par du forcé, pas par de la demande durable |
| Invalidation | De la lecture accumulation : UT suivi d'une chute volumique sous l'🔵 AR (SOW en Phase B). De la lecture UA : prix qui tient au-dessus avec un repli sec (passer en scénario mSOS/SOS) |
| Implication de trading | En hypothèse d'accumulation, **ni short** du UA (« traders often get in trouble at the end of Accumulation because they continually sell short the Resistance Line area », [Fraser, Let's Review (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-wyckoff-power-charting-lets-review)), **ni achat** de cassure. On note 🟧 le high du UA (extrême du piège, futur repère de cassure) |
| Erreurs fréquentes | Appeler la percée « SOS » ; la shorter dans un contexte d'accumulation ; oublier que l'étiquette dépend du biais présumé (même action : UA ou UT) |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/) · [Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/) · [Rutigliano, WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) |

#### 3.4 🔴 ST as SOW — creux plus bas en Phase B

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Villahermosa : **ST as SOW** en accumulation, **mSOW** en distribution · schémas StockCharts/WA : « ST in Phase B » sous le SC (accumulation), « SOW in Phase B » (distribution) · étiquette neutre possible : « ST in B » |
| Question posée par le CO | « L'offre est-elle encore agressive, ou les acheteurs ont-ils disparu ? » |
| Enjeu (coût · information · risque) | **Coût** : encore de l'offre à absorber. **Information** : la qualité de la demande sous la plage. **Risque** : la campagne tourne à la redistribution |
| Lieu et moment | Phase B, sous les lows du SC/ST ; « Generally there are more chances of this event appearing when the Secondary Test of Phase A has produced a lower low » ([Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/)) |
| Signature valide | **Prix** : creux plus bas « due to either the aggressiveness of sellers or a lack of interest from buyers » [D]. **Volume/spread** : en expansion avec clôture basse = offre encore présente ; creux plus bas sur volume faible = vendeurs absents (lecture plus favorable) [I]. **Durée** : la zone « will need to be tested in the future » [D] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Lecture accumulation maintenue** : le sous-percement cesse de produire du suivi et se fait re-tester plus sec ; nouvelle ligne de support. **Lecture distribution renforcée** : « it denotes seller strength and in the zone of structure highs breakout we favor the Upthrust instead of the effective bullish breakout » ([Villahermosa, Spring](https://tradingwyckoff.com/en/spring-shakeout/) [NV]). **Ambigu** : on garde « ST in B » jusqu'à la résolution |

**Vérification pratique**

- [ ] **[D]** Creux plus bas que le SC/ST, en Phase B (pas en Phase C).
- [ ] **[D]** Volume, spread et clôture du sous-percement relevés.
- [ ] **[H]** `vol_ratio ≥ 1.3` + `spread_atr ≥ 1.3` + `clv ≤ 0.4` (profil SOW du screener) : offre agressive.
- [ ] **[D]** Le niveau est re-testé plus tard, et l'on compare les volumes.
- [ ] **[D]** Top-down : dans un downtrend, le scénario redistribution prend le dessus.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Creux plus bas, volumique ou non. ② OI coin ↑ avec le creux et le volume : de nouveaux shorts pressent, l'offre est agressive [I]. OI coin ↓ avec liquidations de longs : des longs fragiles sont purgés, ce qui peut préparer une absorption. ③ Si le prix cale : L/S ↓ (shorts qui entrent), funding < 0, liquidations de longs ↑. **Synthèse** : OI↑ + L/S↓ + funding négatif sans rebond = vendeurs en contrôle |
| Invalidation | Du scénario accumulation : suivi baissier sans réintégration, et volume des baisses qui croît. Du scénario distribution : réintégration rapide puis re-test sec qui tient |
| Implication de trading | Aucune entrée sur l'unité de temps de la structure. On redessine 🟦 le nouveau support (low du ST as SOW, borne basse effective) et on prépare les deux scénarios de Phase C : spring (accumulation) ou cassure (redistribution) |
| Erreurs fréquentes | Appeler « spring » un creux de Phase B jeune ; ignorer le scénario redistribution ; confondre l'étiquette (dépendante du biais) avec la preuve |
| Sources | [Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/) · [Villahermosa, Spring](https://tradingwyckoff.com/en/spring-shakeout/) [NV] · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [WA 2026](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/) |

### Phase C — le test ultime de l'offre

> **À retenir** — Numérotation unique dans tout le mémo, conforme au glossaire et au blog SMI, à Fraser et à Villahermosa (aucune inversion trouvée) : **#1 = lourd** (shakeout / terminal shakeout : pénétration profonde, spread large, volume fort ; test obligatoire) · **#2 = modéré** (pénétration modérée, volume en expansion ; test requis, on achète le test) · **#3 = léger** (pénétration faible, spread étroit, volume faible ; pas de test requis). Pruden (2006) suit la même gradation **sans numéros** : volume « very light » → voie libre ; « moderate » → « more testing of support » ; « heavy » → « renewed decline » le plus souvent ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)). Fraser : « The volume signature is the final arbiter of the type of Spring developing and this also determines the strategy for entry » ([Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)).

<!-- FIG:springs_types -->

Origine des mots : Wyckoff définit le *terminal shake-out* (§21M, ©1932). Le glossaire SMI dit que « a spring is a refinement of Mr. Wyckoff's concept of a Terminal Shake-Out and grew out of that concept » ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/)). Villahermosa attribue le terme à Robert G. Evans et le dérive de « Springboard » ([TheTicker n°1, 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)). **Aucune source ne nomme l'inventeur de la numérotation** ; elle est très probablement de l'ère SMI/Evans (après 1934) [I].

#### 3.5 🟣 Spring #3 — pénétration légère et sèche

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | SMI : « No INCREASE in SUPPLY can COME OUT on the DRIVE into NEW LOW GROUND we call this a #3 SPRING » ([glossaire](https://wyckoffsmi.com/wyckoff-glossery/)) · Fraser : « Number 3 Spring » · Villahermosa : « Spring #3 » · Pruden 2006 : « very light (low volume) » sans numéro |
| Question posée par le CO | « Si j'enfonce le support, reste-t-il quelqu'un pour vendre ? » |
| Enjeu (coût · information · risque) | **Coût** : minimal, il y a peu à absorber. **Information** : une absence d'offre sur un nouveau plus-bas est la preuve la plus forte d'épuisement. **Risque** : lire « sec » un marché simplement vide (week-end, séance creuse en crypto 24/7) [I] |
| Lieu et moment | Phase C, **après** une Phase B mûre (plusieurs ST), sous le 🟦 support (low du SC ou plus bas creux de Phase B) |
| Signature valide | **Volume** : « The volume is low, not rising above the recent low levels » ([Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)) [D] : la référence est le volume des **creux récents**. `vol_ratio ≤ 0.85` [H]. **Spread** : « relatively narrow price spread » ([SMI, O'Brien](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/)) [D] ; `spread_atr ≤ 0.7` [H]. **Pénétration** : « shallow » ([Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)) ; `pen_atr ≥ 0.1` ATR [H], et moins de ~0,5 ATR comme repère à calibrer [H]. **Clôture** : la barre ne clôture pas au plus bas ([WA, algorithmes](https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/)) ; réintégration de la plage, `clv ≥ 0.5` [H]. **Durée** : réintégration sur la barre ou très vite |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : barres de demande, retour dans la plage, SOS proche ; le test est facultatif (« #3 Springs do not need to be tested. However, a Secondary Test is not uncommon »). Confirmation : « It is not confirmed until strong demand comes into the market and there is a rally back into the trading range » ([SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/)). **Raté** : pas de demande, nouvelle dérive sous le low. **Ambigu** : réintégration sans barre de demande, à traiter comme un #2 (attendre un test) |

**Vérification pratique**

- [ ] **[D]** La Phase B est mûre (plusieurs ST, gradient de volume négatif) : sinon, spring « prématuré ».
- [ ] **[D]** Le volume sur la pénétration ne dépasse pas celui des creux récents.
- [ ] **[H]** `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `pen_atr ≥ 0.1` ATR.
- [ ] **[D]** Clôture revenue dans la plage, pas au plus bas de la barre ; `clv ≥ 0.5` **[H]**.
- [ ] **[D]** Barres de demande ou rallye de réintégration dans les barres suivantes.
- [ ] **[I]** Le volume « sec » n'est pas un artefact d'heure creuse : comparer au même créneau des jours précédents.
- [ ] **[D]** Contexte : « Always beware of springs in a downtrend » ([SMI, Short Term Trader](https://wyckoffsmi.com/springs-shakeouts-and-the-short-term-trader/)).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume sec, spread étroit. ② OI coin quasi inchangé : ni purge de longs, ni nouveaux shorts [I]. ③ Tierces rarement nécessaires : liquidations ≈ 0, funding neutre. Si l'OI monte sur la percée (shorts de cassure) puis que le prix réintègre, ces shorts piégés deviennent du carburant, mais il faut encore la réponse acheteuse |
| Invalidation | Clôture sous le 🟪 low du spring avec spread et volume en hausse. SMI (cas « Another Failed Spring ») : « reacted on increased price spread and volume. This negated the two testing scenarios » ([SMI, Another Failed Spring](https://wyckoffsmi.com/another-failed-spring/)) |
| Implication de trading | **Entrée** : sur la réintégration ou sur les premières barres de demande (« Buy the Spring or any of the demand bars that follow », [Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)). **Stop** : sous 🟪 le low du spring (là où la poche de stops a été consommée ; « Place stops under the low of the Spring day »). Marge sous le low pour un second balayage, selon Villahermosa ([site](https://tradingwyckoff.com/en/smart-money-concepts/), [NV]). **Objectif** : 🟦 le high de l'AR / le creek (borne haute de la plage), puis le décompte P&F depuis le LPS (« A spring may also serve as the LPS from the perspective of the P&F count », [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)) ; R:R ≥ 3 |
| Erreurs fréquentes | Prendre un marché vide pour une offre épuisée ; acheter un « spring » de Phase B ; acheter sans réponse de la demande ; acheter un spring dans un downtrend sans test ni SOS |
| Sources | [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/) · [SMI, Testing the Spring](https://wyckoffsmi.com/testing-the-spring/) · [Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends) · [Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action) · [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf) |

#### 3.6 🟣 Spring #2 — pénétration modérée, offre absorbée

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | SMI : « SUPPLY is not absent, it is NOT OVERWHELMINGLY ABUNDANT » ; « The #2 Spring is the most common » · Fraser : « Spring #2 » · Villahermosa : « Spring #2 » · Pruden 2006 : « Moderate volume here may mean more testing of support and to proceed with caution » |
| Question posée par le CO | « Combien d'offre libère la cassure, et ai-je pu tout absorber ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO achète un bloc d'offre (stops et vendeurs tardifs), une liquidité bon marché ([Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)). **Information** : de l'offre est apparue, la mesure est incomplète. **Risque** : absorbée ne veut pas dire épuisée |
| Lieu et moment | Phase C, sous le 🟦 support, après une Phase B mûre |
| Signature valide | **Volume** : en expansion (« Note the big surge of volume on the break of Support. This is a Spring #2 which must be tested », [Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)) [D] ; `0.85 < vol_ratio < 2.0` [H]. **Spread** : « good price spread » ([SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/)) [D]. **Pénétration** : modérée, « goes further below the low on expanded volume » ([Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)) [D]. **Clôture** : retour dans la plage, `clv ≥ 0.5` [H]. **Durée** : test souvent dans les 1–2 barres suivantes en journalier (« it is in the two days immediately following the Spring », [Fraser, Best Trade Entry Points (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/)) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : un test à volume nettement plus faible et creux plus haut, puis demande (fiche 3.8). **Raté** : test à creux plus bas sur volume plus fort, le processus recommence (« the process must be repeated and the Wyckoff Wave must find support above point G », [SMI, Testing the Spring](https://wyckoffsmi.com/testing-the-spring/)). **Ambigu** : rallye sans test, le test peut venir plus tard (« Sé muy precavido si no se ha producido el proceso de testeo », [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)) |

**Vérification pratique**

- [ ] **[D]** Phase B mûre, cassure du support suivie d'une réintégration.
- [ ] **[D]** Volume de la pénétration supérieur aux creux récents (de l'offre est sortie).
- [ ] **[H]** `0.85 < vol_ratio < 2.0` ; `pen_atr ≥ 0.1` ATR.
- [ ] **[H]** Barre de réintégration `clv ≥ 0.5`.
- [ ] **[D]** Statut « spring possible » tant que le test n'a pas eu lieu.
- [ ] **[D]** Test attendu : volume < spring, creux ≥ low du spring.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Expansion de volume puis réintégration. ② Deux profils compatibles [I] : OI coin ↓ avec liquidations de longs (purge de longs fragiles, stops consommés), ou OI coin ↑ sur la cassure puis réintégration (shorts de cassure piégés, futur carburant). ③ Funding qui plonge vers ou sous zéro, liquidations de longs (planchers, flux limité à une par seconde). **Synthèse** : OI↓ + liquidations de longs + réintégration = l'offre forcée a changé de mains |
| Invalidation | Clôture sous le 🟪 low du spring avec volume en hausse. Test à creux plus bas **et** volume plus fort : « these tests should not be traded » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) |
| Implication de trading | **Ne pas acheter la barre**, ou seulement une partie : « take only a partial position on the spring and then adding a second partial position on the test » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)). **Entrée** : sur le test (« The test of the Spring #2 is the best buy point », [Fraser, Skill Building (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-skill-building)). **Stop** : sous 🟪 le low le plus bas (low du spring, invalidation du schéma). **Objectif** : 🟦 le creek / high de l'AR, puis le décompte P&F ; R:R ≥ 3 |
| Erreurs fréquentes | Acheter la barre de spring en taille pleine ; confondre absorption et épuisement ; juger le test contre la MA20 au lieu du volume du spring |
| Sources | [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/) · [SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/) · [Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action) · [Fraser, Skill Building (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-skill-building) · [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf) |

#### 3.7 🟣 Spring #1 / terminal shakeout (et shakeout ordinaire)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | **Wyckoff** (§21M, ©1932) : « A Terminal Shake-out is a rapid or precipitous downward movement, occurring at or near the end of a period of preparation for an advance » ; le *shake-out* ordinaire est le même geste « at other points in the price movement as, for instance, an exaggerated selling climax » · SMI/O'Brien : « The #1 Spring is a shakeout » · Villahermosa : « Spring #1 o Terminal Shakeout » · WA : « like a spring on steroids » · glossaire SMI : le spring diffère du terminal shake-out par « how far it penetrates into new low ground » · Fraser : « The Number 1 Spring is actually a Shakeout that is a complete breakdown » |
| Question posée par le CO | « Ai-je absorbé toute l'offre que la panique et les stops viennent de libérer ? La chute était-elle terminale ? » |
| Enjeu (coût · information · risque) | **Coût** : le plus gros bloc, au meilleur prix, mais un stock important d'un coup. **Information** : offre écrasante, épuisement incertain. **Risque** : c'est une vraie cassure. « Initially, a shakeout or #1 spring is quite similar to a Sign of Weakness (fall through the ice) » ([SMI, Short Term Trader](https://wyckoffsmi.com/springs-shakeouts-and-the-short-term-trader/)) |
| Lieu et moment | Terminal shakeout : fin de longue préparation, sous le 🟦 support. Shakeout ordinaire : « a sharp DOWNWARD THRUST occurring in an UPWARD TREND without extensive previous preparation » ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/)), donc en réaccumulation ; « la principal diferencia, la localización » ([Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)) |
| Signature valide | **Volume** : fort à climactique (« Aparece fuertemente la oferta », Villahermosa) [D] ; `vol_ratio ≥ 2.0` [H]. **Spread** : en expansion [D] ; `spread_atr ≥ 1.3` [H]. **Pénétration** : profonde [D] ; plus de ~1 ATR comme repère à calibrer [H]. **Clôture / reprise** : réintégration rapide ; premier indice de demande : « tras la penetración, el volumen permanece alto pero los rangos del precio comienzan a disminuir » ([Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)) [D]. **Durée** : le test peut venir tard ; SMI : « The reaction took 18 days. The rally only 12 » ([SMI, Test of the Shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/)) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : « debe producirse una fuerte entrada de demanda que impulse al precio de nuevo al alza con unos rangos del precio amplios y un volumen relativamente alto », puis un ou plusieurs tests secs. **Raté** : pas de réintégration, c'est un SOW ; « tendrá que construir una nueva área de acumulación » ([Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)). **Ambigu** (réponse explosive sans retour sur le low) : le CO teste plus tard, sur un repli vers la zone reconquise [I : extension projet ; SMI documente seulement un test tardif après un rallye réactif] |

**Vérification pratique**

- [ ] **[D]** Fin de longue préparation (terminal) ou tendance haussière (ordinaire) : sinon, présumer un SOW.
- [ ] **[H]** `vol_ratio ≥ 2.0`, `spread_atr ≥ 1.3`, pénétration profonde.
- [ ] **[D]** Réintégration rapide de la plage ; sans elle, ce n'est pas un shakeout.
- [ ] **[D]** Statut « possible » jusqu'au test. « all shakeouts (#1 Springs) need to be tested » ([SMI, Test of the Shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/)).
- [ ] **[D]** Test(s) : volume décroissant, creux plus haut ; plusieurs tests possibles.
- [ ] **[D]** Top-down : « it is extremely dangerous to take positions on springs or shakeout in a downtrend » ([SMI, Test of the Shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/)).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume climactique, spread large, longue mèche. ② OI coin en forte baisse avec pic de liquidations de longs (flux forcé consommé), ou OI ↑ sur la cassure (shorts de cassure) puis réintégration avec liquidations de shorts (squeeze) [I]. ③ Funding ≤ 0, liquidations à lire comme des planchers. Le *mark price* peut sous-réagir et fabriquer de la profondeur (octobre 2025, [Lim](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278) [NV]). **Synthèse** : OI↓ + liquidations de longs massives + réintégration rapide + funding négatif = purge terminale probable, à confirmer par le test |
| Invalidation | Pas de réintégration ; clôture sous le 🟪 low du shakeout ; test ultérieur à creux plus bas sur volume plus fort |
| Implication de trading | **Divergence des sources** : SMI, n'entrer qu'après un test réussi (« I would much rather see a successful secondary test before entering the market to the upside », [SMI, Short Term Trader](https://wyckoffsmi.com/springs-shakeouts-and-the-short-term-trader/)) ; Fraser, « It should not be bought » ([Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)) ; Pruden, le shakeout (point 8) est « our first prescribed place to initiate a long position », le test (point 10) « is better » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)). **Choix du mémo** : entrée sur le test réussi seulement. **Stop** : sous 🟪 le low du shakeout (le « danger point » de Pruden), ce qui donne un stop large, donc une taille réduite. **Objectif** : décompte P&F ; si le R:R ≥ 3 est impossible, on passe |
| Erreurs fréquentes | Acheter le *flush* dans un downtrend ; confondre shakeout et SOW ; sauter le test ; confondre SC et shakeout (« A true selling climax looks the same as this shake-out does; the big difference is that on a selling climax you will have a Bear Market behind you », [MTM p.96](https://www.tradeguider.com/mtm_251058.pdf)) |
| Sources | [Cours 1937 §21M](https://archive.org/details/WyckoffMethodOfTapeReading) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/) · [SMI, shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/) · [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf) · [Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) |

> **Penser comme le CO** — Wyckoff décrit le but du terminal shake-out sans détour : « to scare holders of stock into selling out; to catch stops which may have been placed on long positions below the previous line of supports … and to encourage short selling around the bottom » ; puis « the strings are pulled to lock in these shorts and to shut out the sold out bulls ». Il ajoute : « It makes no practical difference whether a shake-out is due to manipulation or panicky selling on the part of distressed longs » ([Cours §21M p.1, ©1932](https://archive.org/details/WyckoffMethodOfTapeReading)).

#### 3.8 🟣 Test du spring (test secondaire du spring ou du shakeout)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | SMI : « Secondary Test » du spring · StockCharts/WA : « Test » (schéma #1) · Pruden : « secondary test at point 10 » · Villahermosa : le test du spring **est** un LPS (« LPS tras sacudida », [LPS ES](https://tradingwyckoff.com/last-point-of-support/)) · VSA : « test » après un *shake-out* (indicateur TG « Basic Test ») |
| Question posée par le CO | « L'offre délogée par le spring a-t-elle vraiment disparu ? » |
| Enjeu (coût · information · risque) | **Coût** : nul si le test réussit. **Information** : la dernière mesure avant le markup. **Risque** : marquer au-dessus d'une offre résiduelle non mesurée |
| Lieu et moment | Après le spring, retour vers la zone de son low : 1–2 barres pour un #2 en journalier (Fraser), plusieurs semaines pour un shakeout (SMI) |
| Signature valide | **Volume** : < volume du spring, c'est le critère primaire (« an even lower-volume test of that spring », [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)) [D] ; `vol_ratio ≤ 0.85` [H]. **Spread** : plus étroit que celui du spring (« narrowing price spreads », [SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) [D] ; `spread_atr ≤ 0.7` [H]. **Creux** : « A high quality test will put in a higher bottom than was recorded on the spring » [D]. **Clôture** : `clv ≥ 0.5` [H]. **Réponse** : hausse dans 1–3 barres (Williams) [D] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : « A successful Secondary Test is the final action that confirms a Spring was successful » ([SMI, Testing the Spring](https://wyckoffsmi.com/testing-the-spring/)) ; le CO lance le markup, un SOS suit vite. **Raté** : « A poor quality Secondary Test means the stock or index reacted below the Spring before demand came into the market », le processus recommence. **Ambigu** : on attend un second test ; TradeGuider : « Give extra weight to a second test in a bullish phase if the second test has lower volume than the first » ([Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)) |

Barème de qualité (synthèse SMI + Fraser + Villahermosa + WA) :

| Grade | Creux | Volume | Spread | Lecture | Action |
|---|---|---|---|---|---|
| **A** | plus haut que le spring | < spring | étroit | test réussi | achetable après la réponse |
| **B** | léger sous-percement | < spring | étroit | « lower quality » mais « not all lower quality tests fail » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) | attendre un creux plus haut ou un nouveau test |
| **C** | tenu | ≥ spring et/ou spread large | large | qualité moindre (« The widespread suggests the Secondary Test may not be completed », [SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/)) | attendre le re-test |
| **D** | plus bas | > spring | — | « these tests should not be traded » | ressort raté probable |

**Vérification pratique**

- [ ] **[D]** Un spring identifié en amont (sa cause), avec son type (#1/#2).
- [ ] **[D]** Volume du test < volume du spring.
- [ ] **[H]** `vol_ratio ≤ 0.85` et `spread_atr ≤ 0.7`.
- [ ] **[D]** Creux ≥ low du spring (grade A) ; sinon grade B, C ou D.
- [ ] **[H]** `clv ≥ 0.5`.
- [ ] **[D]** Réponse haussière dans 1–3 barres. Sans réponse, *negative action*.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume sous celui du spring, spread étroit, creux plus haut. ② OI coin plat ou en légère baisse : pas de nouveaux shorts agressifs [I]. ③ Si l'OI monte : ratio L/S ↓ (shorts qui entrent), funding neutre à négatif, liquidations ≈ 0. **Synthèse** : OI↑ + L/S↓ + flux vendeur lourd sur le test = des vendeurs se construisent, le test peut échouer ; OI plat + liquidations nulles + creux plus haut = offre épuisée |
| Invalidation | Clôture sous le 🟪 low du spring ; test à creux plus bas sur volume plus fort (grade D) |
| Implication de trading | **Entrée** : sur la barre de demande qui suit le test, ou par ordre stop au-dessus du high de la barre de test (« placing an order above the test lets the market come to you », [TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)). **Stop** : sous 🟪 le low du spring (le « specific low risk stop or danger point at point 8 » de Pruden). **Objectif** : 🟦 le creek / high de l'AR, puis le décompte P&F depuis le LPS ; R:R ≥ 3 |
| Erreurs fréquentes | Accepter un test plus volumique que le spring ; acheter un test sans réponse ; juger le volume contre la seule MA20 |
| Sources | [SMI, Testing the Spring](https://wyckoffsmi.com/testing-the-spring/) · [SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/) · [Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action) · [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf) · [MTM](https://www.tradeguider.com/mtm_251058.pdf) |

#### 3.9 🟣 LPS de Phase C — test plus haut, sans spring (schéma #2)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA : « Accumulation Schematic 2 shows a TR without a spring » ; « the testing of supply can occur higher up in the TR without a spring or shakeout » · Fraser : « There are two types of tests; the Spring (or Shakeout) and the Last Point of Support (LPS) » · Villahermosa 2018 : variante « dentro de los límites del rango » · SMI : critères du LPS |
| Question posée par le CO | « Puis-je vérifier l'épuisement de l'offre sans enfoncer le support ? » |
| Enjeu (coût · information · risque) | **Coût** : pas de stops bon marché à ramasser, mais un fond plus fort (« Este evento denota mayor fortaleza de fondo », Villahermosa). **Information** : moins nette qu'un spring. **Risque** : confusion avec un creux de Phase B |
| Lieu et moment | Fin de Phase B / Phase C, creux **plus haut** que le SC et les ST |
| Signature valide | **Volume** : « Volume will diminish on the LPS test as compared to the prior low » ([Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/)) [D] ; `vol_ratio ≤ 0.85` [H]. **Spread** : « RELATIVE NARROWING of the SPREAD and a DECREASE IN THE VOLUME » ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/)) [D]. **Creux** : « An LPS makes a higher low and then turns upward » [D]. **Confirmation** : un SOS qui suit [D] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : SOS puis LPS de Phase D. **Raté** : retour sous les creux précédents, on revient en Phase B (ou on attend un spring). **Ambigu** : sans SOS ensuite, un creux plus haut de Phase B ne se distingue pas d'un LPS de Phase C ; « the identification of Phase C can be challenging » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) |

**Vérification pratique**

- [ ] **[D]** Creux plus haut que le SC et les ST.
- [ ] **[D]** Volume < volume du creux précédent testé.
- [ ] **[H]** `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`.
- [ ] **[D]** Étiquette conditionnelle (« LPS C ? ») jusqu'au SOS.
- [ ] **[D]** Phase B mûre (gradient négatif) en amont.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume sec, spread étroit, creux plus haut. ② OI coin plat ou ↓ [I]. ③ Si OI↑ : L/S, funding, liquidations, comme pour le test du spring |
| Invalidation | Cassure du creux précédent (low du ST de Phase B) sur volume en hausse |
| Implication de trading | **Entrée** : barre de demande au départ du LPS. **Stop** : sous 🟣 le low du LPS C (dernier creux défendu par la demande) ou sous le low précédent (Fraser : « place a stop under the low of the LPS, or under the prior low »). **Objectif** : 🟦 le creek, puis le décompte P&F ; R:R ≥ 3 |
| Erreurs fréquentes | Appeler LPS chaque creux plus haut avant le SOS ; oublier que Pruden préfère le spring, qui « does a better job of cleaning out remaining supply » |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Fraser, Buy Strategies (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/) · [Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) |

### Phase D — la demande prouve qu'elle domine

> **À retenir** — Phase D = « a pattern of advances (SOSs) on widening price spreads and increasing volume, as well as reactions (LPSs) on smaller spreads and diminished volumes » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). Règle de gestion de Pruden : si ce motif n'apparaît pas, « we are advised not to add to our position and look to close our original position » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)). Le SOS est lui-même un **test de la demande** : chez Wyckoff, le CO « bids certain stocks up to new highs in order to encourage this outside buying power » ([TR §10 p.3](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)).

#### 3.10 🟢 SOS mineur — progression dans la plage

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Villahermosa : « minor Sign Of Strength (mSOS) » quand la hausse « fails to break the structure » · Fraser : « Minor Sign of Strength since it could not reach the Resistance line » ; SOS « positionnel » : « price attempting to breach overhead resistance by temporarily rising above a prior peak » · StockCharts/WA : SOS générique, « a price advance on increasing spread and relatively higher volume » · Pruden : JAC d'un **creek mineur** |
| Question posée par le CO | « Quand je cesse de plafonner les rallyes, la demande suit-elle ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO commence à lever des offres. **Information** : la qualité de la demande. **Risque** : un sommet sans suite qui retombe vers le support |
| Lieu et moment | Après le test de Phase C (spring/test ou LPS C), à l'intérieur de la plage, sous le creek majeur |
| Signature valide | **Volume** : en hausse par rapport aux réactions [D] ; `vol_ratio ≥ 1.3` [H]. **Spread** : large [D] ; `spread_atr ≥ 1.3` [H]. **Clôture** : haute [D] ; `clv ≥ 0.6` (seuil du code) [H]. **Position** : sous la résistance majeure. **Durée** : une vague, pas une barre isolée |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : réaction sèche vers un LPS plus haut (fiche 3.11). **Raté** : réaction large et volumique jusqu'au support ; Fraser : « After the SOS, the price will typically fall back into the Accumulation area and attempt to return to support » ; s'il y a de l'offre, ré-étiquetage en Phase B. **Ambigu** : progression sans volume, à ne pas appeler JAC (« The rise from the #2 Spring is not being labeled a JAC as Volume is not expanding », [Fraser, Jumping the Creek (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-jumping-the-creek/)) |

**Vérification pratique**

- [ ] **[D]** Un test de Phase C a précédé (cause de la poussée).
- [ ] **[D]** Le volume de la poussée dépasse celui des réactions récentes.
- [ ] **[H]** `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≥ 0.6`.
- [ ] **[D]** Position : dans la plage (mineur) ou au-dessus du creek majeur (JAC, fiche 3.12).
- [ ] **[D]** La réaction suivante est plus sèche que la poussée.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Expansion de volume et de spread, clôture haute. ② OI coin ↑ avec le prix : de nouveaux longs engagent du capital, version forte [I]. OI coin ↓ avec le prix ↑ : rachat de shorts, version faible. Cas du projet : cassure BTC 64 800, OI USD +0,81 % mais OI coin −0,36 %, donc du short covering. ③ Liquidations de shorts ↑ et funding contenu : squeeze. Funding qui s'envole avec OI↑ : longs encombrés. **Synthèse** : prix ↑ + OI coin ↑ + shorts liquidés + funding contenu = vraie demande qui presse les shorts |
| Invalidation | Réaction sur spread large et volume fort jusqu'au 🟦 support ; « Volume spiked on the LPS which demonstrates a supply of stock still being present » ([Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/)) |
| Implication de trading | **Pas d'entrée sur la barre SOS** : « esta acción no es correcta, lo más recomendable es esperar a la siguiente reacción (LPS) » ([Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/)). Pruden juge prématurée une entrée sur le JAC d'un creek mineur, « because it is evident that the major branch of the creek still lies ahead ». Le SOS sert à **préparer** l'achat du LPS |
| Erreurs fréquentes | Appeler « JAC » un SOS mineur ; l'acheter ; lire l'OI en USD |
| Sources | [Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/) · [Fraser, Buy Strategies (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/) · [Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) |

#### 3.11 🔵 LPS successifs — Phase D, dans la plage

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA : « LPS—last point of support, the low point of a reaction or pullback after a SOS » ; « there may be more than one LPS, despite the ostensibly singular precision of this term » · Pruden : « A series of SOS's and LPS's is good evidence that a bottom is in place » · Fraser : « second LPS » · Villahermosa : « LPS dentro del rango » ; « Price may retreat again developing a Last Point of Support/Supply within the range before attacking that zone again » · **Convention du projet** : « LPS » = repli **dans** la plage, avant le JAC ; le repli après le JAC = BU/BUEC (fiche 3.13) |
| Question posée par le CO | « Les acheteurs reviennent-ils plus haut à chaque repli ? La demande publique prend-elle le relais ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO laisse le prix respirer sans le soutenir. **Information** : chaque creux plus haut mesure la demande. **Risque** : un LPS volumique signale une offre encore présente |
| Lieu et moment | Entre le test de Phase C et le JAC, dans la plage : sur d'anciennes résistances internes devenues supports, en milieu de plage. Plusieurs, en escalier |
| Signature valide | **Volume** : réactions « on smaller spreads and diminished volumes » [D], sous le volume du SOS précédent ; `vol_ratio ≤ 0.85` [H]. **Spread** : étroit [D] ; `spread_atr ≤ 0.7` [H]. **Creux** : plus hauts en escalier ; Rutigliano (WA) : au LPS, « price does not fall below this level again during the TR » ([WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)). **Clôture** : `clv ≥ 0.5` sur la barre de retournement [H]. **Durée** : chaque réaction plus courte que la poussée |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : nouvelle poussée, jusqu'au JAC. **Raté** : un LPS casse le low du LPS précédent ; ré-étiquetage en Phase B (« relabel Phase C and D as a continuation of Phase B », Fraser). **Ambigu** : creux plus haut mais volume moyen, on attend une barre de demande |

**Vérification pratique**

- [ ] **[D]** Un SOS (même mineur) a précédé ce repli.
- [ ] **[D]** Volume du repli < volume du SOS précédent ; spread plus étroit.
- [ ] **[H]** `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`.
- [ ] **[D]** Creux plus haut que le LPS (ou le test) précédent.
- [ ] **[I]** Ratio « activity bullish » > 1 : vol_ratio moyen des poussées / vol_ratio moyen des réactions depuis la Phase C.
- [ ] **[D]** Barre de demande au retournement.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Repli sec, spread étroit. ② OI coin stable ou en légère baisse (prises de bénéfices), sans effondrement [I]. OI coin qui s'effondre pendant que le prix baisse : les longs fuient. ③ Funding qui refroidit, liquidations faibles. **Synthèse** : OI stable + funding qui se normalise + creux plus haut = repli de santé |
| Invalidation | Cassure du 🔵 low du LPS précédent ; pic de volume sur le LPS |
| Implication de trading | **Entrée** : barre de demande au départ du LPS (« On this second LPS, buy any of the early demand bars as the price turns up », [Fraser, Buy Strategies (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/)). **Stop** : sous 🔵 le low du LPS (dernier creux défendu) ou sous le low précédent. **Objectif** : décompte P&F compté **depuis ce LPS**, de droite à gauche ([WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)) ; R:R ≥ 3. Renforcer seulement une position déjà gagnante (« Only average up a winning position », [Fraser, Best Trade Entry Points (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/)) |
| Erreurs fréquentes | Prendre « last » au pied de la lettre ; acheter un LPS volumique ; confondre LPS dans la plage et BUEC |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Fraser, Buy Strategies (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/) · [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/) · [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) |

#### 3.12 🟢 JAC / SOS majeur — franchir le creek

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Pruden : « Jump Across the Creek (JAC) … a good sign if done on good spread and volume – a sign of strength (SOS) » ; « The term 'jump' was first used by Robert G. Evans » · Fraser : « A JAC is synonymous with a SOS (Sign of Strength) » ; « Major Sign of Strength » · Villahermosa : « When the upper Creek is jumped with a volume increase, this movement is a major SOS » · SMI : « To jump (rally) above the creek (drawn trendline) or flow of supply » |
| Question posée par le CO | « La demande peut-elle franchir l'offre flottante (le creek), et la sortie sera-t-elle acceptée ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO passe de passif à agressif, il paie l'écart [I : Kaniel & Liu]. **Information** : la présence d'acheteurs au-dessus de la plage. **Risque** : fausse cassure (UT/UTAD) |
| Lieu et moment | Fin de Phase D, au-dessus de la **zone** du creek (« Crossing the Creek is not a precise price level, it is an event in a zone », [Fraser, Jumping the Creek. A Review (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-04-jumping-the-creek-a-review/)) ; le creek a parfois une branche mineure et une majeure |
| Signature valide | **Volume** : « a surge in volume » [D] ; `vol_ratio ≥ 1.3` [H]. **Spread** : « widening price bars » [D] ; `spread_atr ≥ 1.3` [H]. **Clôture** : « a close near the high of a strong demand bar » [D] ; `clv ≥ 0.6` [H] (la FAQ de Villahermosa demande le quart supérieur, soit ≥ 0,75). **Position** : clôture au-dessus du creek. **Durée** : acceptation sur plusieurs barres |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : BU sec qui tient (fiche 3.13), puis markup. **Raté** : « If it fails to stay above that zone and re-enters the range, the event would be an Upthrust (UT) » ([Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/)). **Ambigu** : volume en hausse mais spread qui se resserre à la cassure (effort sans résultat, profil UTAD de Pruden) : on garde les deux étiquettes, « SOS ou UTAD selon la tenue » |

**Vérification pratique**

- [ ] **[D]** La séquence C → D est accomplie (test de Phase C, au moins un LPS).
- [ ] **[D]** Clôture au-dessus de la zone du creek, sur une barre de demande.
- [ ] **[H]** `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≥ 0.6`, clôture > high de la plage.
- [ ] **[D]** Statut « tentative » jusqu'à la tenue et au BU (règle CLAUDE.md n°3).
- [ ] **[D]** Pas d'effort sans résultat (volume ↑ et spread qui se resserre = alerte UTAD).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Expansion de volume et de spread, clôture haute. ② OI coin ↑ avec le prix : longs neufs, version forte [I]. OI coin ↓ avec le prix ↑ : couverture, version faible qui exige un BU. ③ Funding qui monte mais reste contenu ; liquidations de shorts. Funding extrême avec OI↑ : état encombré, à risque de *flush* ([BIS](https://www.bis.org/publ/work1087.htm)). **Synthèse** : OI coin ↑ + funding contenu + shorts liquidés = demande réelle ; OI coin ↓ + funding qui saute = squeeze qui doit encore passer le BU |
| Invalidation | Réintégration de la plage sur volume ; retour vers le niveau moyen des clôtures de la plage (profil UTAD) |
| Implication de trading | **Pas d'achat de la cassure** : « according to Wyckoff, you should not buy breakouts because that would leave you vulnerable to swift moves in the opposite direction if the breakout turned out to be false » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) ; « This breakout movement itself is not a trading opportunity » ([Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/)). On attend le BU (fiche 3.13), ou la 4ᵉ entrée de Fraser : « Breakout above the high of the BU/SOS », qui vient **après** le BU |
| Erreurs fréquentes | Acheter la barre de cassure ; appeler JAC une hausse sans volume ; ignorer la branche majeure du creek encore au-dessus |
| Sources | [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Fraser, Jumping the Creek (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-jumping-the-creek/) · [Fraser, Jumping the Creek. A Review (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-04-jumping-the-creek-a-review/) · [Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/) · [SMI, bibliothèque](https://wyckoffsmi.com/library/) |

> **Penser comme le CO** — Le récit d'Evans, relayé par Pruden, contient **deux** reculs. Avant le saut, le scout recule pour prendre de l'élan : « After probing the edge of the creek and discovering that the flow of supply was starting to dry up, the Boy Scout would retreat in order to get a running start », c'est le spring ou le LPS. Après le saut, fatigué, il revient se reposer au bord : c'est le BUEC. « The power of the movement by the Boy Scout would be measured by price spread and volume » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)). Aucun texte d'Evans lui-même n'a été retrouvé.

### Transition D → E — le back-up vérifie la nouvelle polarité

<!-- FIG:lps_vs_buec -->

#### 3.13 🔵 BU / BUEC — back-up sur l'ancienne résistance

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Pruden : « Back Up (BU) to a Last Point of Support (LPS) », donc le BU est le **mouvement** et le LPS son point bas ; « Backing Up to the Edge of the Creek » · StockCharts/WA : « BU—"back-up" … a colorful metaphor coined by Robert Evans » ; « Backing up to an LPS means a pullback to support that was formerly resistance » · Fraser 2015 et Villahermosa : « BUEC with a LPS » (synonymes) · Fraser 2022 : scénario BUEC (peu profond) **distinct** du scénario LPS (plus profond) · cours Wyckoff : « second springboard position » ([§11M p.6, page ©1931](https://archive.org/details/WyckoffMethodOfTapeReading)) |
| Question posée par le CO | « L'ancienne offre est-elle partie ? La résistance est-elle devenue support ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO laisse le prix revenir sans soutien pour voir qui vend [I]. **Information** : « both short-term profit-taking and a test for additional supply around the area of resistance » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). **Risque** : la sortie échoue (UT/UTAD) |
| Lieu et moment | Immédiatement après le JAC (« A backup is a test that immediately follows the jump »), sur le 🟦 creek touché par le dessus (« On the Back Up (BUEC) the price touches the Resistance line from above », [Fraser, Reaccumulation Roundup (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-reaccumulation-roundup/)). Il peut s'étirer en petite structure latérale, voire en « a new TR at a higher level » |
| Signature valide | **Volume** : « comparatively lighter volume » que le saut [D] (« lower volume than seen during the breakout movement », Villahermosa) ; `vol_ratio ≤ 0.85` [H]. **Spread** : « relatively narrow price-spread » [D], barres étroites et « entrelazadas » ; `spread_atr ≤ 0.7` [H]. **Profondeur** : école stricte, « should not go below the level of the prior Jump » ([Fraser, Jumping the Creek. A Review (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-04-jumping-the-creek-a-review/)) et « Que el precio no reingrese al rango » ([Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/)) ; école tolérante, « the shallower the reaction the more bullish » mais un LPS plus profond reste haussier ([Fraser, Stocks at a Crossroad (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-08-stocks-at-a-crossroad-891)), et Pruden place le stop sous le spring. **Durée** : non chiffrée |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : « supply cannot regain control » (Nokia, [Pruden](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)), le markup démarre (Phase E). **Raté** : « Un movimiento correctivo con rangos del precio amplios y volumen alto cancela la probabilidad de que el primer movimiento sea de ruptura » ([Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/)), c'est un upthrust. **Ambigu** : volume moyen sur le BU, on attend un second test (« deberíamos esperar a que se desarrollaran sucesivos test sobre la zona ») |

**Vérification pratique**

- [ ] **[D]** Un JAC/SOS majeur précède (cause du BU).
- [ ] **[D]** Volume du BU < volume du JAC ; barres étroites.
- [ ] **[H]** `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`.
- [ ] **[D]** Pas de clôture dans la plage (école stricte) ; au minimum, tenue au-dessus du dernier creux majeur (école tolérante).
- [ ] **[H]** `clv ≥ 0.5` sur la barre de retournement.
- [ ] **[D]** Barre de demande au départ du BU.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume qui sèche, spread étroit sur le creek. ② OI coin stable ou en légère baisse (prises de bénéfices, compatibles avec la lecture de StockCharts) [I] ; un effondrement d'OI pendant que le prix baisse signale des longs qui fuient. ③ Funding qui refroidit depuis les niveaux du SOS, liquidations faibles. **Synthèse** : OI stable + funding qui se normalise + pas de liquidations = changement de polarité sain |
| Invalidation | Clôture dans la plage sur spread large et volume fort (école stricte) ; retour vers le milieu de la plage ou cassure du 🟪 low du spring (école tolérante, stop de Pruden) |
| Implication de trading | **Entrée** : « initiate a position into the strength of these demand bars, placing stops under the prior low (labeled BU) » ([Fraser, Jumping the Creek. A Review (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-04-jumping-the-creek-a-review/)). **Stop** serré : sous 🔵 le low du BU **et** sous 🟦 le creek cassé (une réintégration invalide le JAC ; Villahermosa). **Stop** structurel : sous 🟪 le low du spring (invalidation du schéma ; Pruden, Nokia : entrée vers 110–115, stop « just below the 100 level »). **Objectif** : décompte P&F depuis le LPS ; R:R ≥ 3 |
| Erreurs fréquentes | Acheter le saut au lieu du BU ; accepter un BU volumique ; confondre le BU avec un LPS dans la plage ; croire qu'un second BU est anormal (Fraser décrit « SOS 2 / BUEC 2 », Pruden les points 12 et 14) |
| Sources | [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Fraser, Jumping the Creek (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-jumping-the-creek/) · [Fraser, Jumping the Creek. A Review (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-04-jumping-the-creek-a-review/) · [Fraser, Stocks at a Crossroad (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-08-stocks-at-a-crossroad-891) · [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/) · [Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/) · [Cours 1937 §11M, §16M](https://archive.org/details/WyckoffMethodOfTapeReading) |

> **Penser comme le CO** — Le cours décrit déjà le BU sans le nommer. Sur une page de 1931, après un petit repli, l'action « develops the second, springboard position at 56 (S) for a probable fast mark-up » ([§11M p.6](https://archive.org/details/WyckoffMethodOfTapeReading)). Une page ajoutée en 1937 par Wyckoff Associates (donc posthume) en donne la signature : au retour sur les anciens sommets, « the range again promptly narrows and volume immediately falls off during a shallow recession, telling us in advance that the offerings around those old tops were either dislodged … or they are being absorbed — the stock is in the second springboard position » ([§16M p.21](https://archive.org/details/WyckoffMethodOfTapeReading)).

### Phase E — la tendance continue de se tester

#### 3.14 🔵 Test de continuation — *test in a rising market* (Williams)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Williams : « test with low volume today in a rising market » · TradeGuider : indicateurs « TEST IN A RISING MARKET » et « TEST OF BREAKOUT » · Coulling : « test in the rising market » · Villahermosa : LPS « fuera del rango » (replis de tendance) · StockCharts/WA : tests « at key points during a price advance » |
| Question posée par le CO | « Après une poussée volumique, l'offre est-elle revenue ? » |
| Enjeu (coût · information · risque) | **Coût** : ne pas pousser plus haut tant que les vendeurs de la poussée sont là (« Markets will frequently have to rest and go sideways after any high volume up-days, because the selling has to disappear », [MTM p.39](https://www.tradeguider.com/mtm_251058.pdf)). **Information** : l'offre résiduelle. **Risque** : un SOW de tendance |
| Lieu et moment | Phase E, sur une barre baissière qui revient vers une zone de fort volume récente ; « This indicator is usually testing high volume in the recent background » ([Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)) |
| Signature valide | **Volume** : faible, inférieur à celui de la poussée testée [D]. **Spread** : variable ; marquage intrabarre [D]. **Clôture** : milieu ou haut [D] ; `clv ≥ 0.5` [H]. **Contexte** : tendance haussière établie (« do not enter long in a downtrend on this set up », [TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)) [D]. **Réponse** : barre suivante haussière [D] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : reprise de la tendance (« any low volume down-bars which appear after the prices have rallied and cleared the resistance to the left, is an indication of strength and higher prices to come », [MTM p.30](https://www.tradeguider.com/mtm_251058.pdf)). **Raté** : barre baissière large, volumique, clôture basse : SOW de tendance. **Ambigu** : test sans réponse, *negative action* |

**Vérification pratique**

- [ ] **[D]** Tendance haussière ou sortie de plage confirmée en amont (background de force).
- [ ] **[D]** Barre baissière à faible volume vers une zone de fort volume récente.
- [ ] **[H]** `vol_ratio ≤ 0.85` ; volume < volume de la poussée testée.
- [ ] **[H]** `clv ≥ 0.5`.
- [ ] **[D]** Barre suivante haussière (« Tests need TWO BARS »).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Barre baissière sèche. ② OI coin plat ou ↓ (prises de bénéfices) [I]. ③ Funding qui refroidit. Si l'OI monte avec un ratio L/S ↓ : des shorts s'ouvrent contre la tendance, carburant si la tendance reprend, alerte si une barre d'offre suit. **Synthèse** : OI↓ + funding en baisse + réponse haussière = respiration saine |
| Invalidation | Barre d'offre (spread large, volume fort, clôture basse) sous le low du test |
| Implication de trading | **Entrée** : ordre stop au-dessus du high de la barre de test. **Stop** : sous le low du test, ou sous 🔵 le dernier LPS/BU (dernier support validé). **Objectif** : prochaine zone de résistance ou décompte de palier ; R:R ≥ 3 |
| Erreurs fréquentes | Acheter ce montage dans un downtrend ; oublier le background ; acheter sans barre de confirmation |
| Sources | [MTM p.30, 37, 39, 112–113](https://www.tradeguider.com/mtm_251058.pdf) · [Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf) · [TG, SOS](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf) · [Coulling p.45](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page45.html) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) |

#### 3.15 🔵 Réaccumulation — *stepping stone* en Phase E

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA : « re-accumulation », « stepping stones », « stepping stone confirming count » · Pruden : « Reaccumulation (a trading range within a continuing upmove) » · Fraser : « Stepping Stone Reaccumulation (SSR) » · SMI : « ordinary shakeout » en tendance haussière |
| Question posée par le CO | « Dans cette pause, les ventes sont-elles des prises de bénéfices que j'absorbe, ou une distribution ? » |
| Enjeu (coût · information · risque) | **Coût** : le CO renforce (« The C.O. will use these Reaccumulation phases to add to their holdings », [Fraser, Rev Up with Reaccumulation (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-rev-up-with-reaccumulation-trading-ranges)). **Information** : la qualité des vendeurs. **Risque** : confusion avec une distribution, dans les deux sens |
| Lieu et moment | N'importe où en Phase E : « New, higher-level TRs … can occur at any point in Phase E » ; un BU peut lui-même devenir une telle plage |
| Signature valide | **Phase A** : « the points representing PS, SC and ST are not evident in Phase A. Rather, in such cases, Phase A resembles that more typically seen in distribution » [D]. **Volume** : « In reaccumulation, each drop toward support tends to come on less volume than the drop before it » ([WA 2026](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)) [D]. **Durée/amplitude** : « shorter duration and smaller amplitude » [D]. **Creux** : bas de structure « at about the 1/3 to ½ point of the completed structure » ([Fraser, Distribution or Re-Accumulation? (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-03-distribution-or-reaccumulation-699)) ; « lower peaks are followed by a Spring » ([Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : spring tardif puis SOS au-dessus du sommet de la plage, BUEC, reprise. **Raté** : volume lourd et croissant sur les baisses, sommets plus bas : distribution. **Ambigu** : le test décisif est « how well it can reach and exceed overhead resistance » ([Fraser, Distribution or Re-Accumulation? (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-03-distribution-or-reaccumulation-699)) |

**Vérification pratique**

- [ ] **[D]** Tendance haussière en amont (contexte HTF).
- [ ] **[D]** Volume des baisses décroissant d'un passage à l'autre.
- [ ] **[D]** Plage plus courte et plus étroite que la base primaire.
- [ ] **[D]** Spring ou LPS tardif, puis SOS au-dessus du sommet de la plage.
- [ ] **[D]** Les deux scénarios (réaccumulation / distribution) tenus jusqu'à la sortie.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Gradient de volume des baisses. ② OI coin ↓ sur les baisses (prises de bénéfices), OI ↑ à la sortie (longs neufs) [I]. ③ Funding qui se normalise dans la plage. Funding très élevé + OI ↑ + prix qui cale au sommet : risque de distribution |
| Invalidation | Volume lourd et croissant sur les baisses ; cassure du bas de la plage sans réintégration ; échec sous la résistance |
| Implication de trading | Mêmes montages que la base primaire (spring/test, LPS, BU), avec un décompte de palier à plus petite case (« stepping stone confirming count ») ; R:R ≥ 3 |
| Erreurs fréquentes | Shorter une réaccumulation prise pour une distribution (« Traders will often mistake Reaccumulation for a Distributional top », [Fraser, Reaccumulation Roundup (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-reaccumulation-roundup/)) ; exiger un SC en Phase A |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Fraser, Reaccumulation Roundup (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-reaccumulation-roundup/) · [Fraser, Distribution or Re-Accumulation? (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-03-distribution-or-reaccumulation-699) · [WA 2026](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) |

## 4. Micro-tests VSA : la barre de test n'est pas une barre de no supply

La VSA vient de Wyckoff : le syndicat de traders de la région de Los Angeles (Beverly Hills) pour lequel travaillait Williams lui a fait suivre le cours Wyckoff, et TradeGuider s'appelait « Wyckoff VSA » ([Deusto/Planeta](https://proapi.planetadelibros.com/descargas/sala-prensa-libro/sinopsis-y-biografia/294401/master-the-markets.pdf) ; [MTM, 4ᵉ de couverture](https://www.tradeguider.com/mtm_251058.pdf) ; [Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)). Mais elle étiquette des **barres** à la lumière du *background*, quand Wyckoff lit une **structure**. Un « test » VSA n'exige ni AR préalable ni retour au climax : ce n'est pas le ST wyckoffien.

#### 4.1 🔵 Barre de test (Williams / TradeGuider / Coulling)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Williams : « test », « successful test », « failed test », « Possible Test » · TradeGuider : indicateur « BASIC TEST » (SOS 11), « NO SUPPLY/TEST » (SOS 81) · Coulling : « low volume test » / « High Volume Test » |
| Question posée par le CO | « Si je marque vite les prix à la baisse, les ours sortent-ils ? » (« The best way to find out is to rapidly mark the prices down. This challenges any bears around to come out into the open and show their hand », [MTM p.34](https://www.tradeguider.com/mtm_251058.pdf)) |
| Enjeu (coût · information · risque) | **Coût** : « he cannot mark prices up when others are selling into the same market without losing money » (p.34). **Information** : « Low volume … shows there is little selling on the mark-down. High volume … shows that there is in fact selling (supply) » (p.34). **Risque** : monter au-dessus d'une offre non mesurée |
| Lieu et moment | « Any down-move dipping into an area of previous selling (previous high volume level) » (p.35), avec de la force dans le *background* (SC, *stopping volume*, absorption, tendance haussière) |
| Signature valide | **Forme** : marquage à la baisse pendant la barre puis reprise ; « regains to close on, or near the high, on lower volume » (p.35) [D]. **Volume** : faible, inférieur à celui de la zone d'offre testée [D]. **Spread** : pas d'exigence de range étroit ; « If the spread is narrow it will have less impact » (SOS 11) [D] ; Coulling : « the body must be a narrow spread, with a deep lower wick. The colour of the body can be either bullish or bearish » ([Coulling p.45](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page45.html)) [D]. **Bonus** : « Add extra weight if the low of the bar is into fresh new low ground and also if it is a down bar » (SOS 11). **Non requis** : nouveau plus-bas, « volume < 2 barres précédentes » (critère du no supply) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : « a successful test (on low volume) tells you that the market is ready to rise immediately ». **Raté** (volume élevé) : « a higher volume test usually results in a temporary up-move, and will be subject to a re-test of the same price area again at a later time. The "W" shape results from the action of re-testing an area that had too much supply before » (p.34). **Sans réponse** : « Any testing that does not respond immediately with higher prices, or certainly during the next day or so, can be considered an indication of weakness » (p.35) ; *negative action* (p.152) |

**Vérification pratique**

- [ ] **[D]** Force dans le *background* (SC, *stopping volume*, absorption, tendance haussière).
- [ ] **[D]** La barre plonge dans une zone de fort volume antérieure.
- [ ] **[D]** Volume plus faible que la zone d'offre testée ; afficher aussi `vol_ratio` **[H]**.
- [ ] **[D]** Clôture au milieu ou en haut ; `clv ≥ 0.5` **[H]**, idéalement ≥ 0,7 **[H]**.
- [ ] **[D]** Mèche basse visible (marquage intrabarre) ; ne **pas** exiger `spread_atr ≤ 0.7`.
- [ ] **[D]** Barre suivante haussière (« Tests need TWO BARS to confirm strength », [TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)), sinon *negative action* après 2–3 barres.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume du test vs zone testée. ② **Nuance futures** de Williams : « you can expect high volume testing in a non-cash market, such as a future, to show strength » (p.158) ; TradeGuider : volume « low (can be high in the futures market) ». Sur perps, le volume seul ne tranche donc pas, et l'OI coin arbitre [I] : OI↓ sur un test volumique = fermetures et absorption (plutôt constructif) ; OI↑ sur un marquage volumique = nouveaux vendeurs (re-test probable). ③ Si OI↑ et le prix cale : ratio L/S, funding, liquidations |
| Invalidation | Clôture basse sur volume fort, sous le low du test ; barre suivante baissière avec de la faiblesse dans le *background* : « this is a strong sign of additional weakness and is called a FAILED TEST » ([TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)) |
| Implication de trading | TradeGuider : « Place a stop under the low of the climactic bar and place a buy order above the test bar » ([TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)). **Entrée** : ordre stop au-dessus du high de la barre de test (la confirmation vient à vous). **Stop** : sous 🟦 le low de la barre climactique (l'action testée). **Objectif** : borne haute de la structure, puis décompte ; R:R ≥ 3 |
| Erreurs fréquentes | Confondre test et no supply ; exiger un range étroit ; prendre un test sur fond de distribution (« means little », p.110) ; ignorer la nuance futures |
| Sources | [MTM p.19, 34–35, 89, 110, 152, 158–159](https://www.tradeguider.com/mtm_251058.pdf) · [Holmes/TG, SOS 11, SOS 81](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf) · [TG, SOS](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf) · [Coulling p.44–46](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page45.html) |

#### 4.2 🔵 No supply (*no selling pressure*)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Williams : « no selling pressure » / « no supply » · TradeGuider : « NO SUPPLY » (SOS 199), « NO SUPPLY/TEST » (SOS 81) ; le support de séminaire regroupe « No Supply / Test in a Rising Market / No Selling Pressure » |
| Question posée par le CO | Aucune : c'est un état **passif** (personne ne vend), pas un geste provoqué |
| Enjeu (coût · information · risque) | **Information** : les vendeurs manquent sur la baisse. **Risque** : un manque de vendeurs n'est pas une demande |
| Lieu et moment | Barre baissière, de préférence en tendance haussière ou après de la force |
| Signature valide | « If prices are dropping on volume that is less than the previous two bars (or candles), especially if spreads are narrow, with the price closing in the middle or high of the bar, this indicates that there is 'no selling pressure' » ([MTM p.19](https://www.tradeguider.com/mtm_251058.pdf)) [D] ; « A down bar with volume lower than the two previous bars shows lack of selling pressure as the market falls » (SOS 199) [D]. Proxy : vol < min(vol[t−1], vol[t−2]) **et** `spread_atr ≤ 0.7` **et** `clv ≥ 0.5` [H] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Confirmé** : « The next bar should be up to confirm this indicator » (SOS 199). **Recouvrement** : « Sometimes it may close up on the middle or high which represents a test » (SOS 81). **Non confirmé** : barre suivante baissière, rien n'est prouvé |

**Vérification pratique**

- [ ] **[D]** Barre baissière.
- [ ] **[D]** Volume < volume des deux barres précédentes.
- [ ] **[H]** `spread_atr ≤ 0.7`, `clv ≥ 0.5`.
- [ ] **[D]** Barre suivante haussière.
- [ ] **[D]** Tendance de fond haussière (« do not enter long in a downtrend on this set up », [TG](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf)).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume plus bas que les deux barres précédentes. ② OI coin plat [I]. ③ Rarement nécessaire |
| Invalidation | Barre suivante baissière et volumique |
| Implication de trading | Déclencheur de **continuation** dans une tendance déjà prouvée (cf. fiche 3.14), jamais un retournement à lui seul. **Entrée** : au-dessus du high de la barre de confirmation. **Stop** : sous le low de la barre de no supply, ou sous 🔵 le dernier LPS/BU (dernier support validé). **Objectif** : prochaine résistance ; R:R ≥ 3 |
| Erreurs fréquentes | Le prendre pour un test (pas de lieu ni de geste) ; l'acheter dans un downtrend |
| Sources | [MTM p.19, 40, 156](https://www.tradeguider.com/mtm_251058.pdf) · [Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf) · [TG, SOS](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf) |

#### 4.3 🔴 No demand (et test de la demande de Coulling)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Williams : « no demand » · TradeGuider : « NO DEMAND » (SOW 6) · Coulling : « test of demand » · Williams : l'*upthrust* à bas volume comme absence de demande |
| Question posée par le CO | En distribution : « Reste-t-il des acheteurs pour gêner ma baisse ? » (Coulling : « a test is employed to make sure that all the buying (demand) pressure has been absorbed in the distribution phase », [p.46](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page46.html)) |
| Enjeu (coût · information · risque) | **Information** : l'absence d'acheteurs professionnels sur la hausse. **Risque** : shorter une tendance haussière saine |
| Lieu et moment | Barre haussière près d'un ancien sommet, ou rallye sous une résistance |
| Signature valide | « An up bar on a narrow spread closing in the middle with low volume, or volume lower than the last two bars. It can be a down bar if the high is higher than the previous bar » (SOW 6, [Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)) [D]. Coulling : « The market is marked higher using some news, and if there is no demand, closes back near the open, with very low volume » ([p.47](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page47.html)) [D]. Proxy : barre haussière, vol < min(vol[t−1], vol[t−2]), `spread_atr ≤ 0.7`, `clv ≤ 0.5` [H] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Confirmé** : « The next bar should be down to confirm this indicator » ; « If you are at or near an old top to the left it is highly unlikely that a market will go up through this old top on no demand » (SOW 6). **Raté** (pour le distributeur) : « a failed test stops the campaign in its tracks » ([Coulling p.47](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page47.html)) |

**Vérification pratique**

- [ ] **[D]** Barre haussière (ou plus-haut plus haut) à spread étroit.
- [ ] **[D]** Volume < volume des deux barres précédentes.
- [ ] **[H]** `spread_atr ≤ 0.7`, `clv ≤ 0.5`.
- [ ] **[D]** Barre suivante baissière (confirmation : « we need confirmation before shorting the market following any sign of no demand », [MTM p.33](https://www.tradeguider.com/mtm_251058.pdf)).
- [ ] **[D]** Faiblesse dans le *background* (« Do not short an No Demand in an uptrend, it is in the wrong place », [TG](https://volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20weakness.pdf)).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Hausse à faible volume. ② OI coin plat ou ↓ (rachat de shorts sans longs neufs) [I]. ③ Funding et ratio L/S si l'OI monte pendant que le prix cale : des longs entrent sous la résistance, donc piégés si la barre suivante baisse (règle CLAUDE.md n°4) |
| Invalidation | Barre suivante haussière et volumique qui passe l'ancien sommet |
| Implication de trading | Signal de vente seulement sous résistance et sur fond de faiblesse ; **Stop** : au-dessus du high de la barre de no demand (ou du 🟥 sommet testé) ; **Objectif** : borne basse ; R:R ≥ 3 |
| Erreurs fréquentes | Shorter un no demand dans une tendance haussière ; shorter sans barre de confirmation |
| Sources | [MTM p.32–33, 153](https://www.tradeguider.com/mtm_251058.pdf) · [Holmes/TG, SOW 6](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf) · [TG, SOW](https://volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20weakness.pdf) · [Coulling p.46–47](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page47.html) |

> **Piège** — « Failed test » a trois sens différents. (A) un test **volumique**, donc offre présente, re-test attendu ([MTM p.34, p.77, p.95](https://www.tradeguider.com/mtm_251058.pdf)) ; (B) un test **sans réponse**, *negative action* (p.152) ; (C) l'indicateur TG « FAILED TEST » (SOW 86), une barre baissière large sous les plus-bas récents juste après un test ([Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)). Préciser lequel à chaque usage.

## 5. Fiches de tests — distribution : le CO teste s'il reste des acheteurs

Distribution, redistribution et réaccumulation se ressemblent : « In a redistribution TR within a larger downtrend, Phase A may look more like the start of an accumulation TR » et la Phase A d'une réaccumulation « resembles that more typically seen in distribution » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). Pruden : « distribution is generally accomplished in a shorter time period than accumulation » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)).

<!-- FIG:schema_distribution -->

| Phase | Test | Ce qui est testé | Fiche |
|---|---|---|---|
| A | 🔵 ST du BC (après le 🔴 BC et l'🔵 AR) | la demande résiduelle au sommet | 5.1 |
| B | 🟠 UT in Phase B (+ 🔴 SOW in Phase B / mSOW) | la demande de cassure à vendre, la demande sous l'AR | 5.2 |
| C | 🟠 UTAD | test « définitif » de la nouvelle demande au-dessus de la plage | 5.3 |
| C | 🟣 Test de l'UTAD | la demande restante après l'UTAD | 5.4 |
| D | 🔵 LPSY (multiples) | la difficulté à monter après un SOW | 5.5 |
| D→E | 🔴 FTI (chute à travers la glace) + 🔵 retour sous la glace | la conversion support → résistance | 5.6 |

#### 5.1 🔵 ST du BC (Phase A de distribution)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA, Pruden, S&C 2014, Fraser : **ST** ; « An ST may take the form of an upthrust (UT) » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) |
| Question posée par le CO | « Reste-t-il assez de demande au sommet pour absorber mon offre ? » |
| Enjeu (coût · information · risque) | **Coût** : vendre sans faire baisser le prix trop tôt. **Information** : la profondeur de la demande au niveau du BC. **Risque** : une réaccumulation (le sommet n'en est pas un) |
| Lieu et moment | Après l'AR, retour vers la zone du BC ; souvent un sommet légèrement plus bas (schémas) |
| Signature valide | **Volume** : divergence entre sources. StockCharts/WA : « volume and spread should thus decrease as price approaches the resistance area of the BC » ; S&C 2014 : « Rally on narrowing price spread and diminished volume that is stopped at or near the price level of BC. Confirms BC » [D]. Fraser : « The peak of the ST will generally be marked by high volume and reversal price bars. As price turns back down volume will normally remain high » ([Fraser, Distribution Definitions (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-distribution-definitions/)) [D]. Réconciliation [I] : volume en baisse sur la **montée** vers le BC, volume fort sur les **barres de retournement**. **Clôture** : faible sur le retournement ; `clv ≤ 0.5` [H]. **Sommet** : égal ou un peu plus bas que le BC, parfois un léger dépassement (UT) |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : retour vers le bas de la plage, Phase B. **Raté** (demande forte, sommet accepté au-dessus) : réaccumulation possible ; Fraser : « If the rally is stopped near the BCLX price level either a Distribution or Stepping Stone Reaccumulation is forming » ([Fraser, Context is King (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-context-is-king/)). **Ambigu** : on tient les deux scénarios |

**Vérification pratique**

- [ ] **[D]** BC identifiable (volume et spread climactiques, clôture faible) puis AR.
- [ ] **[D]** Volume en baisse sur l'approche du BC **ou** barres de retournement volumiques à clôture faible.
- [ ] **[H]** `clv ≤ 0.5` sur la barre de retournement.
- [ ] **[D]** Sommet ≤ BC, ou léger dépassement aussitôt rejeté.
- [ ] **[D]** Contexte HTF : tendance haussière mûre (distribution) ou tendance baissière (redistribution).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume de la montée vs volume du retournement. ② OI coin ↑ dans la zone du BC avec une clôture faible : des longs s'ouvrent face à l'offre du CO, donc des longs piégés [I] ; dans un downtrend, un OI↑ à la résistance = demande qui se fait piéger (règle CLAUDE.md n°4). ③ Funding élevé + ratio L/S en hausse : foule acheteuse encombrée |
| Invalidation | Acceptation au-dessus du BC avec un repli sec qui tient : réaccumulation |
| Implication de trading | Pour un détenteur : alléger dans les sommets du BC, du ST et des UT (« Phases A & B are tactically where to sell into the BCLX, ST, and UT price peaks », [Fraser, Context is King (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-context-is-king/)). Pour un short : attendre la Phase D (fiche 5.5). On trace 🟥 le plafond (high du BC, borne haute) et 🟦 le plancher (low de l'AR, borne basse) |
| Erreurs fréquentes | Exiger un volume sec quand Fraser décrit un retournement volumique ; présumer la distribution sans contexte |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [S&C 2014](https://www.wyckoffanalytics.com/wp-content/uploads/2019/08/V32C08822PRUD.pdf) · [Fraser, Distribution Definitions (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-distribution-definitions/) · [Fraser, Context is King (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-context-is-king/) |

#### 5.2 🟠 UT in Phase B (et 🔴 SOW in Phase B / mSOW)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Schémas StockCharts/WA : « UT » (#1) / « UT in Phase B » (#2) au-dessus du BC ; « SOW in Phase B » sous l'AR · Villahermosa : UT, et **mSOW** pour le creux plus bas · Fraser : « The UT is an extended form of a Secondary Test » |
| Question posée par le CO | « Puis-je attirer la demande de cassure et lui vendre ? » ; puis, sur le SOW in B : « Combien de demande reste-t-il sous l'AR ? » |
| Enjeu (coût · information · risque) | **Coût** : nul, le CO vend dans la demande des acheteurs de momentum. **Information** : l'appétit des acheteurs au-dessus du BC. **Risque** : une vraie sortie (accumulation) |
| Lieu et moment | Phase B, au-dessus du 🟥 high du BC ; bref (« A UT is a minor breakout to new high prices which is brief and fails quickly », [Fraser, Context is King (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-context-is-king/)) |
| Signature valide | **Prix** : « a UT will not linger above the Resistance area for long before returning to support » ([Fraser, Distribution Definitions (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-distribution-definitions/)) [D]. **Volume/clôture** : SMI, un upthrust doit « penetrate the top of the trading range on a narrower spread, higher volume and poor close » ([SMI, Test of the Shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/)) [D] ; Williams, « the volume can be either low (no demand) or high (supply overcoming the demand) », clôture « on or very near the lows » ([MTM p.78](https://www.tradeguider.com/mtm_251058.pdf)) [D]. **Volume de Phase B** : « volume is high on the declines and with each succeeding decline off the Resistance level, volume and volatility tend to be higher » (Fraser) [D]. **SOW in B** : chute qui casse l'AR sur spread et volume accrus [D] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** (pour le distributeur) : retour rapide vers le support, puis SOW sous l'AR (« The SOW undercutting the AR is another subtle clue that Distribution is at hand », [Fraser, Just Another Phase (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-just-another-phase/)). **Raté** : acceptation au-dessus avec un repli sec (mSOS/SOS d'une réaccumulation). **Ambigu** : on tient UT/UA jusqu'à la résolution |

**Vérification pratique**

- [ ] **[D]** Percée au-dessus du high du BC, puis réintégration rapide.
- [ ] **[D]** Spread plus étroit, volume plus fort, clôture faible (SMI), ou volume faible (no demand, Williams).
- [ ] **[H]** Barre de réintégration `clv ≤ 0.5` ; profil « effort sans résultat » : `vol_ratio ≥ 1.3` avec `spread_atr` qui baisse.
- [ ] **[D]** Volume plus fort sur les baisses que sur les hausses (« activity bearish »).
- [ ] **[D]** SOW in B : creux sous l'AR sur volume et spread en hausse.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume, spread et clôture de la percée. ② OI coin ↑ sur la percée puis réintégration : des acheteurs de cassure piégés [I]. ③ Liquidations de shorts sur la mèche (stops acheteurs au-dessus du BC), funding qui grimpe, ratio L/S en hausse. **Synthèse** : OI↑ + shorts liquidés + funding en hausse + réintégration = la demande forcée et le FOMO ont servi de contrepartie |
| Invalidation | Prix qui tient au-dessus du BC plusieurs barres avec un repli sec |
| Implication de trading | Short agressif possible, mais « the "smart money" repeatedly stops out traders who initiate such short positions with one UT after another, so it is often safer to wait until Phase D and an LPSY » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). Si l'on prend le risque : **Entrée** sous le low de la barre de réintégration ; **Stop** au-dessus de 🟧 le high de l'UT (extrême du piège) ; **Objectif** 🟦 le low de l'AR (borne basse) ; R:R ≥ 3, taille réduite |
| Erreurs fréquentes | Shorter chaque UT ; prendre un UT pour un SOS ; oublier que « You rarely see up-thrusts in strong markets » ([MTM p.79](https://www.tradeguider.com/mtm_251058.pdf)) |
| Sources | [Fraser, Distribution Definitions (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-distribution-definitions/) · [Fraser, Context is King (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-context-is-king/) · [Fraser, Just Another Phase (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-just-another-phase/) · [SMI, Test of the Shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/) · [MTM p.78–79](https://www.tradeguider.com/mtm_251058.pdf) · [Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/) |

#### 5.3 🟠 UTAD — Upthrust After Distribution

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA : « the distributional counterpart to the spring and terminal shakeout » · SMI : définition attribuée à « Mr. Evens » (sic) dans le glossaire · Pruden : « more definitive test of new demand » · Fraser : « a final Upthrust to a new high after the completion of Distribution » |
| Question posée par le CO | « Après la cassure du plafond, reste-t-il une demande nouvelle capable de tenir ? » |
| Enjeu (coût · information · risque) | **Coût** : nul, le CO vend aux acheteurs de cassure et aux shorts qui se couvrent (« This UTAD usually results in weak holders of short positions giving them up to more dominant interests, and also in more distribution to new, less informed buyers », [Pruden](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)). **Information** : la dernière mesure de la demande. **Risque** : la cassure tient (JAC de réaccumulation) |
| Lieu et moment | Fin de plage, au-dessus du 🟥 BC et des UT précédents : l'UTAD **dépasse le BC par construction** (« The higher highs at each Upthrust (UT) keeps most stockholders calm », [Fraser, Divining Distribution (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-03-divining-distribution/)). Il n'est pas obligatoire (schéma de distribution #2) |
| Signature valide | **Deux profils baissiers** selon Pruden : « on light volume with no follow through or on heavy volume with a breakdown back into the centre of the trading range » [D]. **Effort sans résultat** (SMI/Evans, Pruden schéma 3) : « on increasing volume and "relative narrowing spread" and then return to the average level of closes of the TR » [D] ; « The spread MUST BE COMPARED to the VOLUME » ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/)). **Clôture** : retour dans la plage, `clv ≤ 0.5` [H]. **Pénétration** : `pen_atr ≥ 0.1` ATR [H] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : « failure back into the Distribution range and a cascading fall of price to and through Support » ([Fraser, Divining Distribution (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-03-divining-distribution/)) ; « The evidence that supply is clearly dominant increases either with a clear break of support or with a decline below the mid-point of the TR after a UT or UTAD » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)). **Raté** (pour le distributeur) : tenue au-dessus avec un BU sec, c'était un JAC. **Ambigu** : la « third variation » de Pruden, un upthrust qui retombe au milieu d'une plage trop large pour être une distribution complète |

**Vérification pratique**

- [ ] **[D]** Fin de plage (Phases A et B accomplies) : sinon, il s'agit d'un UT de Phase B.
- [ ] **[D]** Percée au-dessus du BC et des UT, puis retour dans la plage.
- [ ] **[D]** Volume faible sans suivi **ou** volume fort avec retour au centre ; effort sans résultat.
- [ ] **[H]** `pen_atr ≥ 0.1` ATR ; barre de retour `clv ≤ 0.5`.
- [ ] **[D]** Confirmation : cassure sous le milieu de la plage.
- [ ] **[D]** Étiquette conditionnelle (« SOS ou UTAD selon la tenue ») tant que la plage n'est pas cassée.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Volume et spread de la percée (effort sans résultat ?). ② OI coin ↑ sur la percée (longs de FOMO) puis réintégration : longs piégés [I]. ③ Liquidations de shorts sur la montée (stops acheteurs), funding qui monte, puis liquidations de longs à la descente. Un flux acheteur net positif sans progrès du prix = vendeurs passifs qui absorbent [I]. **Synthèse** : OI↑ + funding en hausse + shorts liquidés + retour dans la plage = la demande forcée a été vendue |
| Invalidation | Tenue au-dessus de la plage avec un BU sec qui ne réintègre pas : JAC/SOS de réaccumulation |
| Implication de trading | **Short agressif** : après la réintégration ; **Stop** : au-dessus de 🟧 le high de l'UTAD (extrême du piège : y revenir en clôture = demande réelle). **Short prudent** : sur le test de l'UTAD (fiche 5.4) ou le LPSY. **Objectif** : 🟦 le plancher (low de l'AR), puis le décompte P&F baissier ; R:R ≥ 3 |
| Erreurs fréquentes | Appeler UTAD une percée de Phase B ; shorter avant la réintégration ; oublier la lecture réaccumulation (« A common mistake traders make with Reaccumulation is to conclude it is Distribution », [Fraser, Rev Up with Reaccumulation (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-rev-up-with-reaccumulation-trading-ranges)) |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [Fraser, Divining Distribution (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-03-divining-distribution/) · [Fraser, Distribution or Re-Accumulation? (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-03-distribution-or-reaccumulation-699) |

#### 5.4 🟣 Test de l'UTAD

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Fraser : « Note the persistent weakness that follows the UTAD and Test » ([Fraser, Divining Distribution (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-03-divining-distribution/)) · Villahermosa : le LPSY « sería su test » ([LPS ES](https://tradingwyckoff.com/last-point-of-support/)) ; « Upthrust test » ([guide](https://tradingwyckoff.com/en/wyckoff-method/)) · **Aucune source primaire ne donne de critères propres** |
| Question posée par le CO | « Après l'UTAD, un rallye vers le sommet trouve-t-il encore des acheteurs ? » |
| Enjeu (coût · information · risque) | **Information** : la confirmation de l'épuisement de la demande. **Risque** : une seconde poussée qui casse vraiment |
| Lieu et moment | Après l'UTAD, rallye vers sa zone ; Phase C, fin |
| Signature valide | Par miroir du test du spring et du rallye-test de Pruden (point 11) [I] : **Volume** < volume de l'UTAD ; `vol_ratio ≤ 0.85` [H]. **Spread** : étroit ; `spread_atr ≤ 0.7` [H]. **Sommet** : plus bas que l'UTAD. **Clôture** : `clv ≤ 0.5` [H]. **Réponse** : baisse dans les 1–3 barres |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : SOW, Phase D. **Raté** : nouveau plus-haut sur volume plus fort, début de vraie cassure. **Ambigu** : sommet égal sur volume moyen, attendre un LPSY |

**Vérification pratique**

- [ ] **[D]** Un UTAD réintégré en amont.
- [ ] **[I]** Volume du rallye < volume de l'UTAD ; spread étroit.
- [ ] **[H]** `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `clv ≤ 0.5`.
- [ ] **[I]** Sommet plus bas que l'UTAD.
- [ ] **[D]** Barre baissière de confirmation.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Rallye sec, spread étroit. ② OI coin plat ou ↓ (rachats de shorts sans longs neufs) [I] ; OI ↑ avec le prix qui cale : des longs entrent sous le sommet. ③ Dans ce cas : ratio L/S en hausse, funding positif, liquidations faibles = longs encombrés sous la résistance |
| Invalidation | Clôture au-dessus de 🟧 le high de l'UTAD sur volume |
| Implication de trading | **Entrée short** : sous le low de la barre de rejet. **Stop** : au-dessus de 🟪 le high du test (pivot de Phase C) et de 🟧 l'UTAD. **Objectif** : 🟦 le low de l'AR (borne basse), puis le décompte P&F ; R:R ≥ 3 |
| Erreurs fréquentes | Exiger ce test quand le marché casse directement (un LPSY peut en tenir lieu) ; ignorer un volume croissant sur le test |
| Sources | [Fraser, Divining Distribution (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-03-divining-distribution/) · [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/) · [Villahermosa, guide](https://tradingwyckoff.com/en/wyckoff-method/) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) |

#### 5.5 🔵 LPSY — Last Point of Supply (multiples)

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | StockCharts/WA : « LPSY—last point of supply. After testing support on a SOW, a feeble rally on narrow spread » · Pruden : points 11, 13, 15, 17 · Villahermosa : « El Last Point of Supply (LPSY) es la acción inmediata que precede a un Sign of Weakness (SOW) » ; type 1 = test de l'UTAD ; type 3 = « Fall Through the Ice » (retest) |
| Question posée par le CO | « Après mon SOW, le marché a-t-il encore la force de monter ? » |
| Enjeu (coût · information · risque) | **Coût** : nul, le CO écoule « the last waves of large operators' distribution ». **Information** : l'épuisement de la demande. **Risque** : un spring qui reprend la plage |
| Lieu et moment | Phase D (et E), rallyes faibles après un SOW, sous la 🟦 glace ou sous des résistances internes ; plusieurs |
| Signature valide | **Spread** : étroit, rallye « feeble » [D]. **Volume** : « Volume may be light or heavy, showing weak demand or substantial supply » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) [D] : le volume sec n'est **pas** requis. **Sommet** : plus bas. **Clôture** : faible ; `clv ≤ 0.5` [H] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : markdown (« An LPSY typically results in a bear market downtrend », [Fraser, Unfriendly Skies (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-06-the-unfriendly-skies/)). **Raté** : le rallye reprend la plage et tient, scénario spring. **Ambigu** : LPSY à volume fort et clôture moyenne, attendre le rallye suivant (Pruden : « An even better place would be on the rally testing point 11 ») |

**Vérification pratique**

- [ ] **[D]** Un SOW en amont.
- [ ] **[D]** Rallye à spread étroit, sommet plus bas.
- [ ] **[D]** Volume faible (demande faible) **ou** fort (offre qui absorbe) : les deux sont baissiers si le rallye échoue.
- [ ] **[H]** Barre de rejet `clv ≤ 0.5`.
- [ ] **[D]** Le LPSY se compare aux précédents : chacun moins robuste (« Note how the rallies to the BCLX, ST, UT and LPSY are each less robust than the prior », [Fraser, Just Another Phase (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-just-another-phase/)).

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① Rallye étroit qui échoue. ② OI coin ↓ pendant le rallye : simple rachat de shorts, pas de demande nouvelle [I]. OI coin ↑ pendant que le prix cale : des longs entrent sous la résistance. ③ Ratio L/S ↑ + funding ↑ + liquidations faibles = longs encombrés, donc piégés ; carburant pour la baisse suivante |
| Invalidation | Reprise de la 🟦 glace (support cassé) et tenue au-dessus |
| Implication de trading | **Entrée short** : sur l'échec du rallye (barre de rejet). **Stop** : au-dessus du high du LPSY **et** de la 🟦 glace cassée (« Coloca o mueve el stop loss por encima del Last Point of Supply y la línea de soporte (Ice) rota », [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/)). **Objectif** : 🟥 décompte P&F baissier ; R:R ≥ 3. Ajouter seulement en gain (« additional short positions be added or pyramided only if our initial positions are in profit », Pruden) |
| Erreurs fréquentes | Exiger un volume sec ; shorter en Phase B au lieu d'attendre le LPSY |
| Sources | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Fraser, Unfriendly Skies (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-06-the-unfriendly-skies/) · [Fraser, Just Another Phase (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-just-another-phase/) · [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/) |

#### 5.6 🔴 FTI (chute à travers la glace) et 🔵 retour sous la glace

| Rubrique | Contenu |
|---|---|
| Labels (qui dit quoi) | Pruden (tradition Evans) : « falling through the ice » = **la cassure** ; « The ice… is an analogy to a wavy line of support drawn loosely under reaction lows » · SMI : « The ICE is the FORMER SUPPORT AREA at the BOTTOM of the T/R which BECOMES a SUPPLY AREA » · Villahermosa : étiquette **le retest** « LPSY o Fall Through the Ice (FTI) », d'où un **conflit de vocabulaire** · Villahermosa : « Major Sign of Weakness (MSOW) » pour la cassure de l'ICE. **Choix du mémo** : FTI = la cassure ; « retour sous la glace » = son test |
| Question posée par le CO | Cassure : « Le support cède-t-il sous l'offre ? » Retest : « Le support cassé est-il devenu une résistance ? » |
| Enjeu (coût · information · risque) | **Information** : la conversion de polarité. **Risque** : un spring (le scout regagne la glace) |
| Lieu et moment | Fin de Phase D / début de Phase E ; le retour suit la cassure (Fraser : « if ICE or Support is broken there is typically a pause », [Fraser, Short Term View (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-01-enjoying-the-short-term-view)) |
| Signature valide | **FTI** : « extremely wide price spread and the enormous increase in volume » (cas Nokia, [Pruden](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) [D] ; `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≤ 0.4` [H]. **Retour** : « a rally attempt is thwarted at the ice's surface (now resistance) » [D] ; « tested with a rally that fails at or near support » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) [D] ; spread étroit, volume en général réduit [D] |
| Ce que fait le CO (réussi · raté · ambigu) et traces | **Réussi** : « if price becomes listless and cannot lift (and stays under Support) expect a markdown to follow » (Fraser). **Raté** : « The Boy Scout has two chances to get back above the ice (i.e., creating a bullish "Spring" situation) » ; s'il échoue deux fois, « he would be most likely to sink downward and drown » (Pruden). **Ambigu** : première tentative ratée, attendre la seconde |

**Vérification pratique**

- [ ] **[D]** Cassure de la glace sur spread et volume en expansion.
- [ ] **[H]** `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≤ 0.4`, clôture < low de la plage.
- [ ] **[D]** Rallye de retour sur spread étroit qui échoue sous la glace.
- [ ] **[D]** Compter les tentatives de reprise : deux échecs = markdown probable.
- [ ] **[D]** Pas de clôture durable au-dessus de la glace.

| Rubrique | Contenu |
|---|---|
| Overlay crypto (volume → OI coin → tierces) | ① FTI volumique, retour sec. ② FTI avec OI coin ↑ : de nouveaux shorts, version forte [I] ; FTI avec OI coin ↓ et liquidations de longs : cascade de liquidations, version plus faible qui exige un retest ([Osler](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf) ; [Brunnermeier & Pedersen](https://www.princeton.edu/~markus/research/papers/predatory_trading.htm)). ③ Retour : funding négatif, ratio L/S, liquidations faibles. **Synthèse** : OI↑ à la cassure puis OI plat sur un retour sec = l'offre tient le niveau |
| Invalidation | Le prix reprend la 🟦 glace et y tient (scénario spring) |
| Implication de trading | « This also represents a high-probability opportunity to sell short » (StockCharts/WA, à propos du test de la cassure). **Entrée short** : sur l'échec sous la glace. **Stop** : au-dessus du high du retour et de 🟥 la glace (support devenu résistance). **Objectif** : 🟥 décompte P&F baissier ; R:R ≥ 3 ; stop suiveur ensuite (« Traders who have taken short positions can trail their stops as price declines ») |
| Erreurs fréquentes | Vendre la barre de cassure au lieu du retest ; mélanger les deux sens de « FTI » |
| Sources | [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/) · [Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/) · [Fraser, Short Term View (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-01-enjoying-the-short-term-view) |

## 6. Distinctions rigoureuses : même geste, lieu différent, sens différent

### 6.1 ST, test du spring, LPS de Phase C, LPS de Phase D et BU/BUEC ne testent pas la même chose

| Critère | 🔵 ST (Phase A) | 🟣 Test du spring | 🟣 LPS de Phase C | 🔵 LPS de Phase D (dans la plage) | 🔵 BU / BUEC |
|---|---|---|---|---|---|
| **Moment** | après SC et AR | après le spring (1–2 barres à plusieurs semaines) | fin de B / C, sans spring | après un SOS mineur, **avant** le JAC | **juste après** le JAC (D → E) |
| **Position** | zone du low du SC | zone du low du spring, creux plus haut | creux plus haut que SC/ST, dans la plage | dans la plage, au-dessus du LPS précédent | **au-dessus** de la plage, sur le creek touché par le dessus |
| **Action de référence** (volume à battre) | SC | spring | dernier creux volumique | SOS précédent | JAC |
| **Ce qui est testé** | l'offre résiduelle de la panique | l'offre délogée par le spring | l'offre sans percer le support | la demande qui revient plus haut | le **changement de polarité** (résistance → support) |
| **Nombre** | un ou plusieurs | un ; plusieurs après un #1 | un | plusieurs, en escalier | un, parfois deux (« SOS 2 / BUEC 2 », Fraser) |
| **Invalidation** | clôture sous le SC en expansion | low du spring cassé sur volume | creux précédents cassés | low du LPS précédent cassé | clôture dans la plage (école stricte) ; sous le spring (école tolérante) |
| **Entrée doctrinale** | aucune (« not operationally useful », Villahermosa) | oui : « better » que le shakeout (Pruden) ; « best buy point » (Fraser) | oui (Fraser) | oui : « excellent places to initiate or add » (WA) | oui : « safe » (Pruden, Nokia) |
| **Labels** | ST ; *secondary reaction* (Wyckoff) | Test (WA) ; *secondary test* (SMI, Pruden) ; LPS type 1 (Villahermosa) | LPS (Fraser ; schéma #2 de WA) | LPS (WA, Pruden) ; « LPS dentro del rango » (Villahermosa) | BU (WA) ; BUEC (Pruden, Fraser) ; = LPS (Fraser 2015, Villahermosa) ; « second springboard position » (Wyckoff) |

Sources : [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Fraser, Jumping the Creek (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-jumping-the-creek/) · [Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/) · [Villahermosa, LPS](https://tradingwyckoff.com/last-point-of-support/) · [Cours §11M, §16M](https://archive.org/details/WyckoffMethodOfTapeReading).

> **À retenir** — Fraser résume les quatre premiers : « An LPS or a Spring are doing the same type of work; which is to test a prior high volume price low » ([Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/)). Seul le BU teste autre chose : **l'absence d'offre au-dessus** et la conversion résistance → support (« Old Resistance becomes new Support », [Fraser, Reaccumulation Roundup (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-reaccumulation-roundup/)). La règle du projet « LPS ≠ BUEC » est une **convention opérationnelle utile** : chez StockCharts/WA et Pruden, le low du BU **est** un LPS (« Back Up (BU) to a Last Point of Support »).

### 6.2 Spring, shakeout et terminal shakeout : le lieu et l'intensité font la différence

| Concept | Définition (source) | Contexte | Profondeur · volume | Test requis | Achat de la barre ? |
|---|---|---|---|---|---|
| **Spring #3** | « No INCREASE in SUPPLY can COME OUT on the DRIVE into NEW LOW GROUND » ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/)) | fin de plage d'accumulation | faible · sec | non (« not uncommon ») | oui (Fraser, SMI) |
| **Spring #2** | « SUPPLY is not absent, it is NOT OVERWHELMINGLY ABUNDANT » (SMI) | fin de plage | modérée · en expansion | oui | non, ou partiel (SMI) ; acheter le test |
| **Spring #1 = shakeout** | « The #1 Spring is a shakeout » ([SMI (O'Brien), #3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/)) ; « Spring #1 o Terminal Shakeout » ([Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)) | fin de plage | profonde · fort | oui, parfois plusieurs | **divergence** : Pruden oui (point 8), SMI après test, Fraser jamais |
| **Terminal shake-out** (Wyckoff) | « a rapid or precipitous downward movement, occurring at or near the end of a period of preparation for an advance » ([§21M, ©1932](https://archive.org/details/WyckoffMethodOfTapeReading)) | fin de **longue** préparation | plus profond qu'un spring (SMI : « how far it penetrates ») · fort | oui (SMI) | voir #1 |
| **Shakeout ordinaire** | « a sharp DOWNWARD THRUST occurring in an UPWARD TREND without extensive previous preparation » (SMI) ; « la principal diferencia, la localización » (Villahermosa) | réaccumulation, tendance haussière | variable · « alto, medio o bajo » | oui s'il y a de l'offre sur la barre (SMI) | après test |
| **Shake-out VSA** | « wide spread down, which then reverses to close on the highs, accompanied by high volume » ([MTM p.167](https://www.tradeguider.com/mtm_251058.pdf)) | partout | large · fort | « may need to be re-tested » (TG) | — |
| **SC** (comparaison) | même allure qu'un shake-out, mais « on a selling climax you will have a Bear Market behind you » (MTM p.96) | fin de tendance baissière | — | ST | non |

> **Piège** — La même barre profonde et volumique s'appelle « #1 », « shakeout » ou « terminal shakeout » selon l'auteur. Le glossaire SMI fait du terminal shake-out le **concept parent** du spring, quand O'Brien et Villahermosa en font le **type #1**. Le mécanisme est le même ; on retient le comportement (profondeur × volume × vitesse de réintégration).

### 6.3 JAC/SOS contre UTAD/upthrust : la barre de cassure ne tranche pas, la suite tranche

| Critère | 🟢 JAC / SOS majeur | 🟠 UTAD / upthrust |
|---|---|---|
| Contexte HTF | tendance haussière, ou bas de cycle avec accumulation **gagnée** | tendance haussière mûre (distribution) ou downtrend (redistribution, défaut du projet) |
| Séquence | après le test de Phase C et des LPS | après Phases A et B ; UT en Phase B, UTAD en fin de plage |
| Barre de cassure | spread qui s'élargit, volume en expansion, clôture près du haut | volume ↑ avec spread qui se **resserre** (effort sans résultat, SMI/Pruden), ou volume faible sans suivi ; clôture faible |
| Acceptation | plusieurs clôtures au-dessus du creek | réintégration rapide (« will not linger ») |
| Repli suivant | BU sec et étroit qui tient le creek | repli large et volumique qui réintègre ; retour vers la moyenne des clôtures |
| OI coin [I] | ↑ avec le prix (longs neufs) ; ↓ = squeeze plus fragile | ↑ sur la percée puis réintégration = longs piégés |
| Tierces [I] | funding contenu, shorts liquidés | funding qui saute, shorts liquidés sur la mèche, puis longs liquidés |
| Verdict | **après** le BU (règle CLAUDE.md n°3) | **après** la réintégration ou la cassure du milieu de plage |

Sources : [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [Fraser, Jumping the Creek. A Review (2018)](https://articles.stockcharts.com/article/articles-wyckoff-2018-04-jumping-the-creek-a-review/) · [Villahermosa, SOS](https://tradingwyckoff.com/en/sign-of-strength/) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial).

### 6.4 LPSY contre test de l'UTAD

| Critère | 🔵 LPSY | 🟣 Test de l'UTAD |
|---|---|---|
| Moment | après un SOW (Phase D, E) | après l'UTAD (fin de Phase C) |
| Lieu | sous la glace cassée ou sous une résistance interne | vers la zone de l'UTAD, au-dessus ou près du BC |
| Volume | « light or heavy » (Pruden) | < UTAD, par miroir [I] |
| Sommet | plus bas que le rallye précédent | plus bas que l'UTAD |
| Nombre | plusieurs (points 11, 13, 15, 17) | un |
| Labels | LPSY (WA, Pruden, Fraser) ; FTI pour le retest (Villahermosa) | « Test » (Fraser) ; LPSY type 1 (Villahermosa) |
| Entrée short | « excellent opportunities » (WA) ; mieux encore sur le rallye qui teste le point 11 (Pruden) | entrée plus serrée sous l'UTAD |

### 6.5 Barre de test, no supply et ST wyckoffien

| Critère | 🔵 Barre de test (VSA) | 🔵 No supply (VSA) | 🔵 ST / test wyckoffien |
|---|---|---|---|
| Nature | geste **provoqué** (marquage pour faire sortir les vendeurs) | état **passif** (personne ne vend) | événement **structurel** (Phases A–C) |
| Lieu | zone de fort volume antérieure | n'importe où, de préférence en tendance haussière | zone de l'action testée (SC, spring) |
| Forme | mèche basse, clôture milieu/haut ; nouveau plus-bas = bonus | barre baissière, spread étroit | swing de retour, souvent plusieurs barres |
| Volume | faible vs zone testée (« can be high in the futures market ») | < deux barres précédentes | < action testée, en baisse d'un test à l'autre |
| Spread | pas d'exigence ; étroit = « less impact » | étroit | étroit à l'échelle du swing |
| Confirmation | barre suivante haussière ; 2–3 barres maximum | barre suivante haussière | réponse + séquence (SOS) |
| Sources | [MTM p.34–35](https://www.tradeguider.com/mtm_251058.pdf) ; [SOS 11](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf) ; [Coulling](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page45.html) | [MTM p.19](https://www.tradeguider.com/mtm_251058.pdf) ; SOS 199 | [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) ; [SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/) |

### 6.6 Où les sources divergent, et ce que le mémo retient

| Sujet | Positions (qui → quoi) | Choix du mémo |
|---|---|---|
| **Numérotation des springs** | SMI (glossaire, O'Brien), Fraser, Villahermosa 2018 : #1 lourd → #3 léger. Pruden 2006 : gradation sans numéros. Pruden 2007 : non vérifié. Aucune inversion trouvée | Numérotation SMI partout |
| **Acheter le shakeout / #1** | Pruden : « first prescribed place » (point 8), le test « better ». SMI : « extremely risky », attendre le test. Fraser : « It should not be bought » | Entrée sur le test seulement |
| **Poids du volume dans le spring** | SMI, Fraser, Pruden : le volume est l'arbitre. Villahermosa 2026 : « Volume is a secondary piece of data » [NV, extrait], alors que son article de 2018 est centré sur le volume. WA (algorithmes) : « Effective springs typically show volume coming in » | Volume d'abord, puis vitesse de réintégration |
| **ST sous le low du SC** | WA : « generally stopping at or above » ; dessous = « new lows or prolonged consolidation ». Fraser : « above, at, or below … and still be successful ». Villahermosa : dessous = déséquilibre vendeur. Schéma #1 : ST in Phase B sous le SC | Qualité moindre, jamais « spring » |
| **Volume au ST du BC** | WA, Pruden, S&C 2014 : en baisse. Fraser : « high volume and reversal price bars » | Baisse à l'approche, volume sur le retournement [I] |
| **Volume des ST de Phase B** | WA : ST « significantly diminished », mais début de Phase B « accompanied by high volume ». Fraser : « typically have high volume » | Lire la pente, pas la barre |
| **Phase A climactique ?** | WA, Pruden : pas forcément. Villahermosa : « some type of climactic volume ». FAQ du site : « 4 mandatory sequential events » | Pas obligatoire ; pas de « ST » sans arrêt |
| **Labels de Phase B** | WA : « ST in Phase B » et « upthrust-type actions » sans label. Villahermosa : UA/UT, ST as SOW/mSOW, mSOS. Fraser : UT en accumulation. Rutigliano (WA crypto) : UA | Étiquettes conditionnelles, biais affiché |
| **LPS dans ou hors de la plage** | WA, Pruden : creux d'une réaction après un SOS, y compris sur l'ancienne résistance. Fraser : LPS de Phase C, LPS après un SOS mineur, et « BUEC with a LPS ». Villahermosa : LPS « dentro » et « fuera del rango ». Fraser 2022 : BUEC peu profond vs LPS plus profond | LPS C / LPS D dans la plage / BU-LPS hors plage |
| **BU = LPS ?** | Pruden, WA : le BU est le mouvement **vers** un LPS. Fraser 2015, Villahermosa : synonymes. Fraser (2015-07) les liste comme deux étiquettes | BU = mouvement ; son low = LPS hors plage |
| **Profondeur du BU** | Stricte : Fraser 2018, Villahermosa. Tolérante : Fraser 2022, WA (« a new TR at a higher level »), Pruden (stop sous le spring) | Deux stops : serré (creek) ou structurel (spring) |
| **Volume du LPSY** | Pruden : « light or heavy ». WA : rallye « feeble » à spread étroit, sans critère de volume. Villahermosa : préfère un volume bas | Spread étroit + échec |
| **FTI = cassure ou retest** | Pruden : la cassure. Villahermosa : le retest | FTI = cassure |
| **Définition du test VSA** | Williams : lieu + clôture + volume relatif. TG : nouveau plus-bas = bonus, spread étroit = « less impact » ; le support de séminaire fusionne no supply, *test in a rising market* et règle des deux barres. Coulling : corps étroit + mèche profonde | Test ≠ no supply |
| **Test à fort volume** | Williams : raté, re-test (forme en W), sauf *bad news*/shakeout, *bull move*, **futures**. TG : « may need to be re-tested » | « À re-tester », OI coin en arbitre |
| **Test sans réponse** | Williams : *negative action*, faiblesse. Premier mémo et CLAUDE.md : « neutre » | Faiblesse (errata) |
| **Provenance du vocabulaire** | Weis : Wyckoff « never used such terminology » (springs, up-thrusts, ice lines). Pruden : annotations d'Evans, schémas de Forte (1994). Site Villahermosa : « what Wyckoff identified as Spring and Upthrust in the 1930s » [NV]. Or le cours emploie déjà *upthrust* (§21M p.2, page « Copyright 1932 by Richard D. Wyckoff », ré-estampillée en 1937) | Mécanisme wyckoffien ; « spring », « creek », « ice » post-Wyckoff ; « terminal shake-out » et « upthrust » dans le cours |
| **Neuf tests** | Cours 1937 (pages ©1937 Wyckoff Associates) : un ordre. Pruden 2007 / StockCharts : un autre ordre, PS + SC + ST fusionnés | Citer les deux (section 7.5) |
| **Règle des 3:1** | Cours 1937 §20M p.2 ; Pruden 2007 (test n°9) ; SMI : « At least three points of potential profit should be indicated for each point that is risked » | R:R ≥ 3 avant l'entrée |
| **Evans** | SMI : direction à Robert Stanlaws après 1934, rachat de l'Institut par Evans en 1951. Pruden : Evans « carried on the teaching … after the death of Mr. Wyckoff in 1934 ». StockCharts : enseignant phare « from the 1930s to the 1960s ». Dates 1904–1976 : une seule source [NV] | Rôle certain ; dates non confirmées |

Sources principales : [SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [SMI, histoire](https://wyckoffsmi.com/history-of-wyckoff-stock-market-institute/) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Fraser, Action – Test (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test) · [Fraser, Stocks at a Crossroad (2022)](https://articles.stockcharts.com/article/articles-wyckoff-2022-08-stocks-at-a-crossroad-891) · [Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/) · [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf) · [Weis](https://content.e-bookshelf.de/media/reading/L-802008-2fe9f872b5.pdf) · [MTM](https://www.tradeguider.com/mtm_251058.pdf) · [Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf) · [Cours 1937](https://archive.org/details/WyckoffMethodOfTapeReading) · [readtheticker](https://www.readtheticker.com/Pages/IndLibrary.aspx?65tf=1555_bob-evans-renowned-wyckoff-teacher) [NV].

## 7. Diagnostic de l'état d'une consolidation : quels tests ont eu lieu, comment ils se sont comportés, ce qui manque encore

### 7.1 Arbre de décision : chaque étape est une porte gardée par un test

| # | Question (dans l'ordre) | Si OUI | Si NON | Overlay crypto à cette étape |
|---|---|---|---|---|
| 0 | TF et structure déclarées ? Contexte HTF (Daily/H4) établi ? | passer à 1 | déclarer d'abord ; dans un downtrend, **redistribution par défaut** | — |
| 1 | Un arrêt est-il identifié (SC, ou Phase A non climactique) et l'AR a-t-il posé la borne haute ? | Phase A en cours | pas de plage : tendance | AR avec OI coin ↓ (short covering) |
| 2 | Le ST est-il moins volumique et moins large que le SC, creux ≥ low du SC ? | plage posée, Phase B | « new lows or prolonged consolidation » ; décompte P&F à partir du ST | OI coin plat/↓ au ST |
| 3 | Le volume des creux successifs baisse-t-il (gradient négatif) ? Les rallyes deviennent-ils plus faciles ? | absorption en progrès | Phase B qui s'allonge, ou redistribution | OI qui se dégonfle de test en test |
| 4 | La Phase B dure-t-elle au moins autant que la Phase A ? | une Phase C devient crédible | spring « prématuré » probable | — |
| 5 | Un test de Phase C a-t-il eu lieu (spring #1/#2/#3 ou LPS C) ? De quel type ? | exigence de test selon le type (§3.5–3.9) | attendre ; ne rien anticiper | profil de liquidations au spring |
| 6 | Le test du spring est-il sec (< spring), à creux plus haut, avec une réponse en 1–3 barres ? | **springboard** (cause prête) | re-test ; ou ré-étiquetage en Phase B | OI coin plat, liquidations ≈ 0 |
| 7 | Un SOS/JAC avec expansion et clôture haute au-dessus du creek ? | tentative de sortie, attendre le BU | SOS mineur → LPS ; ou UT ? | OI coin ↑ avec le prix, funding contenu |
| 8 | Le BU est-il sec et tient-il le creek ? | Phase E (markup) | UT/UTAD → scénario redistribution | OI stable, funding qui refroidit |

Sources : [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) · [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/) · [Fraser, Segmenting PnF Counts (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-05-segmenting-pnf-counts/).

### 7.2 Grille de maturité : du bruit au springboard

| Critère | Immature | En maturation | Mûr (« on the springboard ») | En sortie |
|---|---|---|---|---|
| Séquence accomplie | SC/AR seulement | ST + plusieurs ST in B | test de Phase C réussi | SOS/JAC + BU |
| Gradient de volume des creux | volumique, erratique | en baisse | test plus sec que le spring | — |
| Ratio vol(dernier test) / vol(SC) [H] | > 1 | entre 1 et 0,5 | < 0,5 | — |
| Amplitude des oscillations | larges | qui se resserrent | contraction (*hinge*, apex) | expansion haussière |
| Durée Phase B / Phase A | < 1 | ≈ 1 | ≥ 1 | — |
| *Activity bullish* (vol. rallyes / vol. réactions) [I] | < 1 | ≈ 1 | > 1 | > 1 et croissant |
| Réponse aux tests | absente | lente | 1–3 barres | immédiate |
| OI coin sur les tests [I] | ↑ (shorts qui s'ouvrent) | plat | plat/↓ (débouclage) | ↑ avec le prix |

Repères doctrinaux : « Early on in Phase B, the price swings tend to be wide and accompanied by high volume. As the professionals absorb the supply, however, the volume on downswings within the TR tends to diminish » ([StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) ; le dégradé de creux montants : « fewer and fewer sellers remain to propel stocks downward in price. As a consequence, the downwaves become shorter and shorter in length (the bottoms rise) » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) ; la contraction avant le départ : « the stock develops a perfect apex (note how the price movement and volume have narrowed into extreme dullness) » ([Cours §20M p.3](https://archive.org/details/WyckoffMethodOfTapeReading)) ; « Jumping out of a Hinge can result in a robust price move (up or down) » ([Fraser, Three Legged Stool (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-02-three-legged-stool)) ; « The bigger the magnitude of the prior trend, the more times it may need to be Tested before it can be reversed » ([Fraser, Action – Test (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)). Aucune source ne chiffre la baisse de volume d'un test à l'autre ni la durée en barres : les colonnes chiffrées sont des repères [H].

> **À retenir** — La maturité est un **gradient**, pas un événement : une suite de retours sur la même zone à volume décroissant (par exemple ×3 → ×1,5 → ×0,6, valeurs illustratives [H]) est la meilleure preuve de transfert. TradeGuider le dit à l'échelle de deux barres : « Give extra weight to a second test in a bullish phase if the second test has lower volume than the first » ([Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)).

### 7.3 Accumulation ou redistribution : tenir les deux scénarios jusqu'à la sortie

| Indice observé | Favorise l'accumulation | Favorise la redistribution | Source |
|---|---|---|---|
| Contexte HTF | bas de cycle après une baisse **prolongée** avec climax | plage **dans** un downtrend (défaut du projet) | CLAUDE.md ; [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) |
| Phase A | SC, AR, ST nets | même allure (« Phase A may look more like the start of an accumulation TR ») | StockCharts/WA |
| Volume des baisses | décroissant d'un passage à l'autre | « stays heavy on the way down and often grows as the range gets older » | [WA 2026](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/) |
| Test de la borne haute en B | UA à réintégration rapide, ou mSOS | UT suivi d'un SOW volumique sous l'AR | [Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/) ; [Fraser, Just Another Phase (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-09-just-another-phase/) |
| Creux plus bas en B | sans suivi, re-testé plus sec | volumique, suivi (ST as SOW / mSOW) | Villahermosa |
| Rallyes | volume ↑ sur les hausses (*activity bullish*) | volume ↑ sur les baisses (*activity bearish*) | tests d'achat/de vente |
| Phase C | spring + test sec | UTAD, ou UT d'un sommet plus bas | StockCharts/WA |
| Sortie | JAC + BU sec qui tient | SOW + LPSY ; ou JAC qui réintègre (UTAD) | Pruden |
| OI coin [I] | ↓ sur les tests, ↑ à la sortie | ↑ à la résistance avec funding élevé (demande qui se fait piéger) | règle CLAUDE.md n°4 |

> **Penser comme le CO** — « until the price leaves the range we cannot know what the real intention was behind the cause being built » ([Villahermosa, ST](https://tradingwyckoff.com/en/secondary-test/)). Fraser ajoute : « We must continually be ready to update our scenarios and labeling » ([Fraser, Phase Analysis (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-08-phase-analysis-two-case-studies/)). Dès que le prix fait l'inattendu (un aller-retour, un « test » volumique), on re-questionne le cadre au lieu de plaquer l'étiquette prévue.

### 7.4 Emboîtement fractal : une structure entière sur H1 peut n'être qu'un test sur H4

| Sur H4 (contexte) | Sur H1 (structure locale) | Lecture |
|---|---|---|
| 🔵 ST in Phase B sur la borne basse | accumulation H1 complète (SC/AR/ST/spring/SOS locaux) | confluence haussière **locale**, la Phase B H4 continue |
| 🟠 UA/UT in B sur la borne haute | distribution H1 complète (BC/UT/SOW locaux) | le UT H4 s'exécute par une distribution H1 |
| 🟣 Test du spring H4 | LPS H1 qui tient | confluence maximale : entrée H1, contexte H4 |
| 🔵 BU H4 | réaccumulation H1 | le BU s'étire en *stepping stone* |

Fraser : « Wyckoff has a fractal quality, and thus, the Method essentially works in all timeframes » ([Fraser, Short Term View (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-01-enjoying-the-short-term-view)). Villahermosa : pour trader un extrême de Phase B, « if we are in the upper zone, we will look for a minor distribution structure; and if we are in the lower zone, we will look for a minor accumulation structure » ([ST](https://tradingwyckoff.com/en/secondary-test/)). Règle CLAUDE.md : on étiquette d'abord à l'échelle fixée par Gauthier ; la TF supérieure donne le biais sans écraser les étiquettes locales.

### 7.5 Les neuf tests d'achat et de vente : deux listes, deux ordres

La plus ancienne liste trouvée est dans le cours, **§20M p.1**, sur des pages portant seulement « Copyright 1937 by Wyckoff Associates, Inc. ». Elle est donc **posthume** ; sa présence dans l'édition 1931–33 n'est pas vérifiée. La version répandue (StockCharts/WA, « Adapted from Pruden H (2007) The Three Skills of Top Trading … pp. 136-37 ») **réordonne** les tests d'achat et ajoute SC et ST au test « Preliminary support ».

| # | Achat — Cours 1937 (§20M) | Achat — Pruden 2007 / StockCharts | Vente — Cours 1937 | Vente — Pruden 2007 / StockCharts |
|---|---|---|---|---|
| 1 | Objective Accomplished on Down Side (Figure Chart) | Downside price objective accomplished (P&F) | Objective Accomplished on Up Side | Upside objective accomplished |
| 2 | Activity Bullish — volume increasing normally on rallies and decreasing on reactions | **Preliminary support, selling climax, secondary test** | Activity Bearish — volume increasing normally on reactions and decreasing on rallies | Activity bearish |
| 3 | Preliminary Support | Activity bullish | Preliminary Supply | **Preliminary supply, buying climax** |
| 4 | Stronger Than Market — responsive to rallies and resistant to reactions | Downward stride broken | Weaker Than Market — responsive to reactions and sluggish on rallies | Stock weaker than the market |
| 5 | Downward Stride Broken, i.e., supply lines penetrated | Higher lows | Upward Stride Broken, i.e., support lines violated | Upward stride broken |
| 6 | Higher Supports | Higher highs | Lower Tops | Lower highs |
| 7 | Higher Tops | **Stock stronger than the market** | Lower Supports | Lower lows |
| 8 | Base Forming (Figure Chart) | Base forming (horizontal price line) | Crown Forming (lateral movement) | Crown forming (lateral movement) |
| 9 | Estimated Probable Profit Exceeds Indicated Probable Risk | Upside profit potential ≥ 3× the loss if the initial stop-loss were hit | Estimated Probable Profits Exceed Indicated Risk | ≥ 3× the risk |

Sources : [Cours 1937 §20M](https://archive.org/details/WyckoffMethodOfTapeReading) · [StockCharts/WA](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial) · [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf).

| Usage des neuf tests | Détail |
|---|---|
| **Rôle** | « These buying and selling tests outline in a general way the successive steps to be taken when determining the most advantageous buying and selling points » ([§20M p.1](https://archive.org/details/WyckoffMethodOfTapeReading)) ; pour StockCharts, « the nine tests define the line of least resistance in the market » |
| **Règle des 3:1** | « always make sure that the estimated probable profit as determined by the figure chart objective, is at least three times the risk involved in employing a properly placed stop » ([§20M p.2](https://archive.org/details/WyckoffMethodOfTapeReading)) |
| **Ce qu'ils testent** | un **faisceau** (prix, structure, cause P&F, force relative), jamais un signal isolé ; seuls les tests 1 et 9 exigent le P&F (StockCharts) |
| **Adaptation crypto** [I] | test « plus fort que le marché » : BTC vs capitalisation totale, une altcoin vs BTC ; test 8 : P&F à case en % ou en ATR |
| **Asymétrie** | dans la liste Pruden/StockCharts, l'ordre de vente n'est pas le miroir de l'ordre d'achat, signe d'un glissement éditorial plutôt que d'une doctrine [I] |

## 8. Playbook de trading : acheter le test, pas l'événement

**Aide à la décision uniquement — jamais d'exécution automatique.** Les niveaux sont génériques : en situation réelle, chaque prix cité doit porter entre parenthèses l'événement ou la borne qui le définit (convention CLAUDE.md).

### 8.1 Règles communes à tous les montages

| Règle | Contenu | Source |
|---|---|---|
| Ne pas acheter la cassure | « The Wyckoff method instructs you to buy after a backup following an upward jump (a sign of strength) or to sell short after a backup following a downward jump (a sign of weakness) » | [Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) |
| Quatre points d'entrée | « 1) Spring and Test of the Spring, 2) Last Point of Support (there are often multiple LPS points), » 3) BU après la sortie, 4) « Breakout above the high of the BU/SOS » | [Fraser, Best Trade Entry Points (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/) |
| Stops | « Stop placement can go just below the Spring, LPS, or BU » ; dans « a zone that has a very low potential for being triggered » | Fraser 2016a |
| R:R ≥ 3 avant l'entrée | test d'achat n°9 ; « At least three points of potential profit should be indicated for each point that is risked » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) ; à vérifier sur le **premier objectif conservateur** [I] | Cours §20M p.2 ; Pruden 2007 |
| Objectif P&F | compter depuis le LPS, de droite à gauche ; « Never add only part of a P&F phase to your count » ; ajouter le décompte au low de la plage **et** au point médian ; objectifs = zones « stop, look and listen » | [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) |
| Case P&F en crypto | échelle en % (Rutigliano, BTC à 10 % pour 2013–2018) ou en ATR (Fraser : « 5-box reversal PnF chart using ATR (20) scaling ») ; à calibrer en H1/H4 [I] | [Rutigliano, WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf) ; [Fraser, Three Legged Stool (2017)](https://articles.stockcharts.com/article/articles-wyckoff-2017-02-three-legged-stool) |
| Construction | « usually occurs in three tranches » ; « Each purchase or tranche of stock must be at a higher price than the prior purchase » ; « Only average up a winning position » | Fraser 2016a |
| Pyramide | ajouter seulement si les positions initiales sont en gain | Pruden 2006 |
| Plan de Villahermosa | stop d'invalidation de scénario (« below the low of the Spring in a buy, above the high of the UTAD in a sell ») ; objectif minimal = hauteur de la plage ; demi-sortie à la première zone de liquidité, stop au point mort à 50 % du chemin ; « The structure defines the ratio, never the other way around » | [Villahermosa, guide](https://tradingwyckoff.com/en/wyckoff-method/) |

> **Piège** — La configuration de backtest du dépôt (`stop_atr: 1.0`, `rr: 2.0`, entrée sur déclencheur frais) ressemble au seul backtest public trouvé d'un spring **seul** : 41,26 % de gains, −0,13 R en moyenne ([papan-saham](https://github.com/augustgerry/papan-saham/pull/89), [NV]). Si ce résultat se confirme, il plaide pour déclencher sur le **test** et le **LPS** plutôt que sur l'événement, comme Fraser et Pruden. C'est une hypothèse à vérifier dans `screener/optimize.py` (walk-forward), pas une conclusion.

### 8.2 Montages par setup

**🟣 Spring #3 (achat direct)**

| Élément | Contenu |
|---|---|
| Contexte requis | Phase B mûre ; contexte HTF non baissier, ou accumulation gagnée ; pas d'heure creuse |
| Déclencheur | réintégration de la plage sur volume sec, puis première barre de demande |
| Entrée | clôture de la barre de demande |
| Stop | sous 🟪 le low du spring (poche de stops consommée ; y revenir en clôture = offre réelle) |
| Objectif | 🟦 high de l'AR / creek (borne haute de la plage), puis 🟩 décompte P&F depuis le LPS |
| Invalidation | clôture sous le low du spring sur volume en hausse |
| Overlay crypto | OI coin plat, liquidations ≈ 0 ; si OI↑ sur la percée : shorts piégés (carburant) |

**🟣 Test du spring (#2, ou #1 après test)**

| Élément | Contenu |
|---|---|
| Contexte requis | spring #2 ou #1 identifié ; Phase B mûre |
| Déclencheur | test à volume < spring, creux plus haut, puis barre de demande dans 1–3 barres |
| Entrée | ordre stop au-dessus du high de la barre de test (TG), ou clôture de la barre de demande |
| Stop | sous 🟪 le low du spring (« specific low risk stop or danger point », Pruden) |
| Objectif | 🟦 creek, puis 🟩 décompte P&F ; R:R ≥ 3 sur le premier objectif |
| Invalidation | creux plus bas **et** volume plus fort (grade D) ; pas de réponse en 3 barres |
| Overlay crypto | OI coin plat ou ↓, funding neutre ; OI↑ + L/S↓ = vendeurs qui se construisent, attendre |

**🔵 LPS (de Phase C ou de Phase D, dans la plage)**

| Élément | Contenu |
|---|---|
| Contexte requis | test de Phase C passé (ou LPS C), SOS en amont |
| Déclencheur | repli sec à creux plus haut, puis barre de demande |
| Entrée | « buy any of the early demand bars as the price turns up » (Fraser) |
| Stop | sous 🔵 le low du LPS (dernier creux défendu) ou sous le low précédent |
| Objectif | 🟩 décompte P&F compté **depuis ce LPS** (plus conservateur d'abord) ; 🟦 creek en premier relais |
| Invalidation | cassure du low du LPS précédent ; pic de volume sur le LPS |
| Overlay crypto | OI stable ou légère baisse ; funding qui refroidit |

**🔵 BU / BUEC (le setup « safe » de Pruden)**

| Élément | Contenu |
|---|---|
| Contexte requis | JAC avec expansion et clôture haute au-dessus du creek |
| Déclencheur | BU sec et étroit sur le creek, puis barre de demande |
| Entrée | dans la force des barres de demande (Fraser 2018) |
| Stop | serré : sous 🔵 le low du BU **et** 🟦 le creek (une réintégration invalide le JAC) ; structurel : sous 🟪 le low du spring (Pruden, Nokia) |
| Objectif | 🟩 décompte P&F depuis le LPS ; « stop, look and listen » aux objectifs |
| Invalidation | clôture dans la plage sur spread large et volume fort |
| Overlay crypto | OI stable, funding qui se normalise, pas de liquidations |

**🟢 JAC / SOS majeur (pas d'entrée sur la barre)**

| Élément | Contenu |
|---|---|
| Contexte requis | séquence C → D accomplie |
| Déclencheur | aucun sur la cassure ; on attend le BU, ou la cassure du high du BU/SOS (4ᵉ entrée de Fraser) |
| Entrée | au-dessus du high du BU/SOS, **après** le BU |
| Stop | sous 🔵 le low du BU (le test qui a validé le saut) |
| Objectif | 🟩 décompte P&F |
| Invalidation | réintégration de la plage |
| Overlay crypto | OI coin ↑ avec le prix = version forte ; OI coin ↓ = squeeze, BU indispensable |

**🟠 UTAD (short, miroir du spring)**

| Élément | Contenu |
|---|---|
| Contexte requis | Phases A et B accomplies ; contexte HTF baissier ou tendance haussière mûre |
| Déclencheur | réintégration après la percée ; mieux : test de l'UTAD à sommet plus bas, sec |
| Entrée | sous le low de la barre de rejet |
| Stop | au-dessus de 🟧 le high de l'UTAD (extrême du piège) |
| Objectif | 🟦 low de l'AR (borne basse), puis 🟥 décompte P&F baissier |
| Invalidation | clôture au-dessus du high de l'UTAD et tenue (JAC de réaccumulation) |
| Overlay crypto | OI↑ + funding en hausse + shorts liquidés sur la percée, puis réintégration = longs piégés |

**🔵 LPSY / retour sous la glace (short, miroir du BU)**

| Élément | Contenu |
|---|---|
| Contexte requis | SOW, ou FTI à travers la glace |
| Déclencheur | rallye à spread étroit qui échoue sous la glace ou sous une résistance interne |
| Entrée | sur la barre de rejet ; Pruden : « even better » sur le rallye qui teste le point 11 |
| Stop | au-dessus du high du LPSY **et** de 🟥 la glace cassée (support devenu résistance) |
| Objectif | 🟥 décompte P&F baissier ; stop suiveur ensuite |
| Invalidation | reprise de la glace et tenue (deux échecs = markdown ; une reprise = scénario spring) |
| Overlay crypto | rallye avec OI ↓ (rachats sans demande), ou OI ↑ + L/S ↑ + funding ↑ (longs piégés) |

## 9. Seuils du screener et écarts doctrine ↔ code (constat, sans modification du code)

### 9.1 Les sept seuils sont des heuristiques ; aucune source primaire ne les chiffre

| Seuil (`config.yaml`) | Valeur | Où le code l'applique | Ce qu'il traduit | Ancrage dans les sources |
|---|---|---|---|---|
| `climax_vol` | ×2.0 | `events.py` SC/BC (l.97, l.104) ; `window.py` climax à **0,75 × 2,0 = ×1,5** (l.215) | « ultra high », « exceptionally high » (Williams) | qualitatif ; ProRealCode : SC > ×2,4, BC > ×3,0 ([ProRealCode](https://www.prorealcode.com/prorealtime-indicators/wyckoff-event-detection/)) |
| `sos_vol` | ×1.3 | SOS/SOW (`events.py` l.111, l.117 ; `window.py` l.260) | « relatively higher volume » | qualitatif ; scripts : ×1,2 à ×2,0 |
| `wide_spread_atr` | 1.3 ATR | SC/BC/SOS/SOW ; **aussi plafond de spread du ST** (`events.py` l.125, l.128 ; `window.py` l.273) | « wide spread » | qualitatif |
| `narrow_spread_atr` | 0.7 ATR | **aucun détecteur** ; seulement affiché dans le mémo théorie (`theory_table.py` l.180) et accepté comme clé de grille par `optimize.py` (l.34), sans effet sur la détection | « narrowing spread » | qualitatif ; FAQ Villahermosa 50–70 % (non doctrinal) |
| `test_vol` | ×0.85 | ST (`events.py` l.125) ; ST à **×0,98** (0,85 × 1,15, `window.py` l.273) ; LPS à **×1,1** (0,85 × 1,3, l.313) ; LPS/LPSY (`events.py` l.138, l.144) | « diminished volume » | la doctrine compare à l'**action testée**, pas à la MA |
| `pen_atr` | 0.1 ATR | SPRING/UTAD (`events.py` l.80, l.89 ; `window.py` l.291) | pénétration minimale | aucune profondeur chiffrée ; WA : un écart > 10 % entre creux est « unacceptable » ([WA](https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/)) |
| `reclaim_clv` | 0.5 | SC/BC (`events.py` l.98, l.105) ; **pas** le spring de `events.py` ; `window.py` code 0,5 en dur (l.287) | « close in the middle or high » | Williams ; WA : un spring peut clôturer sous 50 % de sa barre, mais pas au plus bas |

CLV = (C−L)/(H−L) (`features.py` l.43). `vol_ratio` = volume / moyenne mobile 20 barres **qui inclut la barre courante** (`features.py` l.45–46), ce qui comprime les ratios : une barre à 2× la moyenne des 19 précédentes s'affiche ≈ ×1,9 [H, calcul].

### 9.2 Écarts entre la doctrine et le code actuel

| # | Fichier : lignes | Code actuel | Doctrine | Conséquence | Piste (non appliquée) |
|---|---|---|---|---|---|
| 1 | `events.py` l.125, l.128 ; `window.py` l.273 ; `window.py` l.72–74 ; `theory_table.py` l.83 | le ST accepte un spread jusqu'à 1,3 ATR ; le texte théorique l'appelle « spread ÉTROIT (< 1.3 ATR) » | « narrowing of spread » (WA, Pruden, SMI) | `narrow_spread_atr` (0.7) est mort ; une barre de 1,2 ATR passe pour « étroite » | appliquer `narrow_spread_atr` aux tests de swing ; harmoniser le texte |
| 2 | `events.py` l.122–130 ; `window.py` l.265–277 | volume du ST jugé contre la MA20 seule | vol(ST) < vol(SC) ; vol(test) < vol(spring) | un ST plus volumique que le SC reste possible si la MA est haute | afficher vol_test / vol_action et l'exiger < 1 |
| 3 | `events.py` l.9–11 | le docstring annonce « AR, ST, SPRING, TEST, SOS, LPS » | — | **aucun détecteur AR ni TEST** dans `events.py` | détecteur « test du spring » (+ test synthétique, convention du dépôt) |
| 4 | `events.py` l.79–86 ; `window.py` l.279–294 | type de spring non classé ; `vol_bonus = 0.6` si vol > climax ; `window.py` retient la pénétration **la plus profonde** | le type (#1/#2/#3) fixe l'exigence de test (SMI, Fraser) | un #1 (le plus risqué) est privilégié et traité comme déclencheur frais | classer #1/#2/#3 (volume d'abord) ; #1/#2 → « test requis » |
| 5 | `events.py` l.80 | spring = pénétration + clôture > support, **sans condition de CLV** | « reverses to close within the TR » ; pas de clôture au plus bas (WA) | spring à clôture faible accepté | appliquer `reclaim_clv` (lu depuis `Thresholds`, pas en dur) |
| 6 | `events.py` l.123–125 ; `window.py` l.272 | ST « près » du support (15 % de la hauteur), clôture ≥ support ; `window.py` tolère un sous-percement de 2 % de la plage | creux ≥ low testé = haute qualité ; plus bas + plus volumique = rejet (SMI) | grade A et grade B confondus | noter le grade A/B/C/D (§3.8) |
| 7 | `events.py` l.122–130 | toute barre sèche près du support dans les 5 dernières barres = « ST » | « as long as you have strength in the background » (Williams) ; cause en amont | test sans cause (condition n°1 de la grille) | exiger un climax/spring/SOS en amont |
| 8 | `events.py`, `window.py` | aucune confirmation par la réponse | réponse en 1–3 barres, sinon *negative action* (MTM p.35, p.152) | test sans réponse compté comme force | statut « possible » → « validé » après réponse |
| 9 | `events.py` l.110–114 | SOS = clôture > high de plage + volume + spread, étiqueté **ferme** sur la barre | « you should not buy breakouts » (Pruden) ; règle CLAUDE.md n°3 | un UTAD naissant est étiqueté SOS | étiquette « SOS ? / UTAD ? » jusqu'à tenue + BU |
| 10 | `window.py` l.250–263 | premier SOS = première barre volumique et large, **sans condition de franchissement** | SOS mineur ≠ JAC (Fraser, Villahermosa) | un mSOS ou un UA de Phase B peut être pris pour le JAC | distinguer mSOS (dans la plage) et JAC (clôture au-dessus du creek) |
| 11 | `events.py` l.134–140 | « LPS » = dernière barre sèche **au-dessus de la résistance cassée** | c'est un BU/BUEC (LPS hors plage) | vocabulaire contraire à la règle CLAUDE.md « LPS ≠ BUEC » | renommer ou dédoubler (BU vs LPS) |
| 12 | `window.py` l.299–316 ; l.50–51 | un seul LPS : réaction la plus profonde ≥ 1 ATR après le SOS, tenue au-dessus du **low du climax**, volume ≤ ×1,1, **sans condition de spread** ; le texte dit « back-up à la creek » | LPS multiples (Pruden 12/14, Fraser) ; BU strict (Fraser 2018) | règle de profondeur la plus tolérante ; LPS et BU confondus | séries de LPS, condition de spread, deux niveaux de profondeur |
| 13 | `window.py` l.265–277 | un seul ST retenu (le plus sec), pas de séquence | gradient de volume sur plusieurs ST (WA) ; UA/UT, ST as SOW | la maturité de Phase B n'est pas mesurée ; les ST volumiques du début sont filtrés | stocker la suite des tests et la pente du volume |
| 14 | `events.py` l.88–94 | toute percée du haut de plage avec retour = « UTAD », même en Phase B | UTAD = fin de plage ; avant, c'est un UT | sur-étiquetage UTAD | condition de position dans la séquence |
| 15 | `events.py` l.141–146 | LPSY exige un volume sec (≤ ×0,85) | « Volume may be light or heavy » (Pruden) | LPSY volumiques manqués | critère spread étroit + échec |
| 16 | `window.py` l.209–217 | climax à ×1,5, sans condition de spread | config ×2,0 et 1,3 ATR | écart non documenté entre les deux modules | aligner, ou documenter le relâchement |
| 17 | `features.py` l.45 | MA20 glissante en H1 sur un marché 24/7 | Williams critique le lissage (MTM p.19) | creux de week-end ou d'Asie = faux « tests secs » [I] | normaliser par heure de la journée ou jour de la semaine |
| 18 | `config.yaml` l.16–17 | backtest à stop 1 ATR et objectif 2R | test d'achat n°9 : R:R ≥ 3 | métrique hors doctrine | tester R:R 3 et une entrée sur test/LPS au lieu de l'événement |

> **À retenir** — Les détecteurs actuels lisent bien les **événements d'action** (climax, percées, signes), mais pas encore les **tests** comme la doctrine les définit : relatifs à l'action testée, gradués, conditionnés par une cause et validés par une réponse. C'est le principal chantier, et chaque nouveau détecteur doit venir avec un test synthétique dans `tests/` (convention du dépôt).

## 10. Errata du premier mémo (`docs/memo_tests_CO.md`)

**Verdicts** : ✅ confirmé · ⚠️ nuancé · ❌ faux · ❔ non vérifié.

| # | Affirmation (§) | Verdict | Correction sourcée |
|---|---|---|---|
| 1 | En-tête : les seuils listés sont « ceux du screener » | ⚠️ | Valeurs exactes (`config.yaml`), mais `narrow_spread_atr` n'est appliqué par aucun détecteur et `pen_atr` (0.1) manque à la liste (§9) |
| 2 | « OI / CVD / absorption sont nos overlays modernes » | ⚠️ | OI et CVD sont bien absents des sources. L'**absorption** est classique : « Out of 1,000 shares offered at a certain price he may take 600 or 700 » ([TR §10](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)) ; « The theme of the B Phase is Absorption » ([Fraser, Let's Review (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-07-wyckoff-power-charting-lets-review)) ; « absorption volume » (MTM). Seule sa mesure par flux est moderne |
| 3 | « Fiches auteurs = paraphrases, aucune citation verbatim » | ⚠️ | Corrigé ici : citations courtes vérifiées sur les textes (cours OCR, MTM, PDF Pruden) |
| 4 | §1.1 Le CO passe de faiseur de prix passif à preneur de prix | ✅ (analogie) | Cohérent avec Kaniel & Liu, Collin-Dufresne & Fos et la loi en racine carrée (§2.2) |
| 5 | §1.2 Le test est « son seul instrument de mesure du monde extérieur » | ❌ | Wyckoff décrit aussi l'enquête sur le carnet (« How much is offered in the next five points up? », [§14M p.4](https://archive.org/details/WyckoffMethodOfTapeReading)), Livermore les sondages de courtiers ([ch. XXI](https://www.gutenberg.org/ebooks/60979)), et les nouvelles comme tests ([TR §10](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)) |
| 6 | §1.3 « un volume absent ne se truque pas » | ⚠️ | Le volume **exécuté** ne s'annule pas (contrairement au *spoofing*), mais le volume déclaré peut être gonflé (*wash trading* > 70 % sur plateformes non régulées en 2019, [Cong et al.](https://nber.org/papers/w30783)) ; en futures, un test volumique peut être valide ([MTM p.158](https://www.tradeguider.com/mtm_251058.pdf)) |
| 7 | §1.4 « On the springboard » = verdict de tests | ✅ | [§14M pp.3–5, ©1931](https://archive.org/details/WyckoffMethodOfTapeReading). Précision : Wyckoff le situe au **bas de la plage**, pas à la cassure (« I claim that the beginning of the springboard move is at the bottom of a range of accumulation ») |
| 8 | §1.5 Les pools de 1910–30 sondaient réellement | ✅ / ⚠️ | Confirmé par [§8M p.1](https://archive.org/details/WyckoffMethodOfTapeReading), [TR §9–10](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks), [Lefèvre ch. XX](https://www.gutenberg.org/ebooks/60979). Nuance : sur 55 pools de 1929, « the evidence suggests informed trading rather than manipulation » ([Jiang, Mahoney & Mei](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)) |
| 9 | §2 Les 5 conditions sont « TOUTES nécessaires » | ⚠️ | Nécessaires : cause, lieu, volume < action testée. Qualité : spread, creux, clôture. Validation : réponse (§1.4). Un léger sous-percement n'invalide pas : « above, at, or below the Selling Climax low and still be successful » ([Fraser, Action – Test (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)) ; « not all lower quality tests fail » ([SMI, Test of Springs](https://wyckoffsmi.com/test-of-springs/)) |
| 10 | §2 cond. 1 : `vol_ratio ≤ 0.85` prouve le volume sec | ⚠️ | La doctrine compare à l'action testée : « the volume is less than on the Spring day » ([Fraser, Springing into Action (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)) ; Williams critique le lissage (MTM p.19) |
| 11 | §2 cond. 2 : spread étroit `≤ 0.7` ATR | ⚠️ | Vrai à l'échelle du swing (SMI, WA). Pour la barre de test VSA : « If the spread is narrow it will have less impact » ([Holmes/TG](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)). Et le code n'applique pas 0.7 |
| 12 | §2 crypto : « un test avec OI qui MONTE n'est pas un test » | ⚠️ | Règle interne non sourcée. Tout contrat a un long et un short : OI↑ peut venir de shorts agressifs **ou** d'acheteurs passifs qui absorbent, donc **ambigu** → tierces (règle CLAUDE.md « OI ambigu »). Garder « non validé » par défaut, pas « invalide » |
| 13 | §3.1 Tableau des tests (ST, Phase B, spring, test, LPS, BUEC, no supply) | ✅ | Conforme à StockCharts/WA, SMI, Pruden et MTM, avec les nuances de la §6 |
| 14 | §3.2 « Doctrinalement le BUEC est une forme de LPS (Evans) » | ⚠️ | Aucun texte d'Evans retrouvé. L'équivalence vient de Fraser 2015 (« BUEC with a LPS », [Fraser, Jumping the Creek (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-jumping-the-creek/)) et de Villahermosa ; pour Pruden et StockCharts, le BU est le mouvement **vers** un LPS |
| 15 | §3.2 LPS = avant la cassure, dans la plage ; BUEC = après | ⚠️ | Convention utile, mais StockCharts/WA définit le LPS comme « the low point of a reaction or pullback after a SOS », y compris sur « support that was formerly resistance » ; Villahermosa a des LPS « dentro » et « fuera del rango » |
| 16 | §3.2 BUEC : « typiquement un ; beaucoup = la sortie ne tient pas » | ❔ | Non sourcé. Fraser décrit « SOS 2 and BUEC 2 », Pruden les points 12 et 14 ; le BU peut devenir « a new TR at a higher level » (StockCharts) |
| 17 | §3.2 Invalidation du BUEC : clôture dans la plage → upthrust | ⚠️ | École stricte (Villahermosa ; Fraser 2018) contre école tolérante (Fraser 2022 ; stop de Pruden sous le spring) |
| 18 | §3.3 « Numérotation variable selon les sources » | ❌ | Même ordre chez SMI (glossaire, O'Brien), Fraser et Villahermosa 2018 : #1 lourd → #3 léger ; Pruden 2006 sans numéros ; aucune inversion trouvée ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/) ; [Fraser, Francis Bacon (2015)](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends) ; [Villahermosa 2018](https://tradingwyckoff.com/assets/TICKER1.pdf)) |
| 19 | §3.3 Les 3 types attribués à « Pruden/SMI » | ⚠️ | Numérotation attestée chez SMI, Fraser, Villahermosa ; Pruden 2006 gradue sans numéros ; Pruden 2007 non consulté |
| 20 | §3.3 #2 : « séquence typique 3–10 barres » | ❔ | Non sourcé : Fraser montre un test le lendemain ou dans les deux jours ([Fraser, Best Trade Entry Points (2016)](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/)) ; aucune source ne chiffre |
| 21 | §3.3 #1 : « test différé en back-up » | ⚠️ | Le test tardif est documenté (« The reaction took 18 days. The rally only 12 », [SMI, Test of the Shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/)) ; le back-up sur la zone reconquise comme substitut est une extension du projet. Achat du #1 : SMI après test, Fraser jamais, Pruden dès le point 8 |
| 22 | §3.4 Barre de test idéale : « baisse, spread étroit, volume < 2 barres précédentes » | ❌ | Conflation : « < 2 barres » définit le **no supply** ([MTM p.19](https://www.tradeguider.com/mtm_251058.pdf) ; SOS 199). Pour le test : nouveau plus-bas et barre baissière = bonus, spread étroit = « less impact » (SOS 11) |
| 23 | §3.4 Règle du re-test sur volume fort | ✅ / ⚠️ | [MTM p.34, 77, 95](https://www.tradeguider.com/mtm_251058.pdf) ; [Coulling p.45–46](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page46.html). Exceptions de Williams : *bad news*/shakeout, *bull move*, **futures** (p.158) |
| 24 | §3.4 (b) « test sec sans réponse = pas de demande = neutre » (repris dans CLAUDE.md) | ❌ | Williams : « Any testing that does not respond immediately with higher prices … can be considered an indication of weakness » (p.35) ; *negative action* « is a sign of weakness » (p.152) ; « The test is discounted » (p.89). En marché plus fort, guetter un second test (p.155) |
| 25 | §3.4 Test raté = `vol_ratio ≥ ~1.5` | ❔ | Heuristique : aucune source ne chiffre « high volume » |
| 26 | §4 l.4 Test sec sans réponse → le CO « attend ou anime » | ⚠️ | Même correction que n°24 : lecture de faiblesse d'abord |
| 27 | §4 l.6 Tests secs puis UPTHRUST de la borne haute → « le cadre est peut-être faux » | ⚠️ | En Phase B, les « upthrust-type actions at the upper end of the TR » sont normales en accumulation (WA ; UA de Villahermosa ; UT de Fraser). L'alerte vaut en **fin** de plage (UTAD potentiel) |
| 28 | §6 spring + test sec = « spring CONFIRMÉ » | ⚠️ | Vrai pour #1/#2 (« A successful Secondary Test is the final action that confirms a Spring was successful », [SMI, Testing the Spring](https://wyckoffsmi.com/testing-the-spring/)). Pour un #3, la confirmation vient de la demande (« rally back into the trading range ») ; WA : « The appearance of a SOS shortly after a spring or shakeout validates the analysis » |
| 29 | §6 « test sec validé > SOS volumique » | ❔ | Heuristique du projet ; aucune source ne classe ainsi (Pruden classe le test mieux que le shakeout, et le BUEC « safe ») |
| 30 | §7 Exemples XAU H4, BTC H1, BTC H4 | ❔ | Données de marché non contrôlées dans cette recherche |
| 31 | §8 Wyckoff (1873–1934) | ✅ | 2 novembre 1873 – 7 mars 1934 ([Wikipedia](https://en.wikipedia.org/wiki/Richard_Wyckoff)) |
| 32 | §8 *Studies in Tape Reading* (1910), le Cours (1931) | ✅ | « By Rollo Tape — The Ticker Publishing Company … Copyright, 1910 » ([archive.org](https://archive.org/details/studiesintaperea00wyckrich)) ; cours ©1931–1933, division *Tape Reading* ©1932, révisions 1934 et 1936–37 ([archive.org](https://archive.org/details/WyckoffMethodOfTapeReading)) |
| 33 | §8 Projet : « rétro-ingénierer les campagnes des gros opérateurs » | ✅ | « my object being to find out or reason out what the large operator did and how he did it; then I could operate in the same way » ([How I Trade, p.40](https://archive.org/details/cu31924031269552)) |
| 34 | §8 Composite Man = trace d'un opérateur unique | ✅ / ⚠️ | [§9M p.1](https://archive.org/details/WyckoffMethodOfTapeReading). Variante « Composite Operator » / « C. O. » dans la division *Tape Reading*, avec la mise en garde « There is no Composite Operator » ([TR §10](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)) |
| 35 | §8 « Campagne en 4 actes » | ⚠️ | En 1910 : « A complete manipulative operation on the long side consists of three parts: Accumulation, marking up, and distribution » ([STR pp.91–92](https://archive.org/details/studiesintaperea00wyckrich)) ; le cycle en quatre phases est une présentation ultérieure |
| 36 | §8 Les Neuf tests d'achat (liste paraphrasée, attribuée à Wyckoff) | ⚠️ | Le contenu suit l'ordre de Pruden 2007 / StockCharts. La plus ancienne version trouvée (cours 1937, §20M, pages Wyckoff Associates) a un autre ordre et ne mentionne pas SC/ST (§7.5) |
| 37 | §8 Robert G. Evans « (†1972) » | ❔ (probablement faux) | Une seule source donne 1904–1976 ([readtheticker](https://www.readtheticker.com/Pages/IndLibrary.aspx?65tf=1555_bob-evans-renowned-wyckoff-teacher), non chargée) ; SMI : rachat de l'Institut en 1951 ([SMI, histoire](https://wyckoffsmi.com/history-of-wyckoff-stock-market-institute/)) |
| 38 | §8 Evans : « conférences SMI (années 1940–60), pas de livre » | ⚠️ | Conférences *Evans Echoes* confirmées (« EE-13 The Ice Story », « EE-33 When A Spring Isn't a Spring », [liste SMI](http://wyckoffstockmarketinstitute.com/evans-echoes-lectures-complete-list/)) ; StockCharts dit « from the 1930s to the 1960s » ; « pas de livre » est invérifiable (on lui crédite le *Count Guide*) |
| 39 | §8 Le **terminal shakeout** classé parmi les allégories d'Evans | ❌ | Terme de Wyckoff lui-même, défini au §21M (page ©1932) ; le **spring** en est le raffinement SMI/Evans ([SMI, glossaire](https://wyckoffsmi.com/wyckoff-glossery/)) |
| 40 | §8 Ice : le LPSY « cale dessous à volume sec » | ⚠️ | « Volume may be light or heavy, showing weak demand or substantial supply » ([Pruden 2006](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) |
| 41 | §8 Pruden (1936–2017), Golden Gate University, « trois compétences », cycle de psychologie de foule | ❔ | Non vérifié dans nos sources (livre de 2007 non consulté) ; StockCharts parle de « the late Dr. Henry O. ("Hank") Pruden » |
| 42 | §8 Pruden « standardise la grille A–E » | ⚠️ | Pruden & von Lichtenstein créditent les schémas à Jim Forte (« The Anatomy of a Trading Range », MTA Journal, 1994) et les annotations à Evans ; les schémas actuels sont de Bogomazov, « edited by » Pruden ; Weis : modèles « added after his death » |
| 43 | §8 Pruden « popularise les springs #1/#2/#3 » | ❔ | L'article de 2006 gradue sans numéros ; le livre de 2007 n'a pas été consulté |
| 44 | §8 « Le trade JAC/BUEC = setup à plus haute probabilité » | ⚠️ | Pruden dit « safe » (Nokia) ; « high-probability opportunity » est employé par StockCharts pour le test de la cassure en **distribution** |
| 45 | §8 Williams (1929–2016) | ✅ | 4 janvier 1929 – 7 novembre 2016 ([TradeGuider](https://www.tradeguider.com/pdf/topbot_V1_Public.pdf)) |
| 46 | §8 *Master the Markets* (1993/2005) | ⚠️ | 1993 = *The Undeclared Secrets That Drive the Stock Market* ; *MTM* = révision de janvier 2000 ; 3ᵉ éd. 2005 (Roy Didlock, vérification indirecte) ; 4ᵉ éd. septembre 2009 ([MTM](https://www.tradeguider.com/mtm_251058.pdf)) |
| 47 | §8 Williams « fondateur du VSA (TradeGuider) » | ⚠️ | La méthode VSA a été codée dans le logiciel « VSA » (Genie Software), « the forerunner to TradeGuider » ; Williams en était Chairman (MTM). Précision utile : il a appris la lecture professionnelle comme trader d'un syndicat à Beverly Hills pendant 12 ans (4ᵉ de couverture de MTM) |
| 48 | §8 Test = geste provoqué (≠ no supply passif) | ✅ | [MTM p.34–35 vs p.19](https://www.tradeguider.com/mtm_251058.pdf) |
| 49 | §8 « Nos seuils `test_vol`, `narrow_spread_atr` en sont la traduction » | ⚠️ | Williams ne chiffre rien ; le spread étroit contredit TradeGuider pour la barre de test ; `narrow_spread_atr` n'est pas implémenté |

> **Piège** — Trois corrections touchent aussi `CLAUDE.md`, qui reprend le premier mémo : (a) « sinon no supply + no demand = neutre » → faiblesse (*negative action*) ; (b) « un "test" à OI↑ n'en est pas un » → test **non validé**, OI ambigu à départager par les tierces ; (c) « spread ≤ narrow_spread_atr » comme condition **nécessaire** → critère de qualité à l'échelle du swing, pas de la barre VSA. Ces lignes ne sont pas modifiées ici ; c'est à Gauthier de trancher.

## 11. Conclusion : le test est une mesure relative, conditionnelle et validée par la suite

Le premier mémo traitait le test comme une barre sèche près d'un support. Les sources en font une **mesure relative** (volume contre l'action testée), **conditionnelle** (pas de test sans cause en amont), **graduée** (A à D, avec un sous-percement toléré) et **validée par la réponse** (sans hausse en 1–3 barres, c'est de la faiblesse). Le type de spring fixe l'exigence de test. L'économie des métaordres explique pourquoi un opérateur rationnel teste : l'impact en racine carrée et sa persistance rendent un markup raté coûteux deux fois. Mais la littérature empirique ne mesure que des avantages modestes : un test sert d'abord à **placer le risque** là où l'offre a déjà été consommée, ensuite seulement à prédire. Pour les perps BTC, l'apport le plus solide est la nuance de Williams sur les futures : un test volumique peut y être de la force. C'est là que la règle du projet « OI en coin » trouve son meilleur ancrage doctrinal : l'OI départage un test volumique, il ne le condamne pas.

Pour le screener, l'écart principal n'est pas un seuil mal réglé : les détecteurs lisent les **actions** (climax, percées, signes) mais pas encore les **tests** au sens doctrinal. Les priorités qui en découlent sont un détecteur de test du spring, la classification #1/#2/#3, le volume relatif à l'action testée, la confirmation par la réponse et des étiquettes conditionnelles (« SOS ? / UTAD ? ») jusqu'à la tenue et au BU. Chacune se valide hors échantillon contre des niveaux arbitraires, sur le modèle d'Osler. Trois lignes de `CLAUDE.md` héritées du premier mémo mériteraient d'être révisées (§10). Le mémo frère `memo_theorie.html` reste la référence rapide des seuils événement par événement.

## 12. Glossaire FR/EN

| Français | English | Définition courte | Origine / usage |
|---|---|---|---|
| Absorption | Absorption | achat passif de l'offre sans hausse du prix (effort sans résultat) | Wyckoff (TR §10), Fraser, Williams |
| Rebond automatique / réaction automatique | Automatic Rally / Automatic Reaction (AR) | rebond (ou repli) réflexe après le climax ; fixe l'autre borne | SMI ; Wyckoff : *technical rally* |
| Fond (contexte) | Background | ce que disent les barres précédentes ; conditionne tout signal VSA | Williams |
| Back-up, retour au bord du ruisseau | Back-Up (BU), Back-Up to the Edge of the Creek (BUEC) | repli sec après le JAC sur l'ancienne résistance | Evans (via Pruden, StockCharts) |
| Climax acheteur | Buying Climax (BC) | sommet de la hausse sur volume et spread extrêmes ; fixe le plafond | Wyckoff |
| Cause et effet | Cause and effect | la largeur (P&F) de la plage mesure l'ampleur du mouvement suivant | présentation moderne (« three laws ») |
| CLV | Close Location Value | (C−L)/(H−L), position de la clôture dans la barre | screener |
| Composite Man / Composite Operator (CO) | Composite Man / Composite Operator | fiction d'un opérateur unique derrière le marché | Wyckoff (§9M ; TR §9–10) |
| Ruisseau | Creek | ligne de résistance sinueuse reliant les sommets de rallye | Evans |
| Décompte P&F | Point & Figure count | mesure horizontale de la cause, comptée depuis le LPS | Wyckoff, WA |
| Effort contre résultat | Effort vs result | volume (effort) comparé au déplacement (résultat) | présentation moderne ; idée présente chez Williams |
| Chute à travers la glace | Fall Through the Ice (FTI) | cassure du support (Pruden) ; le retest chez Villahermosa | Evans |
| Glace | Ice | ligne de support sinueuse sous les creux ; devient résistance après la cassure | Evans, SMI |
| Charnière, apex | Hinge, apex | contraction du prix et du volume avant le départ | Wyckoff |
| Saut du ruisseau | Jump Across the Creek (JAC) | SOS majeur qui franchit le creek sur expansion de volume | Evans |
| Dernier point d'appui | Last Point of Support (LPS) | creux d'une réaction sèche (Phase C, D ou BU) | SMI, WA, Fraser |
| Dernier point d'offre | Last Point of Supply (LPSY) | rallye faible à spread étroit après un SOW | SMI, WA |
| Métaordre | Metaorder | gros ordre fractionné en nombreuses exécutions | microstructure |
| Signe de force / faiblesse mineur | minor SOS (mSOS) / minor SOW (mSOW) | poussée qui ne casse pas la structure | Villahermosa, Fraser |
| Action négative | Negative action | test sans réponse haussière en 2–3 barres = faiblesse | Williams |
| Pas de demande | No demand | barre haussière étroite, volume < deux barres précédentes | Williams, TG |
| Pas d'offre | No supply / no selling pressure | barre baissière, volume < deux barres précédentes | Williams, TG |
| Open interest (en coin) | Open interest (coin-denominated) | nombre de contrats ouverts, lu en BTC pour la direction | projet (CLAUDE.md) |
| Soutien / offre préliminaire | Preliminary Support / Supply (PS / PSY) | premier freinage de la tendance | Wyckoff |
| Réaccumulation (palier) | Re-accumulation (stepping stone) | plage de pause dans une tendance haussière | WA, Fraser |
| Redistribution | Re-distribution | plage de pause dans une tendance baissière | WA, Pruden |
| Réaction secondaire | Secondary reaction | terme de Wyckoff pour le futur ST | Cours §7M |
| Test secondaire | Secondary Test (ST) | retour sec vers la zone du climax | SMI, WA |
| ST en Phase B / ST signe de faiblesse | ST in Phase B / ST as SOW | tests de la borne basse ; creux plus bas en B | WA (schémas) / Villahermosa |
| Climax vendeur | Selling Climax (SC) | creux de la baisse sur volume et spread extrêmes ; fixe le plancher | Wyckoff |
| Secousse (ordinaire) | Shakeout (ordinary) | poussée baissière brutale dans une tendance haussière | SMI, Wyckoff §21M |
| Signe de force / de faiblesse | Sign of Strength / Weakness (SOS / SOW) | poussée large et volumique dans le sens de la sortie | SMI, WA |
| Ressort #1 / #2 / #3 | Spring #1 / #2 / #3 | fausse cassure du support, graduée par l'offre libérée (#1 lourd → #3 léger) | SMI/Evans |
| Tremplin | Springboard | fin de préparation, au bas de la plage ; résultat des tests | Wyckoff (§14M) |
| Volume d'arrêt | Stopping volume | barre baissière très volumique qui clôture haut | Williams |
| Secousse terminale | Terminal shake-out | chute brutale en fin de préparation, plus profonde qu'un spring | Wyckoff (§21M, ©1932) |
| Test (barre de test) | Test (test bar) | marquage à la baisse dans une zone d'offre, qui reprend sur faible volume | Williams |
| Test en marché haussier | Test in a rising market | test de continuation après une sortie ou une poussée | Williams, TG |
| Plage de trading | Trading Range (TR) | zone latérale bornée par le climax et l'AR | — |
| Action d'upthrust | Upthrust Action (UA) | percée brève du haut de plage, en accumulation | Villahermosa |
| Upthrust | Upthrust (UT) | percée du haut de plage qui ne tient pas | Wyckoff (§21M p.2), SMI |
| Upthrust après distribution | Upthrust After Distribution (UTAD) | test final de la demande au-dessus de la plage, en fin de distribution | Evans (glossaire SMI) |

## 13. Bibliographie commentée

**Statut** : *lu* = texte consulté directement ; *extrait* = vu via un extrait ou un outil de récupération ; *non consulté* = cité de seconde main.

**A. Sources primaires (Wyckoff, Lefèvre)**

| Référence | Utilisée pour | Statut |
|---|---|---|
| R. D. Wyckoff (« Rollo Tape »), *Studies in Tape Reading*, Ticker Publishing, 1910 ([archive.org](https://archive.org/details/studiesintaperea00wyckrich)) | tests comme « critical points », trois parties d'une opération | lu (OCR) |
| R. D. Wyckoff, *How I Trade and Invest in Stocks and Bonds*, 1922 ([archive.org](https://archive.org/details/cu31924031269552)) | projet de rétro-ingénierie, pools, Keene, Livermore | lu (OCR, 5ᵉ éd.) |
| *The Richard D. Wyckoff Method of Trading and Investing in Stocks*, cours ©1931–33, éd. 1937 ([archive.org](https://archive.org/details/WyckoffMethodOfTapeReading)) | Composite Man, tests-sondes, *secondary reaction*, springboard, terminal shake-out, upthrust, neuf tests (pages 1937) | lu (OCR) ; la page porte la date de rédaction |
| Wyckoff, *Tape Reading and Active Trading* (Division 2), ©1932 ([archive.org](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)) | « Judging the market by tests and responses », « There is no Composite Operator » | lu (OCR) |
| E. Lefèvre, *Reminiscences of a Stock Operator*, 1923 ([Gutenberg](https://www.gutenberg.org/ebooks/60979)) | *testing order*, coût des sondes, Keene, Imperial Steel | lu |

**B. SMI / Evans**

| Référence | Utilisée pour | Statut |
|---|---|---|
| Wyckoff SMI, glossaire et bibliothèque ([glossaire](https://wyckoffsmi.com/wyckoff-glossery/) ; [bibliothèque](https://wyckoffsmi.com/library/)) | spring #1/#2/#3, terminal et ordinary shakeout, UTAD (Evans), ice, LPS | extrait (outil de récupération) ; vérifier avant citation longue |
| J. O'Brien, blog SMI, 2014–2015 ([#3 Spring](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/) ; [Testing the Spring](https://wyckoffsmi.com/testing-the-spring/) ; [Test of Springs](https://wyckoffsmi.com/test-of-springs/) ; [shakeout](https://wyckoffsmi.com/wheres-the-test-of-the-shakeout/) ; [short term](https://wyckoffsmi.com/springs-shakeouts-and-the-short-term-trader/) ; [failed spring](https://wyckoffsmi.com/another-failed-spring/)) | exigence de test par type, barème de qualité, gestion des positions | extrait |
| SMI, histoire de l'Institut ([SMI, histoire](https://wyckoffsmi.com/history-of-wyckoff-stock-market-institute/)) ; liste des *Evans Echoes* ([liste](http://wyckoffstockmarketinstitute.com/evans-echoes-lectures-complete-list/)) | rôle et chronologie d'Evans | extrait ; aucun texte d'Evans consulté |

**C. Pruden, Wyckoff Analytics, StockCharts, Fraser**

| Référence | Utilisée pour | Statut |
|---|---|---|
| H. Pruden & M. von Lichtenstein, « Wyckoff Schematics: Visual templates for market timing decisions », *Market Technician* (STA) n°55, 2006 ([PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)) | jump/backup, creek et ice, points d'entrée 8/10/12/14, Nokia, LPSY « light or heavy » | lu (texte extrait du PDF) ; source la plus riche sur Evans, de seconde main |
| R. Bogomazov & M. Lipsett (schémas édités par Pruden), « The Wyckoff Method: A Tutorial », StockCharts ChartSchool ([lien](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)) ; même texte chez Wyckoff Analytics ([PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)) | définitions de référence (ST, spring, LPS, BU, UTAD), neuf tests adaptés de Pruden 2007, décompte P&F | lu ; une seule source |
| Pruden, Fraser & Bogomazov, « The Composite Man's Bull Market Campaign », *S&C* V.32:8, 2014 ([PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/08/V32C08822PRUD.pdf)) | achat en net de Phase B, ST du BC, guide de décompte | lu |
| H. Pruden, *The Three Skills of Top Trading*, Wiley, 2007 ([chapitre 6](https://onlinelibrary.wiley.com/doi/abs/10.1002/9781119196822.ch6)) | neuf tests (via StockCharts) | **non consulté** |
| B. Fraser, *Wyckoff Power Charting*, StockCharts, 2015–2022 (articles cités dans le texte, dont [Action – Test](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test), [Springing into Action](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action), [Jumping the Creek](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-jumping-the-creek/)) | types de spring et entrées, LPS de Phase C, JAC/BUEC, distribution, fractalité | lu |
| A. Rutigliano, « Trading the Crypto Market with the Wyckoff Method », Wyckoff Analytics, 2020 ([PDF](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)) | seule source WA sur la crypto : UA, MSOS, P&F en % | lu (en partie images) |
| Wyckoff Analytics, « Reaccumulation vs Distribution », 2026 ([lien](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)) ; « Identifying Wyckoff Springs with Algorithms » ([lien](https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/)) | gradient de volume des baisses ; règles de spring algorithmiques | lu |

**D. Villahermosa, Weis**

| Référence | Utilisée pour | Statut |
|---|---|---|
| R. Villahermosa, « Profundizando en los Springs », *TheTicker* n°1, Instituto Wyckoff España, 2018 ([PDF](https://tradingwyckoff.com/assets/TICKER1.pdf)) | typologie #1/#2/#3, ordinary shakeout, fonctions du spring | lu |
| R. Villahermosa, tradingwyckoff.com ([ST](https://tradingwyckoff.com/en/secondary-test/), [Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/), [LPS](https://tradingwyckoff.com/last-point-of-support/), [SOS](https://tradingwyckoff.com/en/sign-of-strength/), [guide](https://tradingwyckoff.com/en/wyckoff-method/)) | UA/UT, ST as SOW, mSOS, typologie des LPS, FTI, plan de trade | lu, sauf la page Spring (anti-bot, [NV]) ; chiffres des FAQ non doctrinaux ; livre non consulté |
| D. Weis, *Trades About to Happen*, Wiley, 2013 ([extrait](https://content.e-bookshelf.de/media/reading/L-802008-2fe9f872b5.pdf)) | provenance des schémas et du vocabulaire, mise en garde contre les « cookie prints » | introduction seulement ; chapitres « Springs » et « Upthrusts » non consultés |

**E. VSA**

| Référence | Utilisée pour | Statut |
|---|---|---|
| T. Williams, *Master the Markets*, 4ᵉ éd., TradeGuider, 2009 (1993 / 2000 / 2005) ([PDF](https://www.tradeguider.com/mtm_251058.pdf)) | test, re-test, *negative action*, background, nuance futures, no supply/no demand, upthrust | lu ; source commerciale au langage absolu, sans statistiques |
| G. Holmes, *VSA System Explained / Trade Set-Up Sequences*, TradeGuider, 2011 ([PDF](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)) ; supports de séminaire TG ([SOS](https://www.volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20strength.pdf), [SOW](https://volumespreadanalysis.com/hubfs/Website%20PDFs%20%28Downloadables%29/VSA%20Signs%20of%20weakness.pdf)) | définitions officielles des indicateurs (Basic Test, No Supply, No Demand) ; règle des deux barres | lu |
| A. Coulling, *A Complete Guide to Volume Price Analysis*, ch. 5 ([p.45](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page45.html)) | test of demand, test raté | lu sur une copie flipbook non officielle ; date d'édition non vérifiée |

**F. Microstructure et marchés (académique)**

| Référence | Utilisée pour | Statut |
|---|---|---|
| A. Kyle, « Continuous Auctions and Insider Trading », *Econometrica* 53(6), 1985 ([abstract](https://www.econometricsociety.org/publications/econometrica/1985/11/01/continuous-auctions-and-insider-trading)) | camouflage par le bruit, λ | abstract et notes de cours |
| B. Tóth et al., « Anomalous price impact… », *Phys. Rev. X* 1, 2011 ([arXiv](https://arxiv.org/pdf/1105.1694)) ; J.-P. Bouchaud, 2024 ([billet](https://bouchaud.substack.com/p/the-square-root-law-of-market-impact)) ; J. Donier & J. Bonart, Bitcoin ([arXiv](https://arxiv.org/abs/1412.4503)) ; J. D. Farmer et al. ([arXiv](https://arxiv.org/abs/1102.5457)) | loi en racine carrée, liquidité latente, impact permanent ≈ 2/3 | lu |
| Almgren–Chriss ([résumé](https://en.wikipedia.org/wiki/Almgren%E2%80%93Chriss_model)) ; Kaniel & Liu 2006 ([notice](https://ideas.repec.org/a/ucp/jnlbus/v79y2006i4p1867-1914.html)) ; Collin-Dufresne & Fos 2015 ([NBER](https://www.nber.org/papers/w18452)) ; Cont, Kukanov & Stoikov 2014 ([arXiv](https://arxiv.org/abs/1011.6402)) | exécution optimale, ordres limites des initiés, OFI | notices et abstracts |
| C. Osler, 2000, 2003, 2005 ([EPR](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf), [SR 125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf), [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)) | groupement des stops et cascades, base du spring/UTAD | lu ; données FX 1996–2000, transposition à BTC = hypothèse |
| Avellaneda & Stoikov 2008 ([PDF](https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf)) ; Hendershott & Menkveld 2014 ([notice](https://econpapers.repec.org/RePEc:eee:jfinec:v:114:y:2014:i:3:p:405-423)) ; Campbell, Grossman & Wang 1993 ([PDF](https://dash.harvard.edu/bitstream/1/3128710/2/campbell_trading.pdf)) ; Llorente et al. 2002 ([notice](https://econpapers.repec.org/RePEc:oup:rfinst:v:15:y:2002:i:4:p:1005-1047)) | inventaire du teneur de marché, retournements de liquidité vs continuations informées | lu / abstracts |
| Brunnermeier & Pedersen 2005 ([page](https://www.princeton.edu/~markus/research/papers/predatory_trading.htm)) ; Bessembinder et al. ([SSRN](https://papers.ssrn.com/ab_id=956476)) ; Frey & Sandås ([PDF](https://gfk-cfs.de/media//08_48.pdf)) ; van Kervel & Menkveld 2019 ([notice](https://econpapers.repec.org/RePEc:bla:jfinan:v:74:y:2019:i:3:p:1091-1137)) ; L. Harris, *Trading and Exchanges*, 2003 ([OUP](https://academic.oup.com/book/52292)) | trading prédateur, ordres cachés, anticipation, typologie des traders | abstracts ; Harris non consulté directement |
| Jiang, Mahoney & Mei 2005 ([PDF](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)) ; Mahoney 1999 ([notice](https://ideas.repec.org/a/eee/jfinec/v51y1999i3p343-369.html)) | pools de 1929 : informés plutôt que manipulateurs | lu / notice |
| Kavajecz & Odders-White 2004 ([notice](https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html)) ; Garzarelli et al. 2014 ([texte](https://ar5iv.labs.arxiv.org/html/1110.5197)) ; Zapranis & Tsinaslanidis 2012 ([notice](https://econpapers.repec.org/RePEc:taf:apfiec:v:22:y:2012:i:19:p:1571-1585)) ; Sullivan, Timmermann & White 1999 ([PDF](https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf)) | ce que la recherche valide (et ne valide pas) des supports/résistances | lu / abstracts |

**G. Crypto, régulation, données**

| Référence | Utilisée pour | Statut |
|---|---|---|
| Binance API : [OI](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics), [ratio L/S](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio), [liquidations](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams), [funding](https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031) ; [Coinalyze API](https://api.coinalyze.net/v1/doc/) | définitions des données tierces (coin vs USD, comptes vs taille, planchers de liquidations) | lu |
| BIS WP 1087 « Crypto carry » ([BIS](https://www.bis.org/publ/work1087.htm)) ; Garcia Seuma 2026 ([arXiv](https://arxiv.org/abs/2607.27070), prépublication) ; Lim ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278), extrait) ; Silantyev 2019 ([notice](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)) ; Urquhart 2017 ([notice](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html)) ; Cong et al. ([NBER](https://nber.org/papers/w30783)) | cascades de liquidations, carry, flux, chiffres ronds, *wash trading* | abstracts ; Lim [NV] |
| [15 U.S.C. §78i](https://www.law.cornell.edu/uscode/text/15/78i) ; [7 U.S.C. §6c](https://www.law.cornell.edu/uscode/text/7/6c) ; [CFTC 8260-20](https://cftc.gov/PressRoom/PressReleases/8260-20) ; [FCA 2014](https://www.fca.org.uk/news/press-releases/fca-fines-five-banks-%C2%A311-billion-fx-failings-and-announces-industry-wide) ; [MiCA art. 91](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-91-prohibition-market-manipulation) ; [DOJ, Token Mirrors](https://www.justice.gov/usao-ma/pr/eighteen-individuals-and-entities-charged-international-operation-targeting-widespread) | ce qui est interdit aujourd'hui | lu ; pas un avis juridique |

**H. Implémentations et backtests (praticiens)**

| Référence | Utilisée pour | Statut |
|---|---|---|
| ProRealCode, « Wyckoff Event Detection » ([lien](https://www.prorealcode.com/prorealtime-indicators/wyckoff-event-detection/)) ; MQL5, 2026 ([lien](https://www.mql5.com/en/articles/22628)) ; systematic1/wyckoff-scanner ([GitHub](https://github.com/systematic1/wyckoff-scanner)) | fourchettes de seuils des implémentations (aucune n'est doctrinale) | lu |
| PR papan-saham #89 ([GitHub](https://github.com/augustgerry/papan-saham/pull/89)) | seul backtest public d'un spring seul (espérance négative) | [NV] : page 404, vu en extrait |

