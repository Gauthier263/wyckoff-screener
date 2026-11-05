# Vérifier et trader les tests Wyckoff : boîte à outils opérationnelle (notes de recherche, 2026-10-31)

Légende de fiabilité : **[V]** = texte lu directement (page récupérée ou PDF converti en texte) ; **[NV]** = vu seulement via un résumé de moteur de recherche, ou page inaccessible : ne pas présenter comme vérifié. Les citations sont verbatim, en langue originale. « FAQ » = section FAQ de tradingwyckoff.com, distincte du corps de l'article. Les chiffres qu'on y lit ne figurent pas dans les articles eux-mêmes, d'où une fiabilité incertaine.

## Q1 — Quels critères concrets et vérifiables définissent un « test réussi », pour chaque type de test (accumulation et miroir distribution) ?

### Takeaway
Les sources primaires (Wyckoff Analytics/ChartSchool, Fraser, Pruden, Wyckoff SMI, Villahermosa) s'accordent sur un noyau commun. Un test réussi revient vers la zone de l'action précédente (climax, spring, borne cassée) avec un **spread comprimé, moins de volatilité et un volume inférieur à celui de l'action testée**. Pour un test de support, il marque en plus un **plus-bas plus haut** (ou tient la zone).

La référence de volume est l'**événement testé** (SC, spring, SOS), pas une moyenne mobile. Les seuils chiffrés (×MA, ×ATR, % de pénétration) n'apparaissent que dans les implémentations algorithmiques et dans des FAQ non sourcées.

Deux désaccords sont documentés :
- le spring #1 : achetable après un test (SMI) ou jamais (Fraser) ;
- la tolérance d'un ST sous le low du SC : Fraser l'accepte, WA y voit un risque, Villahermosa un léger déséquilibre vendeur.

### Cited Findings

**Principe général « action → test »**
- Fraser : « A Climax is an Action. Such an Action must be Tested. » ; « The signature of the Action phase is volatility, wide spread, and high volume. » ; « In contrast the Testing should have compression of the price spread, less volatility and diminishing volume. » ; « The Test is a visual question: Is the majority of the selling exhausted? » ; « Actions and Tests are occurring in all markets, in all timeframes, all the time. » (2 sept. 2016) [V] — [Fraser, « Action – Test », StockCharts](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)
- Wyckoff Analytics (texte écrit pour la ChartSchool de StockCharts, reproduit avec permission) : « Large operators always test the market for supply throughout a TR (e.g., STs and springs) and at key points during a price advance. If considerable supply emerges on a test, the market is often not ready to be marked up. A spring is often followed by one or more tests; a successful test (indicating that further price increases will follow) typically makes a higher low on lesser volume. » [V] — [Wyckoff Analytics, « Wyckoff Method » (PDF)](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) ; même texte : [ChartSchool, « The Wyckoff Method: A Tutorial »](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)
- Définition d'une barre de demande ou d'offre (utile pour les « demand bars » de Fraser) : « a price bar that has wide spread, closing at a high well above those of the previous several bars and accompanied by higher-than- average volume, suggests the presence of demand. Similarly, a high-volume price bar with wide spread, closing at a low well below the lows of prior bars, suggests the presence of supply. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)

**ST de Phase A (test du SC)**
- WA : « If a bottom is to be confirmed, volume and price spread should be significantly diminished as the market approaches support in the area of the SC. It is common to have multiple STs after a SC. » ; « A successful secondary test (ST) in the area of the SC will show less selling than previously and a narrowing of spread and decreased volume, generally stopping at or above the same price level as the SC. If the ST goes lower than that of the SC, one can anticipate either new lows or prolonged consolidation. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Fraser : « A successful Test can occur above, at, or below the Selling Climax low and still be successful. » [V] — [Fraser, Action – Test](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test). **Désaccord partiel** avec WA (« generally stopping at or above »).
- Villahermosa : « For the Secondary Test to be successful, the bearish movement must be made with a narrowing in price ranges and lower volume than seen in the Selling Climax. » ; « What we really need to focus on is, in order of importance: the decrease in volume and the narrowing of ranges. » ; « a Secondary Test above the Selling Climax low would be seen with a neutral connotation » ; « equally would identify some imbalance in favor of sellers if the Secondary Test ends slightly below the Selling Climax. » [V] — [Villahermosa, « Secondary Test », tradingwyckoff.com](https://tradingwyckoff.com/en/secondary-test/)
- Villahermosa, **FAQ** de la même page (absent du corps) : un ST valide montre « at least 40-50% reduction » de volume ; le ST est « typically 50-70% less than the SC ». La FAQ lit un ST sous le SC à très faible volume comme une force (« shows strength if volume is very low »), ce qui contredit la lecture du corps. [V pour la présence sur la page ; fiabilité incertaine] — [tradingwyckoff.com ST](https://tradingwyckoff.com/en/secondary-test/)
- Pruden & von Lichtenstein : « If a bottom is to be confirmed, significant supply should not resurface, and volume and price spread should be significantly diminished as the market approaches support in the area of the SC. » [V] — [Pruden & von Lichtenstein, « Wyckoff Schematics: Visual templates for market timing decisions » (PDF, journal STA, non daté, postérieur à nov. 2004)](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)

**Tests de Phase B (ST in B, UA, ST as SOW ; miroir UT, mSOW)**
- WA : « There are usually multiple STs during Phase B, as well as upthrust-type actions at the upper end of the TR. » ; « Early on in Phase B, the price swings tend to be wide and accompanied by high volume. As the professionals absorb the supply, however, the volume on downswings within the TR tends to diminish. When it appears that supply is likely to have been exhausted, the stock is ready for Phase C. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Villahermosa [V] — [tradingwyckoff.com ST](https://tradingwyckoff.com/en/secondary-test/) :
  - « Once Phase B has started, we will be watching for any type of test to develop on either of the two ends of the range. »
  - Borne haute : « When the range is accumulation/reaccumulation, this event will be labeled as Upthrust Action (UA) » ; en distribution, « we will label it as Upthrust (UT) ».
  - Borne basse (ST as SOW en accumulation, mSOW en distribution) : « Generally there are more chances of this event appearing when the Secondary Test of Phase A has produced a lower low. » ; « This type of test denotes a lot of underlying weakness. »
  - Tests à fort volume : « Would indicate that there are still operators willing to continue pushing the price. »
  - « The optimal here would be to wait for repeated tests to appear until confirming that there is no stock available. »
  - Étiquetage simplifié possible : « Secondary Test in Phase B (ST in B) ».
- Fraser : « Secondary Test 1 (ST1) has the potential to be a Spring on high volume » ; « ST2 is another attempt to vacuum up shares at the Support Line and could be a Spring. » (13 juin 2015) [V] — [Fraser, « Francis Bacon Reveals the Nature of Trends »](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)
- Pruden & von Lichtenstein : « The penetrations or lack of penetrations of the TR enable us to judge the quantity and quality of supply and demand. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- Le support de cours crypto de Wyckoff Analytics (A. Rutigliano, juillet 2020) étiquette sur un schéma de réaccumulation Bitcoin : « ST in Phase B », « UA », « FAILED SPRING », « MSOS », « BU ». [V] — [Rutigliano, « Trading the Crypto Market with the Wyckoff Method » (slides WA, 2020)](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)

**Spring / shakeout (Phase C) : typologie #1/#2/#3 et critères**
- Fraser (13 juin 2015) [V] — [Fraser, Francis Bacon](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends) :
  - « The Number 3 Spring is a shallow penetration of the prior low on modest volume and can be bought immediately. »
  - « The Number 2 Spring goes further below the low on expanded volume » ; « The test will be on diminished volume and can be bought with stops below the Spring low. »
  - « The Number 1 Spring is actually a Shakeout that is a complete breakdown. » ; « It should not be bought. »
  - « The volume signature is the final arbiter of the type of Spring developing and this also determines the strategy for entry. »
  - « High volume Springs need to be tested in the following days or weeks. » ; « Low volume Springs do not need to be tested, as this indicates that supply is no longer present. »
- Wyckoff SMI (jim-obrien, 14 juin 2015) [V] — [Wyckoff SMI, « A #3 Spring And A Possible Successful Secondary Test »](https://wyckoffsmi.com/a-3-spring-and-a-possible-successful-secondary-test/) :
  - « The #1 Spring is a shakeout. Good supply drives the index or stock through the support and substantially below the bottom of the trading range. » ; « #1 Springs always have to be tested. »
  - « The #2 Spring is the most common. The index or stock falls through the bottom of the range, on good price spread and volume. » ; « #2 Springs also need to be tested. »
  - Le #3 glisse sous le support « on relatively narrow price spread and volume » ; « It is not confirmed until strong demand comes into the market and there is a rally back into the trading range. » ; « #3 Springs do not need to be tested. »
  - **Désaccord avec Fraser** : pour le SMI, le #1 se trade après un test ; pour Fraser, il ne s'achète pas.
- WA [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) :
  - « A “spring” takes price below the low of the TR and then reverses to close within the TR » ; « A terminal shakeout at the end of an accumulation TR is like a spring on steroids. » ; « springs and terminal shakeouts are not required elements ».
  - « A low-volume spring (or a low-volume test of a shakeout) indicates that the stock is likely to be ready to move up, so this is a good time to initiate at least a partial long position.The appearance of a SOS shortly after a spring or shakeout validates the analysis. »
- Pruden & von Lichtenstein [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) :
  - « If the amount of supply that surfaces on a break of support is very light (low volume), it will be an indication that the way is clear for a sustained advance. Heavy supply here will usually mean a renewed decline. Moderate volume here may mean more testing of support and to proceed with caution. »
  - « The extent of supply, or the strength of the sellers, can be judged by the depth of the price move to new lows and the relative level of volume on that penetration. »
  - Préférence pour le test par spring ou shakeout, « given that it does a better job of cleaning out remaining supply from weak holders ».
  - La même gradation en trois niveaux de volume figure dans le support crypto de Rutigliano (« Heavy supply here often precedes a renewed decline. Moderate volume usually means that there will be more testing for supply ») [V] — [slides WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)
- Fraser (6 mai 2016) [V] — [Fraser, « Springing into Action »](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action) :
  - Spring #2 AAPL : « High volume indicates a supply of stock becoming available below the Support zone. »
  - Spring #3 SCHW : « The volume is low, not rising above the recent low levels. » ; « When the price Springs on low volume the stock can be bought right away. »
- Wyckoff Analytics, extrait du Wyckoff Trading Course Part 1 sur la détection algorithmique (daté 6/3/2025) [V] — [WA, « Identifying Wyckoff Springs with Algorithms »](https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/) :
  - « A valid spring cannot occur where the bar is closing at the low of the date. »
  - La barre de spring peut clôturer sous 50 % de son spread et rester valide.
  - Lookback de base de 15 barres (20 ou 25 à tester).
  - Un écart de plus de 10 % entre creux successifs est « an unacceptable scenario », le stop devenant impraticable.
  - « Effective springs typically show volume coming in as price penetrates the support level ». **Tension apparente** avec la préférence pour le « low-volume spring » ; elle se résout par la typologie : un spring volumique (#2) appelle un test.

**Test du spring (secondary test du spring)**
- Fraser : « If there is a low volume move towards the Support Line (the Test), that indicates the prior supply was absorbed. » ; « High volume at the lows normally involves a retest as it tells the C.O. that supply is still present. » [V] — [Fraser, Francis Bacon](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)
- Fraser : « This is a Spring #2 which must be tested and it is the next day. » ; « The next day on the Test, the price remains above the low and the volume is less than on the Spring day. » [V] — [Fraser, Springing into Action](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)
- Fraser : « This is a Spring #2 which must be tested, and it is in the two days immediately following the Spring. » ; « The test of a Spring #2 can be bought. » (1er avril 2016) [V] — [Fraser, « How to Determine the Best Trade Entry Points »](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/)
- Fraser : « The attempt to 'test' the low bar arrives two bars later and on much lower volume. This bar or the next bar can be bought. » (15 avril 2016) [V] — [Fraser, « Wyckoff Buy Strategies »](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/)
- Wyckoff SMI (20 juin 2015) : « Most part Springs need to be tested. The only exception involves a #3 Spring. » ; « A successful Secondary Test is the final action that confirms a Spring was successful. » ; « If there is to be a successful Secondary Test the supply must dry up. This would be shown on the charts as a reaction on reduced price spread and lower volume. » [V] — [Wyckoff SMI, « Testing The Spring »](https://wyckoffsmi.com/testing-the-spring/)
- WA, méthode en cinq étapes (étape 4) : « do the nine buying tests indicate that supply has been successfully absorbed, as evidenced further by a low-volume spring and an even lower-volume test of that spring? » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- WA (article daté 9/28/2026) : « A test of that spring on even lower volume adds to the case that big buyers have soaked up the supply. » [V] — [WA, « Wyckoff Reaccumulation vs Distribution »](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)
- Rutigliano (WA 2020) : « A successful test of a spring, shakeout or LPS makes a higher low on lower volume. » [V] — [slides WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)
- Weis [NV] : selon un résumé de recherche d'une copie tierce du livre, le chapitre 5 « Springs » (pp. 73-94, Wiley 2013) dirait « When the initial breakdown occurs on heavy volume, the propensity exists for a secondary test. Springs following a low‐volume breakdown, like the two on the cocoa chart, are tested less often. » Une recherche en phrase exacte n'a pas retrouvé ce verbatim. Référence du livre : [Weis, *Trades About to Happen*, Wiley](https://onlinelibrary.wiley.com/doi/book/10.1002/9781118656389)

**« LPS de Phase C » (test plus haut sans spring), LPS de Phase D, BU/BUEC : une terminologie divergente**
- WA : « the testing of supply can occur higher up in the TR without a spring or shakeout; when this occurs, the identification of Phase C can be challenging. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Fraser : « a Last Point of Support is the final test (higher low) of the Accumulation area. » [V] — [Fraser, Best Trade Entry Points](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/) ; « An LPS makes a higher low and then turns upward. » ; « The Spring is easier to identify because the Spring makes a minor new price low. » [V] — [Fraser, Wyckoff Buy Strategies](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/)
- WA : LPS = « the low point of a reaction or pullback after a SOS. Backing up to an LPS means a pullback to support that was formerly resistance, on diminished spread and volume. On some charts, there may be more than one LPS » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) ; Rutigliano : à l'LPS, « price does not fall below this level again during the TR. » [V] — [slides WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)
- Villahermosa (en espagnol) [V] — [Villahermosa, « Last Point of Support », tradingwyckoff.com](https://tradingwyckoff.com/last-point-of-support/) :
  - Le retracement qui confirme la cassure « se etiqueta como Last Point of Support (LPS) o » « Back Up to the Edge of the Creek (BUEC) ». Il assimile donc l'LPS de Phase D au BUEC.
  - Critères du test de confirmation : « el movimiento de test lo haga con velas de rango estrecho, entrelazadas y con volumen bajo » ; « Que el precio no reingrese al rango ».
  - Volume : « Volumen alto en el test indica cautela » ; « deberíamos esperar a que se desarrollaran sucesivos test sobre la zona ».

**SOS / JAC (« jump across the creek »)**
- WA : SOS = « a price advance on increasing spread and relatively higher volume. Often a SOS takes place after a spring, validating the analyst’s interpretation of that prior action. » ; « During Phase D, the price will move at least to the top of the TR. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Pruden & vL : « A jump is a relatively wider price-spread move made on comparatively higher volume that penetrates outer resistance or support. » ; le JAC « is a good sign if done on good spread and volume – a sign of strength (SOS). » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- Rutigliano : SOS = « a rally over resistance on increasing spread, volume, and velocity. » [V] — [slides WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)
- Villahermosa : SOS = « Breakout of the top of the range (Creek) with high volume and wide candles. » [V] — [Villahermosa, « Wyckoff Method 2026: Complete Guide and Trading Plan »](https://tradingwyckoff.com/en/wyckoff-method/)

**LPS de Phase D / BU / BUEC (test de la cassure)**
- Pruden & vL [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) :
  - « A backup is a test that immediately follows the jump – a relatively narrow price-spread reaction or rally on comparatively lighter volume that tests and confirms the legitimacy of the preceding jump action. »
  - BU vers un LPS = « a pull back to support (that was resistance) on diminished spread and volume after a SOS. This is good place to initiate long positions or to add to profitable ones. »
  - « A series of SOS’s and LPS’s is good evidence that a bottom is in place and Price Markup has begun. »
  - BUEC sur Nokia : « The pullback comes on a relatively smaller price spread and shrinkage of volume, thus showing that supply cannot regain control. »
- WA : le BU (métaphore d'Evans) représente « both short-term profit-taking and a test for additional supply around the area of resistance » et « can take on a variety of forms, including a simple pullback or a new TR at a higher level. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Villahermosa : en Phase D, « it is essential that price holds on the other side of the structure and no immediate re-entry is generated. » [V] — [Villahermosa, « Wyckoff Phases »](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)

**Réaccumulation (« stepping stone »)**
- WA : « In a re-accumulation TR (which occurs during a longer-term uptrend), the points representing PS, SC and ST are not evident in Phase A. Rather, in such cases, Phase A resembles that more typically seen in distribution (see below). Phases B-E generally have a shorter duration and smaller amplitude than, but are ultimately similar to, those in the primary accumulation base. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Fraser, sur la SSR (Stepping Stone Reaccumulation) : son bas intervient « in the first third to half of the total time spent in the SSR » ; « lower peaks are followed by a Spring. » ; « The breakdown in the late stages of the SSR is a Spring. » [V] — [Fraser, Springing into Action](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)
- WA 2026 : « In reaccumulation, each drop toward support tends to come on less volume than the drop before it. » [V] — [WA, Reaccumulation vs Distribution](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)

**Distribution (miroir) : ST/UT, UTAD, test de l'UTAD, SOW / chute à travers la glace, test de la glace, LPSY**
- WA [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) :
  - ST : « For a top to be confirmed, supply must outweigh demand; volume and spread should thus decrease as price approaches the resistance area of the BC. An ST may take the form of an upthrust (UT) »
  - UT : « a price move above TR resistance that quickly reverses and closes in the TR. This is a test of the remaining demand. »
  - UTAD : il « provides a deﬁnitive test of new demand after a breakout above TR resistance »
  - « Often demand is so weak in a distribution TR that price does not reach the level of the BC or initial ST. In this case, Phase C's test of demand may be represented by a UT of a lower high within the TR. »
  - SOW : « a down-move to (or slightly past) the lower boundary of the TR, usually occurring on increased spread and volume »
  - LPSY : « After testing support on a SOW, a feeble rally on narrow spread shows that the market is having considerable difﬁculty advancing. »
  - Phase D : « The evidence that supply is clearly dominant increases either with a clear break of support or with a decline below the mid-point of the TR after a UT or UTAD. »
  - Phase E : « Once TR support is broken on a major SOW, this breakdown is often tested with a rally that fails at or near support. »
- Pruden & vL [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) :
  - UTAD : « If this breakout occurs on light volume with no follow through or on heavy volume with a breakdown back into the centre of the trading range, then this is more evidence that the TR was Distribution not Accumulation. » ; « Should the move to new high ground be on increasing volume and “relative narrowing spread” and then return to the average level of closes of the TR, this would indicate lack of solid demand »
  - « The magnitude of the upthrust can be determined by the extent of the price move to new highs and the relative level of volume on that movement. »
  - LPSY : « Volume may be light or heavy, showing weak demand or substantial supply. »
  - Test de la glace : « after a break through the ice, a rally attempt is thwarted at the ice’s surface (now resistance). The rally meets a last wave of supply before markdown ensues. »
  - Le SOW « will usually occur on increased spread and volume as compared to the rally to point 9 ».
- Fraser (intraday, 15 janv. 2017) : « Under a (short-term) bearish scenario, if ICE or Support is broken there is typically a pause. » ; « Then if price becomes listless and cannot lift (and stays under Support) expect a markdown to follow. » [V] — [Fraser, « Enjoying the Short Term View »](https://articles.stockcharts.com/article/articles-wyckoff-2017-01-enjoying-the-short-term-view)
- Villahermosa : entrée conservatrice « Test after the shakeout: known as the Spring test (bearish shakeout) or the Upthrust test (bullish shakeout). » [V] — [Villahermosa, guide](https://tradingwyckoff.com/en/wyckoff-method/)

### Inferences
Les checklists ci-dessous sont des **propositions de synthèse**. L'ordre de lecture suit la convention du trader : volume, puis OI en coin, puis métriques tierces. Les proxys chiffrés viennent des implémentations (Q5) et non de la littérature primaire.

- **Test de Phase A (ST du SC)** :
  1. Le volume du ST est inférieur à celui du SC (critère primaire) et le spread plus étroit que celui du SC.
  2. Le low du ST est ≥ au low du SC ; une légère cassure est tolérée selon Fraser, mais elle est « suspecte » pour WA et Villahermosa.
  3. Pour le trader : un OI coin plat ou en repli sur le ST signifie qu'il n'y a pas de nouveaux shorts agressifs. C'est une extension, non sourcée, au cadre du trader.
- **Tests de Phase B** : on lit le **gradient**. Les creux successifs doivent porter de moins en moins de volume (WA 2026). Un « ST as SOW » (creux plus bas, volumique) affaiblit l'hypothèse d'accumulation et rallonge la Phase B, sans l'invalider.
- **Spring** :
  1. Pénétration du low de la plage puis clôture à l'intérieur, sur la même barre ou rapidement.
  2. Classer par volume et profondeur : volume faible + pénétration faible = #3, entrée possible dès la réintégration ou une barre de demande ; volume en expansion = #2, attendre le test ; cassure profonde et volumique = #1, attendre un test (SMI) ou ne pas acheter (Fraser).
  3. La barre ne clôture pas au plus bas (WA).
- **Test du spring** :
  1. Il survient peu après : de 1 à 2 barres jusqu'à « days or weeks ».
  2. Son low est au-dessus de celui du spring.
  3. Son volume est inférieur à celui du spring (critère primaire), et idéalement à la MA.
  4. Son spread est plus étroit que celui du spring.
  5. Une barre ou un SOS de demande suit (« SOS shortly after … validates »).
- **LPS / BU / BUEC** :
  1. Pullback vers l'ancienne résistance (le creek) sur un spread et un volume réduits.
  2. Pas de réintégration de la plage (Villahermosa).
  3. Il succède à un SOS de spread large et volumique.
  4. Si le volume du test est élevé, attendre des tests supplémentaires.
- **UTAD et test de l'UTAD** (miroir) :
  1. Dépassement du haut de la plage puis retour sous la résistance.
  2. Soit faible volume sans suivi, soit fort volume avec retour au centre de la plage.
  3. Puis un rally de test plus bas, sur un spread et un volume réduits (LPSY).
  4. Une cassure sous le milieu de la plage renforce la thèse distributive.
- La référence de volume la plus défendable est **relative à l'événement testé** : vol_test < vol_spring, vol_ST < vol_SC. Le critère ×MA20 reste un filtre secondaire.

### Gaps
- Page « Spring » de Villahermosa ([tradingwyckoff.com/en/spring-shakeout](https://tradingwyckoff.com/en/spring-shakeout/)) inaccessible (vérification anti-bot) : sa typologie du spring n'est pas vérifiée. Ses critères viennent ici de ses pages ST, LPS, Phases et Guide.
- Livre de Weis non consulté (Wiley 403, copie tierce bloquée) : toutes ses citations sont [NV].
- *The Three Skills of Top Trading* de Pruden n'a pas été consulté directement. Les Nine Tests viennent de l'adaptation WA de cet ouvrage (pp. 136-37).
- Aucune source primaire ne chiffre la position de clôture (CLV) d'un test, la pénétration en ATR ou la durée maximale entre spring et test (en dehors des exemples « next day », « two days », « two bars »).
- Aucun critère de test signé par Bogomazov n'a été trouvé. Il est co-auteur de l'article S&C 2014 et co-présentateur du cours crypto.
- La phrase « BUEC : the shallower the pullback, the better » attribuée à Fraser n'a été vue que dans un résumé de recherche [NV].

## Q2 — Quelles règles d'entrée, de stop, d'objectif, de construction et de gestion de position recommandent les praticiens (spring, test, LPS, BU ; shorts UTAD/LPSY) ? Comment utilisent-ils le décompte P&F et le ratio 3:1 ?

### Takeaway
- **Entrées canoniques** (Fraser) : quatre points, à savoir spring et test du spring, LPS (souvent plusieurs), BU après le saut hors de la plage, cassure au-dessus du haut du BU/SOS.
- **Stops** : juste sous le spring, l'LPS ou le BU.
- **Construction** en environ trois tranches, chacune à un prix plus haut (« only average up »). On n'ajoute que si les positions initiales sont gagnantes.
- **Objectifs** : décompte P&F horizontal depuis l'LPS, du plus conservateur au plus agressif, ajouté au plus bas de la plage ou à mi-chemin. Le résultat sert de zone « stop, look and listen ».
- **Filtre de sélection** : potentiel ≥ 3 fois le risque (Buying Test #9).
- **Côté short** : WA et Pruden recommandent d'attendre l'LPSY de Phase D plutôt que de shorter chaque UT.
- **Villahermosa** structure le plan : stop d'invalidation de scénario, objectif minimal égal à la hauteur de la plage, demi-sortie à la première zone de liquidité, stop au point mort à 50 % du chemin.

### Cited Findings

**Points d'entrée et stops (Fraser)**
- Fraser [V] — [Fraser, Best Trade Entry Points](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/) :
  - « Four junctures in Phases C and D are ideal for trade entry. » : 1) « Spring and Test of the Spring » ; 2) « Last Point of Support (there are often multiple LPS points) » ; 3) « Backup (BU) after the jump up and out of the Accumulation » ; 4) « Breakout above the high of the BU/SOS (Sign of Strength). »
  - « Stop placement can go just below the Spring, LPS, or BU. » ; « place a stop loss order in a zone that has a very low potential for being triggered » ; « have the trade work right away ».
- Fraser, entrées sur spring [V] :
  - « Wyckoffians will buy a low volume Spring immediately and place stops below the lowest price. » — [Francis Bacon](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)
  - « Buy Apple on the Test of the Spring #2 and place the stop under the lowest price. » ; « Also stock can be bought on the demand bars that follow the turn off the Spring. » ; « Buy the Spring or any of the demand bars that follow. » ; « Place stops under the low of the Spring day. » — [Springing into Action](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)
- Fraser, LPS et BUEC [V] — [Fraser, Wyckoff Buy Strategies](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/) :
  - « After the LPS entry, place a stop under the low of the LPS, or under the prior low » ; « If the first LPS was missed, the second LPS is a fine place to initiate the campaign. »
  - « Now that the stock has jumped out, it may need a pause in the form of a BUEC or a Stepping Stone Reaccumulation before the trend can continue. »
  - Absorption au point bas : « Note the very high volume on the low bar, this is absorption and good demand. »

**Construction de position**
- Fraser : « Initiating and building a position in a stock using the Wyckoff Method usually occurs in three tranches. » ; « Each purchase or tranche of stock must be at a higher price than the prior purchase. » ; « Only average up a winning position. » ; « This is an excellent system for averaging up winning trades while placing trailing stops at tactical levels » [V] — [Fraser, Best Trade Entry Points](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-how-to-determine-the-best-trade-entry-points/)
- Pruden & von Lichtenstein [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) :
  - « The shakeout at point 8 on our Schematic 1 represents our first prescribed place to initiate a long position. The secondary test at point 10 is better, since a low volume pullback and a specific low risk stop or danger point at point 8 gives us greater evidence and more confidence to act. »
  - « At each of points 8, 10, 12, and 14 we may take positions and use point and figure counts from these points to calculate price projections and help us to determine our reward/risk prior to establishing our speculative position. »
  - « The Wyckoff method instructs you to buy after a backup following an upward jump (a sign of strength) or to sell short after a backup following a downward jump (a sign of weakness). Also according to Wyckoff, you should not buy breakouts because that would leave you vulnerable to swift moves in the opposite direction if the breakout turned out to be false. »
  - Phase D : « It is here that our best opportunities to add to our position exist, before the stock leaves the TR. »
  - « It is important that additional short positions be added or pyramided only if our initial positions are in profit. »
  - Exemples Nokia : « A long position could have been initiated during the pull back test following JAC at around 104 with a protective stop loss order entered below the support level, around 95. » ; BUEC : entrée « in the vicinity of 110115 [110-115] » avec « a sell stop order just below the 100 level ».
- WA [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) :
  - Spring à faible volume : « a good time to initiate at least a partial long position » ; Phase D : « LPSs in this phase are generally excellent places to initiate or add to proﬁtable long positions. »
  - Méthode en cinq étapes : « Put your stop-loss in place and then trail it, as appropriate, until you close out the position. »

**Shorts (UT, UTAD, LPSY, test de la glace)**
- WA [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) :
  - « Aggressive traders may wish to initiate short positions after a UT or UTAD. The risk/reward ratio is often quite favorable. However, the “smart money” repeatedly stops out traders who initiate such short positions with one UT after another, so it is often safer to wait until Phase D and an LPSY. »
  - Phase D : « these LPSYs represent excellent opportunities to initiate or add to proﬁtable short positions. »
  - Phase E (test de la cassure) : « This also represents a high-probability opportunity to sell short. » ; « Traders who have taken short positions can trail their stops as price declines. »
- Pruden & vL : « Point 11 on both distribution Schematics 2 and 3 give us our last opportunity to cover any remaining longs and our first inviting opportunity to take a short position. An even better place would be on the rally testing point 11, because it may give us more evidence (diminished spread and volume) and/or a more tightly defined danger point. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)

**Filtre reward/risk 3:1 et décompte P&F**
- Buying Test #9 : « Estimated upside proﬁt potential is at least three times the loss if the initial stop-loss were hit – P&F and bar charts ». Selling Test #9 en miroir : « Estimated downside proﬁt potential is at least three times the risk for if the initial stop-order were hit ». Source : « Adapted from Pruden H (2007) The Three Skills of Top Trading… pp. 136-37 ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Guide de décompte P&F (WA/ChartSchool) [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) :
  - « After identifying a sign of strength (SOS) towards the right side of the TR on the bar chart, locate the last point at which support was met on a reaction—the last point of support (LPS). Locate this point on your P&F chart also and count from right to left at the price level of the LPS, taking your most conservative count ﬁrst and moving further to the left as the move progresses. »
  - « Never add only part of a P&F phase to your count. » ; « the ﬁrst phase can consist of the P&F count from the LPS back to the spring, while the second phase covers the count from the spring to a clearly deﬁned ST. »
  - « the LPS often appears at the original level of preliminary support or the SC. When the LPS occurs at either of these levels, this tends to validate the count. » ; « A spring may also serve as the LPS from the perspective of the P&F count. »
  - « add the P&F count to the exact low of the trading range in which the count is being measured, as well as to the halfway point between the low and the price level of the count line »
  - Les objectifs sont des points où l'on doit « “stop, look and listen.” These targets should never be looked upon as exact points of where a trend will change »
  - « stepping stone conﬁrming count » : utiliser une case plus petite pour mesurer les plages de réaccumulation.
- Pruden, Fraser & Bogomazov (*Stocks & Commodities* V.32:8, 2014) [V] — [« The Composite Man’s Bull Market Campaign » (PDF)](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/V32C08822PRUD.pdf) :
  - « After seeing a sign of strength (SOS), locate the last point of support (LPS) on a reaction, and count from right to left. »
  - « Counts are only points at which to stop, look, and listen. »
  - « If the last point of support (LPS) comes at such a level of climax, it usually makes it a more valid count. »
  - « The spring, which in this case is a number 3 spring or the secondarytest of a number 2 spring, often constitutes the sign of strength and the last point of support in the same action ».
  - Exemple DJIA : terminal shakeout en mars 2009, LPS vers 8 100, décompte de « 11,100 DJIA points for upside price projections of 17,600–19,200 ».
- Fraser : « To take a count, identify the LPS on the bar chart, then find that point on the PnF chart and count to the left. » ; « Take a conservative count. If you deem the reward to risk to be suitable to your objectives, make the trade. » ; « From the LPS, ALB has a count estimate to $86. » [V] — [Fraser, Wyckoff Buy Strategies](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/)

**Plan de trade de Villahermosa**
- Plan de trade [V] — [Villahermosa, guide](https://tradingwyckoff.com/en/wyckoff-method/) :
  - Entrées :
    - Phase C agressive : « Direct entry on the shakeout (Spring / UTAD) » ; Phase C conservatrice : test du shakeout.
    - Phase D : « Price has already developed SOS/SOW and pulls back to test the broken level from outside (LPS/LPSY/BUEC). »
    - Phase E : « The test offers the opportunity to join the already consolidated move ».
  - Stops :
    - Trois niveaux d'invalidation : déclencheur, « At the opposite extreme of the intention candle that generated the entry. » ; scénario, « below the low of the Spring in a buy, above the high of the UTAD in a sell » ; structurel, « On the other side of the entire complete structure. »
    - Par type d'entrée : LPS/BUEC « Below the broken resistance level. » ; LPSY « Above the broken support level. »
  - Objectifs :
    - Hauteur de plage : « should be at least equivalent to the height of the range »
    - Décompte P&F : « Classic Wyckoff estimates that effect with Point & Figure counts » mais « the effect of the cause cannot be known in advance with sufficient precision »
    - Liquidité : « the next relevant high in a buy, the next low in a sell »
  - Gestion :
    - « closes half the position at the first liquidity zone and lets the rest run » ; « when price covers 50% of the way to the target, move the stop to breakeven »
    - Risque par qualité de setup : 2 %, 1 % ou 0,5 % ; taille = « (Capital × % risk) ÷ (distance to Stop Loss × point value) »
    - « The structure defines the ratio, never the other way around. » ; « When the reading is not 10/10, lower the size and demand a better risk/reward ratio instead of discarding the trade. »
  - FAQ : « TP1 is placed at the resistance of the range (the Creek)... where half the position is closed ».
- Villahermosa, LPS (espagnol) [V] — [tradingwyckoff.com LPS](https://tradingwyckoff.com/last-point-of-support/) :
  - « esperar a que aparezca una vela de fortaleza (SOSbar) y colocar una orden de entrada a mercado »
  - « Coloca o mueve el stop loss de la posición entera bajo el Last Point of Support y la línea de resistencia (Creek) rota. »
  - Acheter pendant le SOS : « esta acción no es correcta, lo más recomendable es esperar a la siguiente reacción (LPS) »
  - L'LPS après un shakeout offre le « Mejor ratio riesgo/recompensa. »
  - La FAQ évoque un objectif d'au moins 3:1 et un stop juste sous le low de l'LPS (absent du corps).
- Phase A : « Phase A will not be operationally useful for seeking new trades. » [V] — [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)

**Divergences notées dans les sources**
- Sur l'achat de cassure : Pruden et vL écrivent « should not buy breakouts » ; la 4ᵉ entrée de Fraser (« Breakout above the high of the BU/SOS ») est postérieure au BU, donc à un test.
- Sur le stop LPS : Fraser le place sous le low de l'LPS ou le low antérieur ; Villahermosa sous l'LPS **et** le creek cassé ; l'exemple Nokia de Pruden et vL, plus large, sous le support de la plage.

### Inferences
- Gabarit de plan par setup, à adapter à la règle du trader selon laquelle chaque niveau doit être justifié par l'événement ou la borne qui le définit :
  - **Test du spring** : déclencheur = clôture d'une barre de demande après un test plus haut à volume sec ; stop = sous le low du spring (le mouvement qui doit tenir) ; objectif 1 = haut de la plage ou de l'AR (le creek) ; objectif 2 = décompte P&F depuis l'LPS ; invalidation = clôture sous le low du spring.
  - **LPS / BUEC** : déclencheur = barre de demande sur un pullback sec qui tient au-dessus du creek ; stop = sous le low de l'LPS et sous le creek cassé (le retour dans la plage invalide le JAC) ; objectif = décompte P&F, en vérifiant le filtre ≥ 3R.
  - **LPSY / test de la glace (short)** : stop = au-dessus du haut du rally de test, ou au-dessus de la glace cassée ; objectif = décompte P&F vers le bas.
- Pour le décompte P&F en crypto, la taille de case peut se fixer en pourcentage ou en ATR, ce qui éviterait les tailles en points calibrées pour les actions. Voir Q6 : Rutigliano utilise un barème à 10 %, Fraser un barème ATR(20).
- Le filtre 3:1 doit s'appliquer **avant** l'entrée, au premier objectif conservateur, et non à l'objectif agressif.
- La construction en tranches correspond naturellement aux quatre points d'entrée de Fraser : tranche 1 au test du spring, tranche 2 à l'LPS, tranche 3 au BU ou à la cassure du haut du BU. Chaque ajout doit être plus haut et la position déjà gagnante.

### Gaps
- Aucune source ne chiffre la taille des tranches : Fraser parle de « three tranches », sans pourcentages.
- Aucune source primaire ne donne de marge de stop en ATR. Les implémentations utilisent 1,0 ATR (backtest de papan-saham [NV]) ou 1,5 ATR (article MQL5), voir Q5.
- Le « 3:1 » n'a été vérifié que dans l'adaptation de Pruden (2007) reproduite par WA, pas dans le texte du cours Wyckoff/SMI original.
- Les règles de sortie partielle de Fraser et de Pruden (au-delà du stop suiveur et du « stop, look and listen ») ne sont pas formalisées.

## Q3 — Quels signaux d'alerte précoce indiquent qu'un test a échoué ou que l'hypothèse d'accumulation est fausse (redistribution) ?

### Takeaway
Les signaux d'échec documentés tiennent d'abord au **volume au mauvais endroit** :
- volume lourd sur la cassure du support, qui annonce une reprise de la baisse ;
- offre importante qui ressurgit sur un test ;
- volume des baisses qui croît à mesure que la plage vieillit (signature de distribution) ;
- test qui fait un plus-bas sous le spring avant que la demande n'arrive.

Viennent ensuite les **échecs de position** : ST sous le SC, échec à atteindre le haut de la plage, retour dans la plage après un SOS ou un JAC (le JAC devient upthrust), échec à reprendre la « glace » en deux tentatives. Le remède commun est de **ne pas ajouter**, de couper la position initiale et de laisser la Phase B s'allonger.

### Cited Findings
- Volume sur la cassure : « Heavy supply here will usually mean a renewed decline. Moderate volume here may mean more testing of support and to proceed with caution. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- Offre sur un test : « If considerable supply emerges on a test, the market is often not ready to be marked up. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- ST sous le SC : « If the ST goes lower than that of the SC, one can anticipate either new lows or prolonged consolidation. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf). Villahermosa : sous le SC, « some imbalance in favor of sellers » [V] — [tradingwyckoff.com ST](https://tradingwyckoff.com/en/secondary-test/)
- Test raté : « If the Test fails, the downtrend resumes. » ; « The bigger the magnitude of the prior trend, the more times it may need to be Tested before it can be reversed. » [V] — [Fraser, Action – Test](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)
- Test de mauvaise qualité : « A poor quality Secondary Test means the stock or index reacted below the Spring before demand came into the market. » ; dans ce cas, « the process must be repeated and the Wyckoff Wave must find support above point G. » [V] — [Wyckoff SMI, Testing The Spring](https://wyckoffsmi.com/testing-the-spring/)
- Shakeout #1 : « A Shakeout (#1 Spring) is a failed Spring. » ; « The Number 1 Spring is actually a Shakeout that is a complete breakdown. » ; « It should not be bought. » [V] — [Fraser, Francis Bacon](https://articles.stockcharts.com/article/articles-wyckoff-2015-06-francis-bacon-reveals-the-nature-of-trends)
- Absence du motif de Phase D : faute de SOS sur spread élargi et volume croissant suivis de LPS sur spread et volume réduits, « If this pattern does not occur, then we are advised not to add to our position and look to close our original position until we have more conclusive evidence that markup is beginning. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- Réaccumulation ou distribution ? [V] — [WA, Reaccumulation vs Distribution (9/28/2026)](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/) :
  - « In reaccumulation, each drop toward support tends to come on less volume than the drop before it. » ; « In distribution, volume stays heavy on the way down and often grows as the range gets older. »
  - Avertissement contre les shorts prématurés : « it's often safer to wait for Phase D and an LPSY. »
  - Paraphrases de l'article : la Phase A seule tranche rarement la question ; la Phase A d'une réaccumulation peut ressembler à un début de distribution ; la Phase A d'une redistribution peut ressembler à un début d'accumulation (ventes paniques volumiques).
- Redistribution : « In a redistribution TR within a larger downtrend, Phase A may look more like the start of an accumulation TR (e.g., with climactic price and volume action to the downside). » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Selling Tests (signaux distributifs à surveiller dans une plage supposée d'accumulation) : #2 « Activity bearish (volume decreases on rallies and increases on reactions) » ; #4 « Stock weaker than the market » ; #6 « Lower highs » ; #7 « Lower lows ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Effort vs résultat : « huge volume on a rally with minimal price advance in a distribution trading range demonstrates a stock's inability to rally because of the presence of signiﬁcant supply ». Côté haussier : « In Reaction #3, the swing size decreases, yet volume increases… showing the presence of large buyers absorbing supply ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Glace et creek [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf) :
  - « A failure by the Boy Scout to reach the upper resistance level of the Trading Range would be a warning of potential weakness. »
  - « The Boy Scout has two chances to get back above the ice (i.e., creating a bullish “Spring” situation)… If on this second attempt, the Boy Scout again fails to penetrate above the ice, he would be most likely to sink downward and drown ».
  - « The presence of a Wyckoff principle like a selling climax (SC) doesn’t confirm that accumulation is occurring in the TR, but it does strengthen the case for it ».
- Échec de cassure et retour dans la plage [V] :
  - Villahermosa : « the breakout could perfectly well fail, turn into an Upthrust and generate a bearish move. » ; « if a shakeout against you appears, evaluate closing. » — [guide](https://tradingwyckoff.com/en/wyckoff-method/)
  - Issues d'échec listées par Villahermosa : « Large traders give up on the campaign. » ; « Phase B continues to extend until complete absorption occurs. » ; « The breakout attempt fails and a new shakeout develops instead. » ; en Phase D, « price holds on the other side of the structure and no immediate re-entry is generated » est « essential ». — [Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)
- Test volumique sur un LPS : « Volumen alto en el test indica cautela » ; un mouvement correctif à volume élevé et rangs larges « cancela la probabilidad de que el primer movimiento sea de ruptura ». [V] — [tradingwyckoff.com LPS](https://tradingwyckoff.com/last-point-of-support/)
- Shorts piégés en distribution : « the “smart money” repeatedly stops out traders who initiate such short positions with one UT after another ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Faux signal inverse : « Shakeouts may also occur once a price advance has started, with rapid downward movement intended to induce retail traders and investors in long positions to sell their shares to large operators. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Spring raté, sans invalidation : le schéma de réaccumulation Bitcoin de Rutigliano place un « FAILED SPRING » en Phase B, suivi d'un « UA », d'un « MSOS » et d'un « BU ». [V] — [slides WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)
- Raccourcissement de la poussée (SOT), source secondaire : « each successive push to a new high or low gains less ground than the one before ». La source exige au moins trois poussées. Volume lourd = effort absorbé par le camp opposé ; volume léger = retrait des participants. Le SOT « describes deceleration, not reversal » et appelle à attendre un changement de caractère. Concept attribué à Weis (2013). [V pour la page] — [LuxAlgo, « Shortening of the Thrust »](https://www.luxalgo.com/library/concept/shortening-of-the-thrust/)
- Weis [NV] : « Shortening of the thrust is my favorite setup. It involves a change in behavior followed by a low-volume pullback. » (résumé de recherche d'une copie Scribd de son livret « Trade Setups », non vérifié).

### Inferences
- **Alertes précoces vérifiables par barre**, à appliquer dans l'ordre volume, puis OI en coin, puis métriques tierces :
  1. Le volume du test est ≥ à celui du spring ou du SC.
  2. Le test casse le low du spring avant qu'apparaisse une barre de demande.
  3. Le volume moyen des creux successifs de Phase B est croissant (gradient inverse).
  4. Après le SOS, le premier pullback se fait sur un spread large et un volume en hausse, ou réintègre la plage.
  5. Le rally depuis le spring n'atteint pas le haut de la plage (le « Boy Scout » échoue).
  6. Deux tentatives de reprise de la glace échouent après une cassure.
- Dans le cadre du trader (non sourcé dans la littérature Wyckoff), un test qui casse le spring avec un OI coin en hausse indiquerait l'ouverture de nouveaux shorts. Ce serait le pendant, sur dérivés, de « considerable supply emerges on a test ». À confirmer par le ratio L/S, le funding et les liquidations si le prix cale.
- Un spring raté n'invalide pas forcément la plage (exemple de Rutigliano, ST1/ST2 « could be a Spring » chez Fraser, « Phase B extension » chez Villahermosa). Il **requalifie** l'événement en test de Phase B, ce qui repousse le timing. C'est cohérent avec la règle top-down du CLAUDE.md : tenir les deux scénarios jusqu'à la cassure.

### Gaps
- Pas de taux d'échec mesuré pour chaque signal d'alerte (voir Q5) ; les critères restent qualitatifs.
- Le texte original de Weis sur le SOT et sur l'« absorption » n'a pas été vérifié.
- Aucune source primaire ne définit un « délai d'expiration » (combien de barres sans SOS après un spring avant d'abandonner). Seules les implémentations en fixent un (MQL5 : fenêtre LPS de 8 barres ; systematic1 : spring à 30 barres et SOS à 10 barres maximum).

## Q4 — Comment les praticiens diagnostiquent-ils l'état et la maturité d'une consolidation à partir de la séquence de tests (Nine Buying Tests, gradient de volume, temps) ?

### Takeaway
Le diagnostic repose sur quatre éléments, à lire avec trois points de contexte.
1. Une **checklist binaire** : les Nine Buying ou Selling Tests (Pruden d'après Wyckoff).
2. Le **gradient de volume et d'amplitude** à travers les tests successifs : oscillations larges et volumiques en début de Phase B, puis creux de plus en plus secs et plus-bas montants.
3. La **durée relative** des phases : la Phase B est plus longue que A et C, et une Phase B courte trahit l'urgence.
4. La **séquence d'événements accomplie** : SC, AR et ST ont-ils eu lieu, y a-t-il eu un spring ou un test en Phase C, un SOS puis un LPS.

Contexte :
- La maturité « springboard » se confirme quand un spring à faible volume est suivi d'un test à volume encore plus faible, puis d'un SOS.
- La cause (décompte P&F) doit suffire pour l'objectif visé.
- En réaccumulation, les phases sont plus courtes et plus étroites.

### Cited Findings
- Les Nine Buying Tests, verbatim (adaptés de Pruden 2007, pp. 136-37) [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf) :
  1. « Downside price objective accomplished – P&F chart »
  2. « Preliminary support, selling climax, secondary test - Bar and P&F charts »
  3. « Activity bullish (volume increases on rallies and diminishes during reactions) – Bar chart »
  4. « Downward stride broken (that is, supply line or downtrend line penetrated) - Bar or P&F chart »
  5. « Higher lows »
  6. « Higher highs »
  7. « Stock stronger than the market (that is, stock more responsive on rallies and more resistant to reactions than the market index) - Bar chart »
  8. « Base forming (horizontal price line) – Bar or P&F chart »
  9. « Estimated upside proﬁt potential is at least three times the loss if the initial stop-loss were hit – P&F and bar charts »
  - Les Selling Tests en sont le miroir, avec « Crown forming (lateral movement) - P&F chart » en #8.
  - Rôle des tests : « the nine tests deﬁne the line of least resistance in the market. » ; ils « help delineate when a trading range is drawing to a close ». Seuls les tests #1 et #9 « could only be met through the use of P&F charts ».
- Étape 3 (cause suffisante) : « choose stocks that are under accumulation or re-accumulation and have built a sufﬁcient cause to satisfy your objective. » ; étape 4 (prêt à partir) : « a low-volume spring and an even lower-volume test of that spring ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Gradient de Phase B :
  - WA : « Early on in Phase B, the price swings tend to be wide and accompanied by high volume. As the professionals absorb the supply, however, the volume on downswings within the TR tends to diminish. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
  - Pruden et vL : « In the early stages of Phase B, the price swings tend to be rather wide, and volume is usually greater and more erratic. As the TR unfolds, supply becomes weaker and demand stronger as professionals are absorbing supply. The closer you get to the end or to leaving the TR, volume tends to diminish. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- « Accumulation Gradient of Rising Bottoms » (Pruden et vL, schéma ajouté) : « fewer and fewer sellers remain to propel stocks downward in price. As a consequence, the downwaves become shorter and shorter in length (the bottoms rise) and the Composite Man as a result accumulates an increasing line of stock. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- Gradient du volume des baisses (réaccumulation contre distribution) : « In reaccumulation, each drop toward support tends to come on less volume than the drop before it. » ; « In distribution, volume stays heavy on the way down and often grows as the range gets older. » ; « Phases B through E of a reaccumulation generally last less time and swing less than in the first accumulation base. » [V] — [WA 2026](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)
- Durée relative des phases :
  - Villahermosa : « In proportional terms we want this phase [B] to be longer than Phases A and C. » ; si la Phase B est plus courte, « it will denote urgency on the part of the traders. » [V] — [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)
  - Villahermosa, guide : « Phase B should consume, at a minimum, a proportionally equal or greater amount of time than Phase A. » [V] — [guide](https://tradingwyckoff.com/en/wyckoff-method/)
  - FAQ : la Phase B est « The longest phase (40-70% of total time) » et les bougies passent à des « ranges 50-60% smaller toward the end of Phase B » (absent du corps). [V pour la présence ; fiabilité incertaine] — [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)
  - Pruden et vL : « distribution is generally accomplished in a shorter time period than accumulation. » [V] — [Pruden & vL PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- Bornes des phases selon Villahermosa : la Phase C « begins with the start of the shakeout movement and ends after testing it » ; la Phase D « is after the completion of the shakeout test and until the confirmation event develops completely » ; la Phase E « begins after the confirmation event ». [V] — [Villahermosa, Phases](https://tradingwyckoff.com/en/phases-of-a-wyckoff-structure/)
- Nombre de tests : « The bigger the magnitude of the prior trend, the more times it may need to be Tested before it can be reversed. » [V] — [Fraser, Action – Test](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)
- Repères temporels en SSR (Fraser) : bas « in the first third to half of the total time spent in the SSR » ; « lower peaks are followed by a Spring. » [V] — [Fraser, Springing into Action](https://articles.stockcharts.com/article/articles-wyckoff-2016-05-springing-into-action)
- Compression : « Jumping out of a Hinge can result in a robust price move (up or down). » (25 fév. 2017) [V] — [Fraser, « Three Legged Stool »](https://articles.stockcharts.com/article/articles-wyckoff-2017-02-three-legged-stool)
- Phase C difficile sans spring : « the testing of supply can occur higher up in the TR without a spring or shakeout; when this occurs, the identification of Phase C can be challenging. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Exemple de Phase D distributive : « a decline below the mid-point of the TR after a UT or UTAD » renforce la preuve. [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Synchronisation par décompte de palier (stepping stone) : « as the price target projected from the stepping- stone TR approaches that of the original TR, the upward or downward trend may be ready to resume. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)

### Inferences
- **Tableau de bord « état de la plage »** proposé (synthèse) :
  - (a) événements accomplis : PS, SC, AR, ST, ST in B ou UA, spring ou LPS en Phase C, test, SOS, LPS/BU ;
  - (b) gradient de volume : pente du volume moyen des creux successifs (doit être négative), avec un rapport vol(dernier test) / vol(SC) ;
  - (c) gradient d'amplitude : écarts entre creux et sommets successifs, plus-bas montants ;
  - (d) ratio de durée Phase B / Phase A (≥ 1) ;
  - (e) cases des Nine Tests cochées, dont #9 = potentiel P&F ≥ 3 fois le risque ;
  - (f) pour le trader, le profil d'OI coin à travers les tests : OI qui se dégonfle sur les tests secs = débouclage, pas d'ouverture de shorts (extension non sourcée).
- Le module `window.py` du screener reconnaît déjà la séquence ordonnée. L'ajout naturel serait un **score de maturité** combinant (b), (c) et (d), et un drapeau « test plus sec que le spring ».

### Gaps
- Aucune source n'offre de score de maturité quantifié ni de pondération des Nine Tests ; ce sont des cases binaires à juger visuellement.
- Les pourcentages de durée et de contraction de la FAQ de Villahermosa ne sont pas étayés.
- Pas d'étude empirique liant le gradient de volume des tests à la réussite de la sortie de plage.

## Q5 — Quelles définitions quantitatives utilisent les implémentations algorithmiques, et existe-t-il des résultats empiriques (taux de réussite, espérance) pour les setups spring/test ? Calibration des seuils du screener

### Takeaway
- **Divergences entre implémentations** : elles se contredisent jusque sur le signe du volume du spring. Certaines exigent un pic (ProRealCode >1,5× la MA20, PhenLabs), d'autres un volume faible (MQL5 <1,2× la moyenne de la plage, plusieurs scripts TradingView). C'est la typologie #2/#3, que la plupart aplatissent.
- **Fourchettes typiques** : climax 2,0–3,0× la MA20, SOS 1,2–2,0×, test ou ST < MA et < 0,8× la barre précédente, réintégration dans la même barre ou sous 3 barres, pénétration de 0,3 à 6 %, clôture au-dessus de 0,6 du range.
- **Résultats empiriques** : aucune étude publiée à comité de lecture n'a été trouvée. Le seul backtest systématique repéré (PR GitHub papan-saham, [NV]) donne pour le spring seul, sur données journalières, un stop à 1 ATR et un objectif à 2R, une **espérance négative** : 41,26 % de réussite, −0,13 R en moyenne. Les taux de 60 à 70 % affichés par des scripts sont sans méthodologie.

### Cited Findings

**Implémentations open source et leurs seuils**
- ProRealCode, « Wyckoff Event Detection » [V] — [ProRealCode](https://www.prorealcode.com/prorealtime-indicators/wyckoff-event-detection/) :
  - Paramètres : `volLen = 20`, `priceLookback = 20` (ATR sur 20), `volThreshMult = 2.0`, `volumeFilter = 1.5`, `priceThreshMult = 0.3`.
  - SPRING : `low < ll[3]`, close > open, `close > low + 0.6×rng`, vol > volMA × 1.5.
  - SC : vol > volMA × 2.4, `close > low + 0.45×rng`.
  - ST-A : low à ±2 % de `ll[5]`, vol < volMA **et** vol < 0.8 × volume[1].
  - SOS : vol > volMA × 2.0 sur une série haussière de 3 barres.
  - LPS : low > low[1], vol < volMA × 1.5.
  - JAC : close > hh[3], vol > volMA × 2.0.
  - TSO : vol > volMA × 2.4, `close > low + 0.7×rng`.
  - BC : vol > volMA × 3.0.
  - UT-D : vol > volMA × 1.5, `high − close > 0.3×avgTR`.
  - BUEC : premier UT-D dans les 5 dernières barres.
  - Pas d'événement UTAD distinct.
- systematic1/wyckoff-scanner (C#, README : application générée par IA puis retouchée à la main) [V] — [GitHub systematic1/wyckoff-scanner](https://github.com/systematic1/wyckoff-scanner) :
  - Épuisement vendeur : baisse ≥ 15 % en 60 barres maximum, range lissé ≥ 1,5× la normale sur un volume ≥ 1,3× la médiane, puis repli ≤ 70 % du pic.
  - AR : sous 20 barres, rebond ≥ 6 % récupérant ≥ 20 % de la baisse, volume entre 0,5× et 1,5× la médiane.
  - Boîte : ≥ 10 barres, ≤ 12 % de haut en bas, volume ≤ 0,9× la médiane.
  - Spring : pénétration du support de 0,3 à 6 %, clôture revenue au-dessus sous 3 barres.
  - SOS : clôture > 0,5 % au-dessus de la résistance, ≥ 1,3× le volume moyen 20 jours, range au moins moyen.
  - Drapeaux de récence : spring ≤ 30 barres, SOS ≤ 10 barres.
- Article MQL5 (Tola Moses Hector, 4 juin 2026) [V] — [MQL5, « Automating Classic Market Methods in MQL5 (Part 1) »](https://www.mql5.com/en/articles/22628) :
  - Machine à états : plage, puis spring, puis SOS, puis entrée LPS.
  - Spring : low < support − 10 pips et clôture > support sur la même barre, volume tick < 1,2× la moyenne de la plage.
  - SOS : clôture > résistance, volume > 1,2×.
  - LPS : support < clôture < haut du SOS, sous 8 barres (`InpLPSBars`).
  - Invalidation : clôture sous le low du spring.
  - Gestion : stop à 1,5× ATR(14), objectif à 2R, risque de 1 %.
  - « between four and ten qualifying setups per year » sur EURUSD H4.
  - Aucun résultat chiffré publié.
- PhenLabs, « Smarter Money Concepts – Wyckoff Springs & Upthrusts » (TradingView) [V] — [TradingView PhenLabs](https://kr.tradingview.com/script/Vj3nQB8Y-Smarter-Money-Concepts-Wyckoff-Springs-Upthrusts-PhenLabs/) :
  - Support/résistance sur 20 barres ; multiplicateur de pic de volume de 1,5 (plage 1,0–3,0) sur une SMA10 ; ATR(5) pour mesurer la reprise ; seuil de probabilité sigmoïde de 0,9.
  - Une autre fiche indexée donnait un défaut de 5 (plage 2–20) [NV] : conflit à vérifier dans le code.
- TradingView « Wyckoff Method – Comprehensive Analysis » (frankieho_92) [V] — [TradingView](https://www.tradingview.com/script/Grzy0O68-Wyckoff-Method-Comprehensive-Analysis/) :
  - Volume MA 20 ; « High Volume Multiplier (default: 1.5) » ; « Climax Volume Multiplier (default: 2.0) » ; « Range Expansion Threshold (default: 1.5) » ; paliers « VERY HIGH (>2x average) », « HIGH (>1.5x average) », « LOW (<0.7x average) » ; valeurs forex 1,3 et 1,8.
  - Spring défini sur volume FAIBLE, shakeout sur volume FORT.
  - Taux affichés : « With proper filtering: 60-70% on major signals (Spring, UTAD, SOS, SOW) », sans jeu de données ni méthode.
- TradingView « Wyckoff Accumulation / Distribution Detector (v3) » : spring = « Price makes a low below recent pivot support », « Closes back above », « Does so on low volume ». Aucun seuil chiffré. [V] — [TradingView v3](https://de.tradingview.com/script/LN3t3Xax-Wyckoff-Accumulation-Distribution-Detector-v3/)
- WA (détection algorithmique) : lookback de 15 barres ; un spring ne clôture pas au plus bas ; il peut clôturer sous 50 % du range ; un écart de plus de 10 % est inacceptable. Pas de seuils de volume, pas de backtest. [V] — [WA, Identifying Wyckoff Springs with Algorithms](https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/)
- « Buying Climax + Spring [Darwinian] » (TradingView) [NV] : seuil d'écart 0,2 %, fenêtre de confirmation de 5 barres, fraction de clôture sous le haut de 0,3, lookback de 20 barres. — [TradingView Darwinian](https://in.tradingview.com/script/VC2lJJDY-Buying-Climax-Spring-Darwinian)

**Résultats empiriques**
- Backtest de la PR GitHub papan-saham #89 [NV : vu dans un résumé de recherche ; page en 404, dépôt inaccessible] — [GitHub PR](https://github.com/augustgerry/papan-saham/pull/89) :
  - Protocole : 56 tickers, 5 ans, barres journalières, entrée à la clôture de la barre suivante, stop au low de l'événement − 1 ATR, objectif à 1:2.
  - Spring seul : 41,26 % de réussite, R moyen −0,130, IC 95 % ±0,064, n = 1 098.
  - Conclusion de l'auteur : edge négatif ; le bonus de score du spring est retiré et l'événement devient informatif.
- Absence de backtest public :
  - Quantified Strategies [NV, page bloquée par vérification anti-bot] dirait n'avoir trouvé « any relevant backtest on the internet ». — [Quantified Strategies](https://www.quantifiedstrategies.com/wyckoff-trading-strategy/)
  - The Right Trader [NV] : « no reliable published win rate ». — [The Right Trader](https://therighttrader.com/learn/trading-strategies/wyckoff-trading-strategy)
- Article académique : Sharma & Raj (2024), « Wyckoff Theory in the Mind of the Market: A Psychological and Structural Reappraisal », *JISEM* 9(4). Texte extrait : article **descriptif**, sans backtest ni statistique de performance. [V] — [JISEM (PDF)](https://www.jisem-journal.com/download/60_Wyckoff%20Theory.pdf)
- Article algorithmique de WA et article MQL5 : aucun résultat chiffré publié. [V] — [WA](https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/) ; [MQL5](https://www.mql5.com/en/articles/22628)

### Inferences
- **Calibration des seuils du screener** (`config.yaml`, échelle CLV [0,1] = (C−L)/(H−L), cf. `screener/features.py`) :

| Seuil | Valeur actuelle | Ce que disent les sources | Lecture |
|---|---|---|---|
| `climax_vol` | 2.0 | ProRealCode : SC >2,4×, PS >2,0×, BC >3,0× la MA20 ; frankieho : 2,0 (forex 1,8) ; systematic1 : ≥1,3× la médiane avec range ≥1,5× ; FAQ Villahermosa : 200–400 % (non fiable) | 2,0 est le bas de la fourchette. Envisager 2,4 pour le SC si l'on veut coller à ProRealCode. |
| `sos_vol` | 1.3 | systematic1 : ≥1,3× (+0,5 % au-dessus de la résistance, range ≥ moyen) ; MQL5 : >1,2× ; ProRealCode SOS/JAC : >2,0× ; frankieho : >1,5× (forex 1,3) ; primaire : « relatively higher volume » | Consensus bas, défendable. Un SOS fort pourrait exiger aussi un spread ≥ 1,3 ATR et une clôture au-dessus de la borne. |
| `wide_spread_atr` | 1.3 | frankieho : expansion de range 1,5 ; systematic1 : 1,5× la normale (climax), range au moins moyen (SOS) | Fourchette de 1,3 à 1,5. |
| `narrow_spread_atr` | 0.7 | Aucun chiffre primaire ; FAQ Villahermosa : −50 à −70 % (non fiable) | Pas d'ancrage. Mieux vaut un critère relatif : spread du test < spread du spring. |
| `test_vol` | 0.85 | Primaire : relatif à l'événement testé (« lesser volume », « less than on the Spring day », « even lower-volume test ») ; ProRealCode ST : vol < MA et < 0,8× la barre précédente ; frankieho : LOW <0,7× ; systematic1 : plage ≤0,9× la médiane ; MQL5 LPS : <1,2× | Garder 0,85× la MA comme filtre, mais **ajouter** vol_test < vol_spring (et vol_ST < vol_SC), qui est le critère des auteurs. |
| `pen_atr` | 0.1 | systematic1 : 0,3–6 % ; MQL5 : 10 pips ; WA : >10 % d'écart inacceptable ; Fraser : #3 « shallow », #1 « complete breakdown » | 0,1 ATR est un plancher. Ajouter une classification de profondeur (et de volume) en #3/#2/#1 qui commande « entrée immédiate » ou « attendre le test ». |
| `reclaim_clv` | 0.5 | ProRealCode : spring >0,6, TSO >0,7, SC >0,45 ; WA : <0,5 toléré mais pas au plus bas ; MQL5 : clôture > support sur la même barre ; systematic1 : réintégration sous 3 barres ; ChartSchool : « reverses to close within the TR » | 0,5 se situe entre WA (permissif) et ProRealCode. L'exigence primaire est la **réintégration** de la plage ; une tolérance de N barres (≤3) est défendable. |

- Fenêtres temporelles des implémentations : BUEC ≤ 5 barres (ProRealCode), LPS ≤ 8 barres (MQL5), spring ≤ 30 barres et SOS ≤ 10 barres (systematic1). Fraser donne un test à 1–2 barres pour un #2 (exemples journaliers).
- Le backtest papan-saham (stop à 1 ATR, objectif à 2R) ressemble fortement à la configuration `backtest:` du screener (`stop_atr: 1.0`, `rr: 2.0`). S'il se confirme, il suggère qu'un **spring seul, sans test ni SOS ni contexte**, n'a pas d'edge. Cela plaide pour ne déclencher que sur le **test** et sur l'LPS, comme le recommandent Fraser et Pruden. C'est une hypothèse à vérifier avec l'optimiseur walk-forward du dépôt, pas une conclusion.
- Les taux de 60 à 70 % sans méthodologie sont à exclure de toute communication.

### Gaps
- Aucune étude publiée à comité de lecture (SSRN, Journal of Technical Analysis, IFTA) donnant des statistiques de spring ou de test n'a été trouvée.
- Le backtest papan-saham n'a pas pu être vérifié (404, dépôt non accessible).
- Le code source de PhenLabs et de frankieho n'a pas été lu : seules les descriptions l'ont été.
- Aucun backtest crypto H1/H4 ni or spécifique au spring ou à son test n'a été trouvé.

## Q6 — Comment confirmer en multi-unités de temps, et comment adapter la méthode au crypto 24/7, à l'intraday (et à l'or) ?

### Takeaway
- **Fractalité** : Wyckoff est explicitement fractal pour Fraser, avec des actions et des tests sur toutes les unités de temps. Les praticiens lisent la structure dominante d'abord, en contexte, puis descendent pour le timing. Villahermosa : contexte Wyckoff en daily ou H4, exécution en M15–H1.
- **Synchronisation** : WA demande de caler l'entrée sur un retournement de l'indice de marché, ce qui transpose naturellement vers BTC ou la capitalisation totale pour les altcoins.
- **Crypto (source WA)** : seul le support de 2020 de Rutigliano aborde le sujet. Il alerte sur les actifs illiquides (« quick runs immediately erased after », « irregular spreads ») et utilise un P&F à **échelle en pourcentage (10 %)** pour Bitcoin.
- **Non couvert par les sources** : rien de primaire sur le 24/7 (absence de séances, volume de week-end, fragmentation entre exchanges, spot contre perpétuels). Ces points relèvent de l'inférence.

### Cited Findings
- Fractalité et intraday (Fraser) :
  - « Wyckoff has a fractal quality, and thus, the Method essentially works in all timeframes. » ; « The trained eye can see the price structures unfolding whether it be on a weekly vertical chart or the shortest term intra-day chart. » [V] — [Fraser, Enjoying the Short Term View](https://articles.stockcharts.com/article/articles-wyckoff-2017-01-enjoying-the-short-term-view)
  - Cas d'étude : graphique 60 min pour la plage, P&F 30 min pour les objectifs ; pour voir la « minutia of the Distribution », il faut « zoom into the smaller timeframes where the elements of the structure can be seen ». [V] — même source.
  - « Traders in all timeframes will seek proof of the exhaustion of the prevailing trend, in the form of Tests » [V] — [Fraser, Action – Test](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)
- Hiérarchie des unités de temps (Villahermosa) [V] — [Villahermosa, guide](https://tradingwyckoff.com/en/wyckoff-method/) :
  - « Macro framework (Wyckoff): on a daily or H4 chart, you identify whether we are in accumulation, distribution or trend. » ; « you drop to M15-H1 and look for Order Blocks or CRT setups ».
  - Tableau des unités de temps idéales : Wyckoff « H4 - Daily - Weekly ».
  - « Always read the structure of the dominant one first and use it as context. »
- Synchronisation avec le marché : « Three-quarters or more of individual issues move in harmony with the general market, so you improve the odds of a successful trade by having the power of the overall market behind it. » ; Buying Test #7 : « Stock stronger than the market ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Champ d'application : « Wyckoff's methods can be applied to any freely-traded market in which large institutional traders operate, including commodities, bonds and currencies. » [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)
- Crypto, support WA de Rutigliano (juillet 2020) [V] — [slides WA 2020](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf) :
  - Diapositive « ILLIQUID CRYPTO ASSET » : « QUICK RUNS IMMEDIATELY ERASED AFTER », « IRREGULAR SPREADS ».
  - Schéma de réaccumulation BTC : « FAILED SPRING », « UA », « MSOS », « BU ».
  - « BITCOIN 2013- 2018 PERCENTAGE SCALING (10%) » avec « AGGRESSIVE COUNT » (« $19277 »), et renvoi aux « Wyckoff Point-And-Figure Charting » Specials de Fraser et Bogomazov sur l'échelle en pourcentage.
- Cours crypto WA (Rutigliano et Bogomazov, non daté) : « how to apply the Wyckoff Method to the universe of cryptocurrencies » ; « Common mistakes in high volatility environments » ; « A special section will be devoted to advanced tactics to protect crypto portfolios in conditions of high volatility. » La page ne traite ni du 24/7 ni de la source de volume. [V] — [WA, « Crypto strategies from swing trading to intraday »](https://www.wyckoffanalytics.com/demand/crypto-strategies-from-swing-trading-to-intraday)
- P&F à échelle ATR : « Compare it to the 5-box reversal PnF chart using ATR (20) scaling. » [V] — [Fraser, Three Legged Stool](https://articles.stockcharts.com/article/articles-wyckoff-2017-02-three-legged-stool)
- Taille de case P&F pour les actions (non transposable telle quelle) : « for low-priced stocks, the box size could be 0.5 to 1 point, whereas for high-priced (> $200) stocks, a box size of 5 points would be more appropriate ». Pour les plages de palier, on préfère « a smaller box size ». [V] — [WA PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2021/05/Wyckoff-Method-Wyckoff-Analytics-English.pdf)

### Inferences
- **Pile multi-unités de temps pour BTC** (à confirmer) :
  - D1/H4 = contexte et biais top-down ; une plage dans un downtrend est une redistribution par défaut (CLAUDE.md).
  - H1 = structure locale complète, étiquetée relativement à sa propre plage.
  - Unité de temps inférieure (15m/5m) = seulement le timing d'un test ou d'un LPS.
  - Une confluence existe quand l'LPS H1 coïncide avec un test de Phase B ou C sur H4.
- **Adaptations 24/7 crypto** (inférences, aucune source primaire) :
  - (a) Normaliser le volume par heure de la journée ou jour de la semaine, car un vol MA20 glissant en H1 traverse des creux de week-end et de séance asiatique qui peuvent fabriquer de faux « tests secs » ou de faux « climax ».
  - (b) Préférer un volume agrégé (multi-exchanges, voire spot + perp) au volume d'une seule venue.
  - (c) Mesurer pénétration et marges de stop en ATR ou en %, pas en points.
  - (d) Utiliser un P&F en % (≈ 0,5–1 % en H1 ?) ou en ATR, à calibrer.
  - (e) Lire l'OI en coin comme un « second volume » : un test sec + OI coin en baisse = débouclage, cohérent avec un test réussi ; un test + OI coin en hausse = ouverture de positions, à attribuer par le ratio L/S, le funding et les liquidations (convention du trader, non issue de la littérature Wyckoff).
- **Or** : les sources confirment l'applicabilité aux matières premières (WA), mais n'abordent pas la qualité du volume. Côté pratique, le volume tick des CFD XAUUSD n'est qu'un proxy ; le volume des futures COMEX (GC) est préférable pour lire l'effort (inférence).

### Gaps
- Aucune source primaire (WA, Fraser, Villahermosa, Weis) traitant explicitement du 24/7 : séances, week-ends, fragmentation du volume, spot contre perp.
- Le contenu des sessions du cours crypto WA n'est pas accessible. Seule la page descriptive et le support de 2020 l'étaient, et une large part de ce support est faite d'images non textuelles.
- Rien de trouvé sur l'adaptation de la méthode à l'or (choix du flux de volume) chez les auteurs primaires.
- Pas d'étude sur la meilleure combinaison d'unités de temps (contexte, structure, déclencheur) mesurée empiriquement.
