# Microstructure and execution theory behind Wyckoff "tests" and the Composite Operator (CO), mapped onto crypto perps

Tag legend used in the Inferences sections: **[ÉTABLI]** = directly supported by the cited literature · **[ANALOGIE]** = a Wyckoff reading built on that literature, plausible but not tested as such · **[NON VÉRIFIÉ]** = a claim I could not confirm against a primary source. Short verbatim quotes are kept under ~125 characters. Every number below comes from the cited page, unless it is explicitly labelled as an illustrative calculation.

---

## Q1. What do Kyle (1985) and the metaorder / square-root impact literature imply about how a large buyer must build a position (time, price range, passive vs aggressive), and why is marking up before supply is exhausted costly?

### Takeaway
A large informed buyer cannot take size quickly. Price impact grows like √(size/daily volume): buying **1 % of daily volume moves price by about 0.1 daily σ**. Impact does not fully disappear, and aggressive buying reveals information to market makers and to order anticipators. The cheapest strategy is therefore to trade gradually and mostly passively, hidden in other traders' volume, and to concentrate fills when liquidity is abundant, i.e. when others are selling heavily. Only after that does the buyer turn aggressive. Marking up early raises the cost of every remaining unit and leaks the information. If latent supply is still there when buying pauses, price relaxes back.

### Cited Findings

**Kyle (1985), *Continuous Auctions and Insider Trading*, Econometrica 53(6):1315–1335**
- Bibliographic record: Kyle, A.S., Econometrica vol. 53 no. 6, pp. 1315–1335, Nov. 1985. The full text sits behind JSTOR. — [IDEAS/RePEc](https://ideas.repec.org/a/ecm/emetrp/v53y1985i6p1315-35.html)
- Setup: one risk-neutral insider who knows V ~ N(μ, σ_V²), noise traders u ~ N(0, σ_u²), and a competitive risk-neutral market maker. The market maker sees only total order flow q = x + u and sets p = E[V|q]. — [Kyle 1985 lecture notes, R. Liu (2025)](https://ronming1303.github.io/documents/Kyle_1985_.pdf)
- One-shot equilibrium: x = β(V − μ) and p = μ + λq, with **β = σ_u/σ_V** and **λ = σ_V/(2σ_u)**. The notes state "1/λ is a measure of market depth". The insider's ex-ante expected profit is **σ_V·σ_u/2**. The market maker's posterior variance is **σ_V²/2**, "Exactly half the previous variance: Insider reveals half his information". — [Kyle notes](https://ronming1303.github.io/documents/Kyle_1985_.pdf)
- Comparative statics: more noise trading (σ_u↑) makes the insider **more** aggressive, and more asymmetric information (σ_V↑) makes him **less** aggressive. The noise "can hide speculator's information and increases the expected payoff". — [Kyle notes](https://ronming1303.github.io/documents/Kyle_1985_.pdf)
- Continuous-trading limit, quoted from the abstract: "noise trading provides camouflage which conceals his trading from market makers"; "prices follow Brownian motion, the depth of the market is constant over time,"; "and all private information is incorporated into prices by the end of trading." — [Econometric Society, Kyle 1985 abstract](https://www.econometricsociety.org/publications/econometrica/1985/11/01/continuous-auctions-and-insider-trading)
- Kyle's impact is **linear** (Δ ∝ Q). Tóth et al. note that a square-root singularity is "certainly not accounted for in Kyle's classical model of impact [11], which predicts a linear impact ∆ ∝ Q". — [Tóth et al. 2011, PDF](https://arxiv.org/pdf/1105.1694)

**Square-root law for metaorders: Tóth, Lempérière, Deremble, de Lataillade, Kockelkoren, Bouchaud (2011), Phys. Rev. X 1, 021006**
- Published as "Anomalous price impact and the critical nature of liquidity in financial markets", Physical Review X 1, 021006 (2011). — [arXiv 1105.1694](https://arxiv.org/abs/1105.1694)
- Law: **Δ(Q) = Y·σ·√(Q/V)**. Here σ is the daily volatility and V the daily traded volume, both measured on the day of the trade, and "The numerical constant Y is of order unity". More generally Δ ∝ Q^δ "with δ in the range 0.4 to 0.7". — [Tóth et al. PDF](https://arxiv.org/pdf/1105.1694)
- Evidence quoted in the paper:
  - Almgren et al.: 700,000 US stock orders executed by Citigroup, giving **δ ≈ 0.6**.
  - Moro et al.: **δ ≈ 0.5** on Madrid and **≈ 0.7** on London.
  - CFM's own data: "nearly 500,000 trades" (metaorders) on futures, June 2007 to Dec 2010, giving **δ ≈ 0.5 for small-tick and ≈ 0.6 for large-tick contracts**, "for Q/V ranging from a few 10^−4 to a few %".
  - [Tóth et al. PDF](https://arxiv.org/pdf/1105.1694)
- Order of magnitude: "trading one hundredth of the daily volume moves the price by a tenth of its daily volatility, which is indeed a huge amplification". Marginal impact "diverges for small volumes as Q^−1/2". — [Tóth et al. PDF](https://arxiv.org/pdf/1105.1694)
- Why size must be spread out (the "liquidity funnel"): "large metaorders have to be fragmented in order to be digested by the liquidity funnel, leading to long-memory in the sign of the order flow". — [Tóth et al. PDF](https://arxiv.org/pdf/1105.1694)
- Latent liquidity, which is why the CO cannot be seen in the book: "since there is little incentive to reveal one's intentions too early, most of the volume is latent and not revealed". The average latent supply/demand profile is "V-shaped and vanishes around the current price". — [Tóth et al. PDF](https://arxiv.org/pdf/1105.1694); [arXiv abstract](https://arxiv.org/abs/1105.1694)
- Fragility: "we believe that markets operate in a critical regime where liquidity vanishes". The authors link this to "micro-crisis". — [Tóth et al. PDF](https://arxiv.org/pdf/1105.1694)
- Bouchaud (2024): "average price impact only depends on the total volume traded Q, and barely on execution schedule", provided the participation rate is not too high. The exponent "remains stubbornly anchored around delta=1/2". Latent liquidity means volumes "intended to be exchanged but not necessarily visible in the order book". He also gives a Glosten-Milgrom style derivation: "Market makers try to detect these informed traders". — [Bouchaud, "The Square-Root Law of Market Impact" (Substack, Nov 2024)](https://bouchaud.substack.com/p/the-square-root-law-of-market-impact)
- The textbook treatment is the "Impact of metaorders" chapter of Bouchaud, Bonart, Donier & Gould, *Trades, Quotes and Prices* (Cambridge UP, 2018). — [Cambridge Core chapter page](https://cambridge.org/core/books/trades-quotes-and-prices/impact-of-metaorders/7320C5E965EE6CE7B755E36FAA542899)
- Bitcoin: Donier & Bonart reconstruct **more than one million metaorders** on a Bitcoin/USD exchange and "empirically confirm the 'square-root law'" for impact, "which holds on four decades". — [arXiv 1412.4503](https://arxiv.org/abs/1412.4503)

**Impact decay and permanent impact**
- Farmer, Gerig, Lillo & Waelbroeck derive a "fair pricing" condition: "the average transaction price of the metaorder is equal to the price after trading is completed". They predict that impact grows "roughly as the square root of metaorder size", with "average permanent impact relaxing to about two thirds of peak impact". — [arXiv 1102.5457](https://arxiv.org/abs/1102.5457)
- Said et al. (2018) study **limit-order** metaorders, which is the passive case. Temporary impact follows a power law, and "the long-term impact is shown to stabilize at a level of approximately two-thirds of the maximum impact". The same summary attributes publication of Farmer et al. to *Quantitative Finance* 13:1743–1758. — [Said et al., arXiv 1802.08502 (search summary)](https://arxiv.org/abs/1802.08502)

**Optimal execution: Almgren & Chriss (2000/2001), Journal of Risk 3(2):5–39**
- Model:
  - Unaffected price: arithmetic Brownian motion.
  - **Permanent impact g(v) = γv** and **temporary impact h(v) = ηv**, where v is the trading rate.
  - The trader minimises **E[C] + λ·Var[C]**.
  - [Wikipedia, Almgren–Chriss model](https://en.wikipedia.org/wiki/Almgren%E2%80%93Chriss_model)
- Optimal holdings: **x_k = X·sinh(κ(T − t_k))/sinh(κT)**, with κ̃² = λσ²/(η − ½γτ). — [Wikipedia](https://en.wikipedia.org/wiki/Almgren%E2%80%93Chriss_model)
- Limiting cases: a risk-neutral trader (λ = 0) trades linearly (TWAP); as λ → ∞ the trader liquidates immediately; "the more risk-averse the trader, the more front-loaded the execution schedule". — [Wikipedia](https://en.wikipedia.org/wiki/Almgren%E2%80%93Chriss_model)
- A secondary source describes κ as the "urgency" parameter and gives a half-life of ln2/κ. — [search summary citing MetricGate / RL extension, arXiv 1403.2229](https://arxiv.org/pdf/1403.2229)

**Passive vs aggressive, and timing (liquidity provision vs liquidity taking)**
- Kaniel & Liu (2006), J. Business 79(4):1867–1914:
  - Informed traders may prefer **limit** orders, sometimes so much that "in equilibrium limit orders convey more information than market orders".
  - The **horizon** of the private information is "positively related to the probability of using limit orders". With a short horizon they switch to market orders.
  - [IDEAS record + abstract (search summary)](https://ideas.repec.org/a/ucp/jnlbus/v79y2006i4p1867-1914.html)
- Collin-Dufresne & Fos (2015), J. Finance 70(4):1555–1582, use Schedule 13D activists, who are genuinely informed:
  - On their trading days, "both high-frequency and low-frequency measures of stock liquidity indicate a higher stock liquidity", and Kyle's lambda, PIN and Amihud measures show *lower* adverse selection.
  - "The evidence is consistent with informed traders being more aggressive when measured stock liquidity is high."
  - [NBER w18452](https://www.nber.org/papers/w18452)
  - The second channel is that these filers hold long-lived information and therefore also use **limit orders**. — [Harvard Law School Forum summary by the authors](https://corpgov.law.harvard.edu/2015/08/05/prices-and-informed-trading/)
- Cont, Kukanov & Stoikov (2014), J. Fin. Econometrics 12(1):47–88, using 50 US stocks: "a linear relation between order flow imbalance and price changes, with a slope inversely proportional to the market depth". The trade-volume relation is noisier than the order-flow-imbalance (OFI) relation. — [arXiv 1011.6402](https://arxiv.org/abs/1011.6402)

**Hidden / iceberg orders and absorption**
- Bessembinder, Panayides & Venkataraman (2009), JFE 94(3):361–383, on Euronext-Paris:
  - Hidden orders make up **44 % of order volume**.
  - "aggressively priced orders tend to be exposed… while larger and less aggressively priced orders tend to be hidden".
  - [SSRN abstract](https://papers.ssrn.com/ab_id=956476)
- Frey & Sandås, using Xetra data:
  - Hidden liquidity is associated with "greater liquidity in the order books, greater trading volume, and smaller price impact".
  - When participants detect icebergs, they "tend to strongly respond by submitting matching market orders".
  - The larger the executed fraction of an iceberg, the smaller its price impact, which is "consistent with liquidity rather than informed trading".
  - [CFS WP 2008/48 (search summary)](https://gfk-cfs.de/media//08_48.pdf)

**Information leakage and order anticipation**
- van Kervel & Menkveld (2019), J. Finance 74(3):1091–1137: HFTs first **lean against** large institutional orders and then **trade in the same direction** for the most informed ones. The authors read this as investors trading off speculative profit against the "risk of being detected and preyed on by HFTs". — [EconPapers record + abstract (search summary)](https://econpapers.repec.org/RePEc:bla:jfinan:v:74:y:2019:i:3:p:1091-1137)

### Inferences
- **[ÉTABLI] Size takes time.** With Δ ≈ Yσ√(Q/V) and Y ≈ 1, the cost of urgency is large. *Illustrative calculation, not a source:* take a BTC daily σ of 3 % (assumed) and Y = 1.
  - Buying 1 % of a day's volume gives about +0.30 %.
  - 10 % of a day's volume gives about +0.95 %.
  - 50 % gives about +2.1 %, but that is well beyond the Q/V range Tóth tested ("a few %").
  - Under fair pricing, the average fill sits about 2/3 of the way to the peak, so the average price paid is about (2/3)·Yσ√(Q/V). The total cost of a metaorder is therefore about (2/3)·Yσ·Q^{3/2}/V^{1/2}: doubling the size multiplies the total dollar cost by about 2.8.
- **[ÉTABLI → ANALOGIE] Why accumulation looks like a range.** Price responds to *net* order-flow imbalance relative to depth (Cont-Kukanov-Stoikov), not to *gross* volume. If a large patient buyer sits on passive bids that absorb sellers' market orders, gross volume is high, net imbalance is near zero and price goes sideways. That is Wyckoff's "effort without result" at the bottom of the range. Inventory moves from weak hands to strong hands without a trend. The reading of the *buyer's identity* is the analogy; the price-formation mechanism is established.
- **[ÉTABLI] When to fill.** Kyle's insider hides in noise volume. Real informed traders (13D filers) trade more when liquidity is high and use limit orders (Collin-Dufresne & Fos). The cheapest moments to get size are when someone else urgently needs to trade the other way. **[ANALOGIE]** In Wyckoff terms, the selling climax (SC) and springs, where forced or panicked supply peaks, are where the CO buys. Kyle-λ type measures do not even flag the presence of informed trading on those days.
- **Why marking up before supply is exhausted is costly:**
  1. Impact is concave and partly permanent. Every unit bought after the price has been pushed up is paid at a higher price, so you pay against your own impact.
  2. In Kyle's world, aggressive flow makes the market maker revise value, so the remaining purchases are made at prices that already reflect the buyer's information. The information premium is "spent".
  3. Order anticipators detect and back-run the most informed flow (van Kervel & Menkveld), which raises costs further.
  4. **[ANALOGIE]** If latent sell liquidity (supply) is still there, the price relaxes back once the buyer pauses: about 1/3 of the peak impact decays on average, and more if real supply returns. The CO then holds inventory bought high. Hence the logic of the **test**: before markup, verify that supply near the lows has been consumed.
- **[ANALOGIE] What the test measures, in microstructure terms.** A low-volume pullback that holds above the spring/SC low means small sell-side order flow produced little downward price change. In the Cont-Kukanov-Stoikov setting, either selling pressure is small (OFI small) or bid depth is large relative to it. Both are the conditions for a cheap markup. A pullback that falls quickly on low volume means thin bids, i.e. demand is absent. No paper tests "Wyckoff tests" per se; this is a translation of the OFI/depth relation.
- **[ANALOGIE] The SOS as the switch from passive to aggressive.** Kaniel & Liu show that informed traders switch to market orders when the information horizon shortens. The jump across the creek or SOS can be read as the moment the large buyer starts crossing the spread: wide spread, high volume, positive taker imbalance.
- **[ANALOGIE] Range length.** Almgren-Chriss implies that a patient buyer (low λ, long-lived information) trades close to linearly, which produces long ranges. An urgent buyer front-loads, which produces short, volatile accumulations. Range duration should scale with position size relative to V and with the buyer's patience.
- **[ÉTABLI] Passive is not invisible.** Limit-order metaorders also leave lasting impact (about 2/3 of peak, Said et al.) and icebergs get detected (Frey & Sandås). Absorption leaves traces: volume clusters at the range lows, and strongly negative taker flow (CVD) while price holds (see Q5).

### Gaps
- I did not verify Kyle's continuous-time closed form against the original text (commonly stated as λ = Σ₀^{1/2}/σ_u, constant). Only the "depth constant over time" statement comes from the abstract. Kyle's λ has **no universal value**: it is market- and period-specific.
- No current estimate of Y or δ for **BTC perpetuals** was found. The Donier & Bonart abstract page does not name the venue, the period or the fitted exponent. It is widely believed to be MtGox-era data, but I could not verify that.
- I did not verify whether the original Almgren-Chriss temporary-impact function includes a fixed-cost term (ε·sgn); Wikipedia gives only ηv.
- No empirical study links metaorder impact decay directly to Wyckoff "tests". That mapping remains an analogy.

---

## Q2. What does Osler's work show about where stop-loss and take-profit orders cluster, and how stop cascades accelerate moves through support/resistance? How does that ground the spring/UTAD and the test after it?

### Takeaway
Using a real dealer order book, Osler shows two things. Take-profit (and limit) orders bunch **at** round numbers and act as "partially reflecting barriers". Stop-loss orders bunch **just beyond** them: buy-stops just above, sell-stops just below. Crossing those levels therefore triggers positive-feedback "price cascades" that are faster, larger and longer-lived than moves after take-profits. Dealers know where these orders sit, and "running the stops" is market lore. Regulators have sanctioned dealers for deliberately triggering client stops. This is the mechanical basis of the spring and the upthrust. The edge Osler documents is statistically significant but modest, about 4–5 percentage points.

### Cited Findings
- **Osler (2000), "Support for Resistance", FRBNY Economic Policy Review 6(2):53–68:**
  - Data: support/resistance levels published daily by six firms, Jan 1996 to Mar 1998, for USD/DEM, USD/JPY and GBP/USD, with one-minute quotes; tested against **10,000 sets of arbitrary levels** by bootstrap.
  - "Exchange rates bounced off arbitrary support and resistance levels 56.2 percent of the time on average… they bounced off the published levels 60.8 percent of the time."
  - The published levels beat the arbitrary ones in all 16 firm-currency pairs, and the result is significant at 5 % for all but three.
  - Predictive power lasted "at least five business days".
  - More than 70 % of published levels end in 0, and 96 % end in 0 or 5.
  - [FRBNY EPR PDF](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf)
- **Osler (2003), "Currency Orders and Exchange Rate Dynamics: An Explanation for the Predictive Success of Technical Analysis", J. Finance 58(5):1791–1819:**
  - Abstract of the working paper, FRBNY SR 125: "Take-profit orders tend to reflect price trends, and stop-loss orders tend to intensify trends." and "The requested execution rates of these orders are strongly clustered at round numbers".
  - "stop-loss buy orders tend to be clustered just above round numbers (for example… 1.6605, rather than 1.6600 or 1.6595), and stop-loss sell orders tend to be clustered just below".
  - Take-profit orders are more strongly clustered at round numbers, so "round numbers should act as partially reflecting barriers".
  - Data: **9,667 conditional orders** at a large dealing bank, 1 Sep 1999 to 11 Apr 2000. The single biggest cluster is at levels ending in 00, with about **8.7 %** of orders.
  - [FRBNY SR 125 PDF](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf); [JF record](https://econpapers.repec.org/RePEc:bla:jfinan:v:58:y:2003:i:5:p:1791-1819)
- **The dealer as informed liquidity provider (same paper):**
  - Conditional orders are about 5–10 % of the bank's deal flow.
  - Dealers seek them because they "provide private information about likely exchange-rate movements".
  - With a large take-profit sell at 1.6010, a dealer can "with relative safety open a short position at 1.6000".
  - The conditional order book is "pre-trade order flow information that is available only to the dealer".
  - [SR 125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf)
- **Osler (2005), "Stop-loss orders and price cascades in currency markets", J. Int. Money & Finance 24(2):219–241 (FRBNY SR 150, 2002):**
  - Three results: (1) "Exchange rate trends are unusually rapid when rates reach exchange rate levels at which stop-loss orders have been documented to cluster"; (2) the response to stop-losses is larger than to take-profits; (3) it lasts longer.
  - "Most results are statistically significant for hours, although not for days."
  - Stop-loss orders "are sometimes triggered in waves", which may explain the "fat tails" of returns.
  - [FRBNY SR 150 PDF](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf); [EconPapers](https://econpapers.repec.org/RePEc:fip:fednsr:150)
- **Magnitudes (SR 150):**
  - USD/DEM moves 0.061 % in the 15 minutes after crossing a round number, against 0.054 % after crossing an arbitrary number. The difference holds in 51 of 58 ten-day intervals.
  - The reversal frequency is 59.3 % at round numbers against 54.8 % at arbitrary numbers.
  - 14.3 % of executed stop-loss buys request rates ending in [01,10], against 6.9 % in [90,99].
  - Data: the Royal Bank of Scotland order book, 1 Aug 1999 to 11 Apr 2000, 9,655 orders worth more than $55 bn. Stop-losses are 43 % of orders by volume.
  - [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)
- **Stop hunting described in SR 150:**
  - "Market lore suggests that participants sometimes intentionally trigger a series of stop-loss orders, and the activity has its own name: 'running the stops.'"
  - Deutsche Bank on 7 Mar 2002, USD/JPY: "Japanese accounts aggressively sold USD/JPY, which in turn triggered successive waves of stop-loss orders… Once below ¥129.80, USD/JPY fell within seconds to ¥129.40".
  - Stop runs are described as extremely rapid and "gappy".
  - [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)
- **Sanctioned stop triggering:** in Nov 2014 the FCA fined Citi, HSBC, JPMorgan, RBS and UBS a total of **£1,114,918,000** because, between 1 Jan 2008 and 15 Oct 2013, G10 spot FX traders "attempted to manipulate fix rates and trigger client 'stop loss' orders" and "shared information about clients' activities which they had been trusted to keep confidential". — [FCA press release](https://www.fca.org.uk/news/press-releases/fca-fines-five-banks-%C2%A311-billion-fx-failings-and-announces-industry-wide)
- **Round-number clustering exists in Bitcoin:** over 10 % of BTC prices end in 00. Price and volume are positively related to clustering, but there is no significant return pattern after round numbers. — [Urquhart (2017), Economics Letters 159:145–148, IDEAS](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html)
- **Predatory trading theory:**
  - Trading "that induces and/or exploits the need of other investors to reduce their positions" is predatory. Predators withdraw liquidity instead of supplying it, which causes **price overshooting**.
  - Predation can even trigger the victim's forced liquidation. The Brady Report linked the 1987 crash partly to this behaviour.
  - [Brunnermeier & Pedersen (2005), J. Finance 60(4):1825–1863, author page](https://www.princeton.edu/~markus/research/papers/predatory_trading.htm); [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:60:y:2005:i:4:p:1825-1863)

### Inferences
- **[ÉTABLI] Obvious range edges carry two opposite order layers:**
  - Resting take-profit and limit orders **at** the level reflect price, so ranges and "tests" bounce.
  - Stops **just beyond** the level accelerate price once it is crossed, which gives the breakout or flush.
  - [ANALOGIE] A range is literally bounded by an order cluster on each side.
- **[ANALOGIE] Spring, step by step:**
  1. Price pierces support (the SC low or the range low).
  2. The sell-stops just below fire in waves as market sell orders. That is a burst of urgent supply.
  3. A large patient buyer absorbs it with resting bids. It gets size without lifting price, because the stops are the counterparty liquidity it needs (see Q1).
  4. The close comes back inside the range: high volume, long lower wick, high CLV.
  5. The stop fuel below support has been **consumed**, so that supply is gone.
- **UTAD/upthrust (mirror):** buy-stops above resistance (short covering, breakout buyers, and in crypto short liquidations) are the liquidity into which a distributor sells.
- **[ANALOGIE] The test after the spring** re-approaches the same zone on **low volume and a narrow spread**. Because the stops there were already executed, no cascade fires, and if price holds, supply is exhausted. If the retest instead *re-ignites* a cascade (volume and spread expand downward, closes are weak), the stop pool or real supply was not exhausted and the "spring" was a breakdown. Osler's "waves" result explains why one flush does not always clear a level.
- **[ÉTABLI] Keep magnitudes honest.** Bounce edges are about 4.6 pp (60.8 % vs 56.2 %) and 4.5 pp (59.3 % vs 54.8 %). Post-crossing acceleration is about 0.061 % vs 0.054 % over 15 minutes, and the effects are significant for hours, not days. These are statistical tilts on intraday FX, not deterministic rules.
- **[ANALOGIE] Stop hunting needs no conspiracy.** Anyone with inventory to execute (the CO) or a predatory motive (Brunnermeier-Pedersen) benefits from the liquidity a stop cascade releases. Dealers who see conditional order books have an informational advantage (Osler). Misusing client stop information is documented misconduct (FCA 2014).
- **[ANALOGIE] Crypto transfer.** BTC prices cluster at round numbers (Urquhart), which is the precondition for Osler-type stop clustering just beyond them. In perps, liquidation prices behave like stops without discretion, so the cascade mechanism is stronger (see Q5).

### Gaps
- No crypto replication of Osler's order-level clustering was found. Stop orders on centralised exchanges are not public, and commercial "liquidation heatmaps" are model estimates I did not assess.
- Osler's evidence comes from one bank's book in 1999–2000 FX and from FX intraday data. Extending it to BTC perps on H1/H4 is an assumption.
- The two Osler versions describe the dataset differently (9,667 orders from 1 Sep 1999 in SR 125, against 9,655 orders from 1 Aug 1999 at RBS in SR 150). This is a minor discrepancy.

---

## Q3. What do market-maker inventory models say about a dealer's behaviour when inventory is long or short, and how could that appear as "tests" on a chart?

### Takeaway
Inventory models (Ho & Stoll 1981; Avellaneda & Stoikov 2008) show that a dealer who is long lowers his reservation price below mid and skews quotes to sell, and a dealer who is short does the opposite. Empirically, intermediary inventory creates **transitory price pressure** that mean-reverts within about a day on the NYSE. High-volume moves driven by liquidity demand tend to reverse. On a chart, part of the automatic rally (AR) after a climax and part of the secondary test (ST) can therefore be explained mechanically by liquidity providers absorbing a climax and then unloading inventory. This is an alternative, or a complement, to "the CO testing supply".

### Cited Findings
- **Avellaneda & Stoikov (2008), Quantitative Finance 8(3):217–224:**
  - Reservation (indifference) price **r(s,q,t) = s − q·γ·σ²·(T − t)**, where q is the inventory and γ the risk aversion (eq. 8/29).
  - Total optimal spread around r: **δ^a + δ^b = γσ²(T − t) + (2/γ)·ln(1 + γ/k)** (eq. 30).
  - "If the agent is long stock (q>0), the reservation price is below the mid-price, indicating a desire to liquidate the inventory by selling stock." When short, "the reservation price is above the mid-price".
  - The spread is independent of inventory, a property that "follows from our assumption of exponential arrival rates".
  - [Avellaneda & Stoikov PDF](https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- **Ho & Stoll (1981), JFE 9(1):47–73,** as described by Avellaneda & Stoikov: it "analyses the optimal prices for a monopolistic dealer in a single stock… derive[s] optimal bid and ask quotes around this price, to account for the effect of the inventory". The inventory effect "was found to be significant in an empirical study of AMEX Options by Ho and Macris (1984)". — [A&S PDF](https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf); [EconPapers record](https://econpapers.repec.org/RePEc:eee:jfinec:v:9:y:1981:i:1:p:47-73)
- **Hendershott & Menkveld, "Price Pressures", JFE 114(3):405–423 (2014),** using 12 years of daily NYSE intermediary positions:
  - "A $100,000 inventory shock causes an average price pressure of 0.28% with a half-life of 0.92 days."
  - Price pressure causes "average transitory volatility in daily stock returns of 0.49%".
  - The effects are larger and last longer in small stocks.
  - The social cost is about 10 % of the cost of immediacy.
  - The figures come from the 2010 working paper; published values may differ.
  - [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:114:y:2014:i:3:p:405-423); [CFS WP 2010/14](https://gfk-cfs.de/media//10_14.pdf)
- **Campbell, Grossman & Wang (1993), QJE 108(4):905–939:**
  - Return autocorrelation declines with volume.
  - Risk-averse "market makers" absorb non-informational selling or buying pressure, and the resulting price moves later **reverse**.
  - "a stock price decline on a high-volume day is more likely than a stock price decline on a low-volume day to be associated with an increase in the expected stock return".
  - [Harvard DASH PDF](https://dash.harvard.edu/bitstream/1/3128710/2/campbell_trading.pdf); [SSRN](https://papers.ssrn.com/abstract=297335)
- **Dealers trade on their own order-book information:** a dealer holding a large take-profit sell at 1.6010 can open a short at 1.6000 knowing his loss is capped. — [Osler SR 125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf)

### Inferences
- **[ÉTABLI] The rule:** long inventory → quotes skewed down → the dealer sells into rallies or lets price sag. Short inventory → quotes skewed up → the dealer buys dips or lets price drift up. The skew grows with inventory, risk aversion, volatility and the remaining horizon (q·γ·σ²·(T−t)).
- **[ANALOGIE] SC → AR → ST as an inventory cycle:**
  1. In the selling climax, liquidity providers (dealers, market makers and patient large buyers) absorb forced selling and end up **long**.
  2. Price was pushed below "fair" by the liquidity demand. Campbell-Grossman-Wang predict that high-volume declines are followed by higher expected returns, so the snap-back is the AR.
  3. The liquidity providers then work off the inventory. Their skewed quotes cap the rally and let price drift back toward the climax zone: that is the ST, typically on lower volume.
  4. If real demand absorbs that inventory at the ST (low volume, holds above the SC low), the inventory overhang is gone. That is bullish evidence equivalent to "supply exhausted".
  - Mirror: after a buying climax (BC), dealers are **short**, which gives the AR down and the ST up toward the BC on low volume.
- **[ANALOGIE] Two explanations for the same test, both possibly true.** (a) The CO probes supply. (b) Intermediaries mean-revert inventory. Reading volume first separates them partly. A climax-like expansion followed by a quieter retest is consistent with both. A retest that *expands* volume to the downside is consistent with neither: that is new supply.
- **[NON VÉRIFIÉ / spéculatif] Speed in crypto.** In crypto perps, market makers hedge across spot and perps and are mostly algorithmic, so their inventory half-lives are plausibly far shorter than the NYSE specialists' ~1 day. Pure inventory-driven retests would then show mostly on M5–H1. On H4, a test is more likely driven by participants' flows (stops, liquidations, accumulation) than by dealer inventory alone.

### Gaps
- I did not retrieve the Ho & Stoll (1981) abstract; their results are described here only through Avellaneda & Stoikov and bibliographic records.
- I found no published estimate of crypto market-maker inventory half-lives or of price pressure in BTC perps.
- Grossman-Miller (1988), the classic liquidity-provision reversal model, was not checked.

---

## Q4. Which concepts in Harris's trader typology map onto the CO, onto "weak hands", and onto stop-hunting behaviour? And what is the modern "CO", honestly, given pre-1934 pools and today's law?

### Takeaway
In Harris's framework, the CO is best read as **informed (value) traders who must execute large orders**, helped or shadowed by **dealers** who supply liquidity. "Weak hands" are **utilitarian** traders forced to trade (liquidity needs, margin calls) and **futile** traders whose orders are predictable, such as chartists' stops at obvious levels. Stop hunting belongs to **parasitic** traders: order anticipators (front-runners, squeezers) and bluffers or manipulators. Historically, the 1920s pools that inspired the CO idea look in the data **more like informed trading than successful manipulation**. Their manipulative tactics (wash sales, matched orders, churning to "paint the tape", and today spoofing and layering) are illegal under US §9 (1934), CEA §4c(a)(5)(C) (Dodd-Frank) and EU MAR/MiCA. The modern "CO" is aggregate large-player and algorithmic behaviour, not a single puppet master.

### Cited Findings

**Harris, *Trading and Exchanges: Market Microstructure for Practitioners* (Oxford UP, 2003)**
- Part III, "Speculators", contains ch. 10 "Informed Traders and Market Efficiency", ch. 11 "Order Anticipators" and ch. 12 "Bluffing and Price Manipulation". — [search summary of the table of contents; publisher page](https://academic.oup.com/book/52292)
- Taxonomy, per a lecture slide reproducing Harris's Figure 8-1:
  - Three top-level groups: **utilitarian**, **profit-motivated** and **futile** traders.
  - Order anticipators sit under profit-motivated traders, alongside informed traders and dealers.
  - **Parasitic traders** include order anticipators and bluffers.
  - I could not verify these placements against the book itself. — [Scribd lecture "FINA3307-Lecture4" (search summary)](https://www.scribd.com/document/522091194/FINA3307-Lecture4)
- A book review gives these one-line descriptions:
  - Informed traders, "who profit by bringing prices into line with where they should be".
  - Dealers, "who provide liquidity to other traders by buying and selling out of their often very expensive inventory".
  - Order anticipators, "the parasites who frontrun and imitate the actions of those higher in the chain of information".
  - Bluffers, who spread false information to create transitory price moves.
  - Futile traders, "who think they know what they are doing but serve to provide money and energy to the informed traders". The review calls chartists and trend followers "mainly futile traders".
  - [DailySpeculations review](https://dailyspeculations.com/reviews/books/trading-exchanges-harris.html)
- Harris, "Order Exposure and Parasitic Traders" (1997 working paper):
  - "the art of trading lies in knowing when and how to expose trading interest".
  - Exposure is costly because others may front-run the order or refuse to trade with it.
  - Summaries list parasitic sub-types as front runners, quote matchers, sentiment-oriented technical traders and manipulators.
  - I could not retrieve the original text (403). — [search summary; Scribd copy](https://www.scribd.com/document/430142185/Exposure-pdf)
- Order anticipation is empirically real: HFTs lean against, then trade with, informed institutional orders. — [van Kervel & Menkveld 2019](https://econpapers.repec.org/RePEc:bla:jfinan:v:74:y:2019:i:3:p:1091-1137)
- Predatory trading induces or exploits other traders' forced trades and causes overshooting. — [Brunnermeier & Pedersen 2005](https://www.princeton.edu/~markus/research/papers/predatory_trading.htm)

**The 1920s pools: what the evidence says**
- Pools were "agreements, often written, among a group of traders to delegate authority to a single manager to trade in a specific stock for a specific period of time and then to share in the resulting profits or losses". The Senate Banking and Currency Committee (1932–34) concluded that they were attempts at manipulation. — [Jiang, Mahoney & Mei, NYU WP 2004 (published JFE 77(1):147–170, 2005)](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)
- The manipulative reading, from Leffler & Farwell, quoted by Jiang, Mahoney & Mei: a "heavy 'churning' of the stock… few things attract speculators more quickly than a rising volume". Galbraith says pools bought to "attract the interest of people watching the tape". — [JMM WP](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)
- The informed reading, from Huebner (1934) and Pratt (1921): pool participants "seek out undervalued stocks and purchase them quietly in order to profit from a later price rise". This is the Wyckoff accumulation narrative. — [JMM WP](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)
- Results: in a hand-collected sample (55 pools drawn from the Senate's 1929 list of 107 stocks), "the evidence suggests informed trading rather than manipulation". Mahoney (1999) found modest positive abnormal returns that were **not** followed by abnormally negative returns, whereas manipulation would predict a reversal. The Senate hearings "generated little hard evidence of manipulation". — [JMM WP](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)

**What is illegal today**
- **US Securities Exchange Act 1934, §9(a)(1)** (15 U.S.C. 78i) bans acts "For the purpose of creating a false or misleading appearance of active trading", including transactions that involve "no change in the beneficial ownership" (wash sales) and matched orders. — [LII 15 U.S.C. 78i](https://www.law.cornell.edu/uscode/text/15/78i)
- **§9(a)(2)** bans "a series of transactions" "creating actual or apparent active trading in such security, or raising or depressing the price" "for the purpose of inducing the purchase or sale of such security by others". §9(a)(3)–(5) ban touting price moves caused by manipulative market operations. — [LII](https://www.law.cornell.edu/uscode/text/15/78i)
- **CEA §4c(a)(5), 7 U.S.C. 6c(a)(5):** it is unlawful to engage in conduct that "violates bids or offers"; that "demonstrates intentional or reckless disregard for the orderly execution of transactions during the closing period"; or that is "spoofing" "(bidding or offering with the intent to cancel the bid or offer before execution)". The attribution to Dodd-Frank §747 (2010) is from general knowledge and is not shown on the fetched page. — [LII 7 U.S.C. 6c](https://www.law.cornell.edu/uscode/text/7/6c)
- **JPMorgan gold spoofing:** the CFTC imposed a record **$920 million** (Release 8260-20, 29 Sep 2020). Precious-metals and Treasury traders, including desk heads, placed orders in gold, silver, platinum, palladium and Treasury futures that they intended to cancel before execution, from 2008 to 2016. — [CFTC release 8260-20](https://cftc.gov/PressRoom/PressReleases/8260-20)
- **EU MiCA (Reg. (EU) 2023/1114), Art. 91**, applicable from 30 Dec 2024:
  - "No person shall engage in or attempt to engage in market manipulation".
  - Prohibited conduct includes conduct that "gives, or is likely to give, false or misleading signals as to the supply of, demand for, or price of, a crypto-asset".
  - It also covers "securing a dominant position" and order placement, "including any cancellation or modification thereof", that makes it "more difficult for other persons to identify genuine orders" or creates false signals, "including by" "entering orders to initiate or exacerbate a trend".
  - [ESMA Interactive Single Rulebook, MiCA Art. 91](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-91-prohibition-market-manipulation)
  - Commentary says Art. 91 mirrors the manipulation catalogue of **MAR Art. 12** (Reg. (EU) 596/2014). — [Mondaq, "Fintech insights 12"](https://webiis08.mondaq.com/fintech/1792090/fintech-insights-12-mica-prevention-of-market-abuse)
- **Crypto wash trading:**
  - Wash trading "averaged over 70 %" of reported volume on unregulated exchanges and was absent on regulated ones, across 29 exchanges from 9 Jul to 3 Nov 2019. — [Cong, Li, Tang & Yang, Management Science 69(11):6427–6454 (2023), NBER w30783](https://nber.org/papers/w30783); [Reading repository](https://centaur.reading.ac.uk/113166)
  - Operation Token Mirrors (Oct 2024): the FBI created the bait token NexFundAI, and market makers (Gotbit, ZM Quant, CLS Global, MyTrade) were charged with wash trading. Prosecutors described these as the first criminal charges against crypto market makers for wash trading. — [DOJ D. Mass. press release](https://www.justice.gov/usao-ma/pr/eighteen-individuals-and-entities-charged-international-operation-targeting-widespread); [Decrypt](https://decrypt.co/285503/feds-charge-gotbit-others-market-manipulation)

### Inferences
- **[ANALOGIE] CO ≈ Harris's informed (value) traders who carry a liquidity problem**, plus dealers who intermediate. "Thinking like the CO" means asking the execution question from Q1: *where can I get size without moving price?* The answer is where other traders **must** trade: climaxes, stop pools beyond obvious levels, and liquidation clusters.
- **[ANALOGIE] "Weak hands" are two groups.** (a) Utilitarian traders forced by liquidity needs or margin calls, i.e. forced flow. (b) Futile or pseudo-informed traders, such as chartists who all put stops just under the same swing low (Osler's clustering). Their predictable orders are the CO's liquidity.
- **[ANALOGIE] Stop hunting ≈ parasitic behaviour.** Order anticipators (front-runners, squeezers) and predatory traders trigger or ride forced flows. Dealers who misuse client order information do it illegally (FCA 2014). Spoofed "walls" are bluffing, which is illegal (CEA §4c; MiCA Art. 91(3)(b)).
- **[ÉTABLI] An honest definition of the CO for the memo.** No single operator moves BTC or gold. What exists is (i) large informed or institutional metaorders executed by algorithms (Almgren-Chriss lineage), (ii) inventory-managing liquidity providers, (iii) order anticipators and HFTs, and (iv) mechanical forced flows (stops, liquidations). Wyckoff's "Composite Man" is a **useful heuristic** for reading their *net* footprint in volume and price. It is not a claim of conspiracy. The very pools that inspired it look statistically like informed accumulation (JMM 2005).
- **[ÉTABLI] Gold-specific caution.** Spoofing in COMEX precious-metals futures was sanctioned (JPM, 2008–2016). Displayed depth ("walls") can be fake; **executed** volume cannot be cancelled. This is a direct argument for the project's "volume first" rule.
- **[ANALOGIE] The legal line.** A legitimate large order that moves price, or even triggers stops, is not in itself manipulation. The illegal elements are false or misleading signals, fictitious devices, intent to cancel (spoofing), wash or matched trades, and touting. This is not legal advice.
- **[ÉTABLI] Crypto caveat.** On unregulated venues, a large share of "volume" was fake in 2019 (Cong et al.). Volume-based Wyckoff reads should rely on major venues with credible volume. The project's choice of Binance through Coinalyze is a reasonable default, but I found no venue-level audit for 2026.

### Gaps
- I could not verify Harris's exact sub-categories (front runners, sentiment-oriented technical traders, squeezers, quote matchers) or their chapter placement against the book. The Harris 1997 paper was blocked (403).
- I did not fetch the MAR Art. 12 text or the Annex I indicators. The Dodd-Frank §747 attribution comes from general knowledge.
- Primary sources on specific 1929 pools (for example the RCA pool) were not retrieved.

---

## Q5. Crypto: how should OI change (in coin), funding, the long/short ratio, liquidations and CVD be read during a spring, a test, an SOS and a back-up? What academic or industry research exists on liquidation cascades and stop hunts in crypto?

### Takeaway
Read each event in the order **volume/spread → OI in coin → third-party metrics** (L/S ratio, funding, liquidations), and use CVD as the absorption detector.
- **Spring:** a long flush (OI coin↓, long liquidations↑) or trapped breakdown shorts (OI coin↑ then price reclaims), with negative CVD that fails to push price lower.
- **Test:** volume dries up, OI is flat, liquidations are about zero, and price holds.
- **SOS:** volume expands, and OI coin rises with price (new longs). The weaker version is OI coin falling with price, i.e. short covering.
- **Back-up:** volume dries up, OI is stable and funding cools.

Data definitions matter:
- Binance publishes OI both in coin (sumOpenInterest) and in USD value.
- Coinalyze defaults to `convert_to_usd=false`.
- The Binance L/S ratio counts **accounts**, not size.
- Binance's liquidation stream pushes at most **one liquidation per symbol per second**, so liquidation totals are lower bounds.

Research on liquidation cascades is young but growing: BIS on crypto carry, a 2026 arXiv study of seven BTC cascades, and analyses of the October 2025 crash. Stop or liquidation "hunts" are documented mainly by industry reporting, for example on Hyperliquid, where positions are public.

### Cited Findings

**Data definitions**
- Binance `GET /futures/data/openInterestHist`:
  - Fields `sumOpenInterest` ("total open interest", e.g. "20403.12345678") and `sumOpenInterestValue` ("total open interest value", e.g. "176196512.12345678").
  - Periods from 5m to 12h (one more period value was hidden on the page).
  - "Only the data of the latest 1 month is available"; periods with no trades are skipped and "not backfilled".
  - [Binance API docs, Open Interest Statistics](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics)
- Coinalyze API:
  - Open-interest endpoints take `convert_to_usd`, enum "true"/"false", **default "false"**.
  - L/S ratio fields: `r` = "Ratio", `l` = "Longs %", `s` = "Shorts %".
  - Liquidation fields: `l` = "Longs liquidation volume", `s` = "Shorts liquidation volume".
  - OHLCV field `bv` = "Buy volume. `Sell volume = v-bv`", and `btx` = buy trades.
  - [Coinalyze API documentation (OpenAPI spec embedded in page)](https://api.coinalyze.net/v1/doc/)
- Coinalyze's aggregated BTC OI adds coin-margined OI to stablecoin-margined OI converted to USD notional, and also publishes each family in the other unit. — [Coinalyze BTC open interest page (search summary)](https://coinalyze.net/bitcoin/open-interest/)
- Binance funding:
  - "Funding Rate (F) = [Average Premium Index (P) + clamp (interest rate - Premium Index (P), 0.05%, -0.05%)] / (8 / N)".
  - The interest rate is "0.03% daily by default" (0.01 % per 8 h). Funding is settled every 8 h by default (00:00, 08:00 and 16:00 UTC) and can switch to 1 h when the cap or floor is hit.
  - When funding is positive, "traders long on a perpetual contract will pay a funding fee to traders on the opposing side". Majors such as BTCUSDT are capped at ±0.75 × the maintenance margin ratio, and other USDⓈ-M perps at ±2 %.
  - [Binance FAQ, funding rates](https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031)
- Binance `GET /futures/data/globalLongShortAccountRatio` describes an "account num ratio of all traders", with "Only the data of the latest 30 days". The field labels on the page appear misaligned. Separate "Top Trader" account and position ratios exist. — [Binance API docs, Long/Short Ratio](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio)
- Binance liquidation stream `!forceOrder@arr`: "For each symbol, only the latest one liquidation order within 1000ms will be pushed as the snapshot." — [Binance API docs, All Market Liquidation Order Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams)

**Research on cascades, leverage and order flow**
- **BIS WP 1087, "Crypto carry"** (Schmeling, Schrimpf & Todorov; 2023, revised Oct 2025):
  - The futures-spot gap can reach up to 60 % p.a. It is driven by convenience yields, demand from trend-chasing small investors and scarce arbitrage capital.
  - "high crypto carry predicts future price crashes".
  - Margin spikes and liquidations make cash-and-carry risky.
  - [BIS WP 1087](https://www.bis.org/publ/work1087.htm)
  - Companion column: "a 10% increase in standardised carry predicts a 22% increase in sell liquidations relative to total open interest over the following month". — [VoxEU/CEPR column](https://cepr.org/voxeu/columns/crypto-carry-market-segmentation-and-price-distortions-digital-asset-markets)
- **Garcia Seuma (arXiv 2607.27070, July 2026; preprint):**
  - Seven BTC liquidation cascades from 2022 to 2025, "including the record 19B USD event of 10 October 2025".
  - "Price carries the critical-slowing-down signature in five of seven events", but not in the two tariff shocks.
  - The only cross-event regularity is "a compression of taker order-flow variance", which "is a population-level precursor, not a per-event alarm".
  - [arXiv 2607.27070](https://arxiv.org/abs/2607.27070)
- **Lim, "Anatomy of a Crypto Cascade: Minute-Level Evidence from the October 2025 Crash" (SSRN):** using minute-level Binance and Bybit data for spot, perps and mark prices, futures led the crash, and the **mark price** used for liquidations undershot both spot and futures, creating a feedback loop. Snippet level only; the page returned 403. — [SSRN 6579278](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6579278)
- **Size of the Oct 10–11, 2025 event:** CoinGlass ranks 10 Oct 2025 as the largest liquidation event, at about **$19.16 bn**, triggered by the US 100 % tariff announcement on China. Other CoinGlass-based reports say $19.27 bn in 24 h. CoinGlass itself says the true total may be higher because of platform reporting delays. — [KuCoin blog (CoinGlass ranking)](https://www.kucoin.com/blog/top-10-largest-crypto-liquidation-events-of-all-time); [The Daily Hodl](https://dailyhodl.com/2025/10/10/19270000000-in-bitcoin-and-crypto-liquidated-in-largest-single-day-leverage-meltdown-in-history/amp/)
- **Order flow in crypto:**
  - On BitMEX XBTUSD, **trade** flow imbalance explains contemporaneous price changes better than order-book flow imbalance. The author attributes this to the lack of depth and low update rates in crypto markets.
  - Over large enough intervals, price change shows a strong linear relation with order flow imbalance.
  - [Silantyev (2019), Digital Finance 1:191–218, IDEAS](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)
- **Square-root impact in Bitcoin** holds over four decades (more than 1 M metaorders). — [Donier & Bonart, arXiv 1412.4503](https://arxiv.org/abs/1412.4503)
- **Public "whale hunts" (industry reporting):**
  - In March 2025 a roughly $420 M 40× BTC short on Hyperliquid drew a public call on X to push price up and liquidate it.
  - 10x Research argued that public position tracking lets groups "deliberately target" liquidation levels.
  - In a separate case, an ETH whale's forced close cost Hyperliquid's HLP vault about $4 M. The Bybit CEO *suspected* that the whale had exploited the liquidation engine.
  - These are news sources, not peer-reviewed. — [Cointelegraph](https://cointelegraph.com/news/traders-targeting-hyperliquid-whales-significant-positions-trigger-liquidations-10x-research); [BeInCrypto](https://beincrypto.com/whale-hunt-hyperliquid-bitcoin); [The Defiant](https://thedefiant.io/news/defi/whale-s-nine-figure-eth-liquidation-costs-hyperliquid-usd4-million)
- **Round-number clustering in BTC**, the precondition for stop clusters: more than 10 % of prices end in 00. — [Urquhart 2017](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html)

### Inferences

**Why OI in coin, not in USD — [ÉTABLI arithmetic, from the Binance field definitions]**
- For linear USDT perps, OI_USD = OI_coin × price, so ΔOI_USD% ≈ ΔOI_coin% + Δprice%. A USD series rises on a rally even if positions shrink.
- Worked check of the project's own case: OI coin −0.36 % with OI USD +0.81 % implies price ≈ +1.17 % over the window. The "demand" read in USD was just the price term; the coin series showed short covering.
- **[NON VÉRIFIÉ]** For inverse, coin-margined contracts, whose size is fixed in USD (Binance COIN-M BTCUSD perps are generally stated to be $100 per contract), the artefact is reversed: the coin-equivalent OI falls mechanically when price rises. Aggregates that mix both families (as Coinalyze's aggregate does) carry price-dependent distortions. Prefer single-family linear OI in coin for reading direction.

**Event by event, in the project's order: volume → OI coin → third-party metrics**

Spring (flush below support, then reclaim):
- (1) Volume and spread expand on the pierce; the close is back inside the range with a high CLV. That is effort without downside result, i.e. absorption.
- (2a) OI coin ↓ with long liquidations ↑: weak longs were flushed and stop or liquidation supply consumed. This is the "clean" spring. **[ANALOGIE, via Osler + Q1]**
- (2b) OI coin ↑ on the break, then price reclaims: new breakdown shorts are trapped and become future squeeze fuel. **[ANALOGIE]**
- (3) Funding dips toward or below zero (shorts crowded). CVD is strongly negative while price stops falling, which means passive bids are absorbing taker sells. Long liquidations are a **lower bound** because of Binance's one-per-second snapshot.
- Invalidation: a close below the spring low with expanding volume and rising OI coin means real supply, not a spring.

Test of the spring / ST:
- (1) Volume is clearly below the climax and spring, with a narrow spread and a higher low.
- (2) OI coin is flat or slightly down: no new aggressive shorts.
- (3) Liquidations ≈ 0 (orderly), funding is neutral, CVD is mildly negative but price holds.
- Mechanism: small sell flow produces a small price response, i.e. supply is exhausted (Cont-Kukanov-Stoikov). **[ANALOGIE]**
- Warning: a pullback with OI coin rising, falling L/S ratio (shorts entering) and a heavy CVD means sellers are building and the test may fail. This is exactly the "ambiguous OI → use tertiary metrics" case in the project rules.

SOS / jump across the creek:
- (1) Wide-spread, high-volume up bar closing near the high. Llorente et al. show that speculative or informed high-volume moves tend to **continue** (see Q6).
- (2a) OI coin ↑ with price: new longs, i.e. demand that commits capital. This is the strong version.
- (2b) OI coin ↓ with price ↑ plus short liquidations: covering or squeeze. This is the weaker version and needs a back-up to confirm.
- (3) Funding rises but stays contained. Extreme funding plus OI↑ points to the crowded-long, crash-prone state described by BIS crypto carry. CVD is positive and price responds, meaning thin asks.
- Per the project rule, a breakout is only an SOS once it holds and is followed by an LPS above.

Back-up / LPS:
- (1) Volume dries up and spreads narrow on the pullback to the creek or former resistance (Osler: the old level now holds take-profits and limit bids; Kavajecz & Odders-White: support/resistance sit on depth peaks).
- (2) OI coin is stable or dips slightly (profit-taking), without collapsing. An OI coin collapse with price falling means longs are fleeing and the SOS failed.
- (3) Funding cools from SOS levels (leverage flushed), liquidations are small and CVD is roughly flat.

UTAD / upthrust: mirror everything above. Buy-stops and short liquidations above resistance supply the liquidity. Positive CVD with no upside progress means passive sellers are absorbing. Rising OI coin at resistance in a downtrend means longs are being trapped (the project rule (4) on reading OI by frame and location).

**Other inferences**
- **[ÉTABLI] The L/S account ratio is not size.** Every open contract has a long and a short, so a ratio of 2 means more *accounts* are net long, not more BTC. It mostly maps retail crowding. The Top-Trader position ratio is closer to size. Use it as a crowding tell, not as a measure of net demand.
- **[ÉTABLI → ANALOGIE] Liquidations are forced market orders.** They are Osler's stops without discretion, which is why they cascade (Brunnermeier-Pedersen overshooting) and why springs and UTADs in perps can overshoot further than in spot. The October 2025 evidence that the mark price undershot (Lim) shows that venue mechanics can manufacture extra "spring depth".
- **[ANALOGIE] Coils before cascades.** The Garcia Seuma result that taker order-flow variance compresses before cascades matches the Wyckoff observation that quiet narrowing precedes violent tests. It is a population-level effect, so do not use it as a timing trigger.
- **[ÉTABLI] Venue hygiene.** Use credible-volume venues (Cong et al.), and treat liquidation magnitudes from the Binance stream as lower bounds.

### Gaps
- I found no peer-reviewed study of OI, funding or L/S during *springs or tests specifically*. The event table above is an analogy built from the mechanisms; it should be validated with the project's backtester (`screener/optimize.py`, out-of-sample) before being treated as an edge.
- No academic study isolates intentional stop or liquidation hunting on centralised-exchange perps. The evidence is industry reporting (Hyperliquid) plus the mechanism literature.
- The long/short split of the Oct 2025 liquidations varies across reports (long-dominated per most CoinGlass-based outlets; at least one item reversed the labels). I did not verify the exact figures.
- The exact contract size of Binance COIN-M BTCUSD perps was not checked.
- I could not resolve the misaligned field descriptions on Binance's L/S ratio page from the page alone.

---

## Q6. Has any academic or empirical study tested Wyckoff patterns, springs/false breakouts, or the reliability of support/resistance?

### Takeaway
I found **no peer-reviewed test of the Wyckoff method, its springs or its tests**. What is tested are its **building blocks**:
- Support/resistance levels interrupt trends slightly more often than chance (Osler: 60.8 % vs 56.2 %).
- They coincide with order-book depth peaks (Kavajecz & Odders-White).
- The probability of bouncing rises with the number of prior bounces at short time scales (Garzarelli et al.).
- Stop clusters make breakouts accelerate (Osler).
- High-volume moves reverse when liquidity-driven and continue when informed (Campbell-Grossman-Wang; Llorente et al.).

The edges are small, depend on the time scale and are exposed to data snooping. Once costs are included, simple support/resistance trading has not beaten buy-and-hold.

### Cited Findings
- **Wyckoff itself:** my searches across SSRN, arXiv and the general web found no peer-reviewed empirical test of Wyckoff schematics or springs. The closest is arXiv 1812.02527, which uses regimes "loosely modeled on the Wyckoff Price Regimes" in a Markov-switching strategy and does not test Wyckoff patterns. — [arXiv 1812.02527](https://arxiv.org/abs/1812.02527)
- **Osler (2000):** bounce frequency **60.8 %** at published levels against **56.2 %** at arbitrary levels, with power lasting at least 5 days (details in Q2). — [FRBNY EPR](https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf)
- **Osler (2005):** faster trends after crossing round numbers; reversal 59.3 % vs 54.8 % (Q2). — [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)
- **Garzarelli, Cristelli, Pompa, Zaccaria & Pietronero (2014), Sci. Rep. 4:4487:**
  - Data: 9 LSE stocks, tick data for 2002, at time scales of 45, 60, 90 and 180 s.
  - "the probability of bouncing on a support or a resistance is an increasing function of the number of previous bounces".
  - Significant (p < 0.0001) at 45–90 s, not significant at 180 s. Shuffled series give about 0.5.
  - After costs, "these minor arbitrage opportunities are usually no more profitable".
  - [ar5iv full text](https://ar5iv.labs.arxiv.org/html/1110.5197)
- **Kavajecz & Odders-White (2004), RFS 17(4):1043–1071:** support and resistance levels **coincide with peaks in limit-order-book depth**, and technical rules "locate depth already in place". — [IDEAS](https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html)
- **Zapranis & Tsinaslanidis (2012), Applied Financial Economics 22(19):1571–1585:** using NYSE/NASDAQ data over about 20 years, support levels predict trend interruptions better than resistances, but they do **not** produce excess returns over buy-and-hold, "aligned with the efficient market hypothesis". — [EconPapers](https://econpapers.repec.org/RePEc:taf:apfiec:v:22:y:2012:i:19:p:1571-1585); [Canterbury repository](https://repository.canterbury.ac.uk/item/871vw/identifying-and-evaluating-horizontal-support-and-resistance-levels-an-empirical-study-on-us-stock-markets)
- **Brock, Lakonishok & LeBaron (1992)** tested 26 rules, including trading-range breaks, on DJIA data from 1897 to 1986, and the rules beat cash. **Sullivan, Timmermann & White (1999)** built nearly 8,000 rule variants and corrected for data snooping (White's Reality Check). Some rules still beat the benchmark in 1897–1986, but performance weakened out of sample. BLL themselves warned "the dangers of data snooping are immense". — [Sullivan-Timmermann-White PDF](https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf)
- **Llorente, Michaely, Saar & Wang (2002), RFS 15(4):1005–1047:** "returns generated by risk-sharing trades tend to reverse themselves while returns generated by speculative trades tend to continue themselves". Across stocks, the volume-autocorrelation relation tracks the extent of informed trading. — [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:15:y:2002:i:4:p:1005-1047); [PDF](https://www.johnhcochrane.com/s/llorente_michaely_saar_wang_volume_rfs.pdf)
- **Campbell, Grossman & Wang (1993):** high-volume declines are more often followed by higher expected returns (liquidity reversal). — [Harvard DASH](https://dash.harvard.edu/bitstream/1/3128710/2/campbell_trading.pdf)
- **Jiang, Mahoney & Mei (2005)** on the 1929 pools: the evidence fits informed trading (accumulation) better than manipulation (Q4). — [JMM WP](https://archive.nyu.edu/bitstream/2451/26529/2/FIN-04-022.pdf)

### Inferences
- **[ÉTABLI] Supported components:**
  - (a) Range boundaries are real liquidity zones: depth peaks and order clusters.
  - (b) Crossing them releases stop-driven acceleration, the mechanism behind springs and upthrusts that fail or succeed.
  - (c) Repeated tests raise the odds of a bounce, at least at very short horizons.
  - (d) Volume conditions what happens next. A liquidity-driven high-volume move (climax) tends to reverse, which matches SC → AR. A high-volume move driven by informed flow tends to continue, which matches the SOS.
- **[ANALOGIE] Not supported as a whole:** no study validates the full sequence (SC → AR → ST → Spring → test → SOS → LPS) or the claim that a low-volume test *predicts* a markup. The memo should present Wyckoff as a **coherent interpretive grammar built on mechanisms that are individually documented**, not as a proven pattern system.
- **[ÉTABLI] Effect sizes are modest:** about 4–5 pp bounce edges, minute-to-hour persistence, no excess returns after costs in equity support/resistance tests. A discretionary H1/H4 trader should treat tests as **probability tilts plus risk-definition points** (the stop goes beyond the spring low, which is exactly where the stop cluster was consumed), not as certainties.
- **[ANALOGIE] Double-edged memory.** The more obvious a level becomes through many tests, the more stops cluster just beyond it (Osler). If it finally breaks, the cascade is larger. "Multiple tests strengthen a level" (Garzarelli) and "obvious levels get run" (Osler) are both true. This fits the project rule of holding both scenarios until the range breaks and confirming any breakout with a back-up.
- **Practical:** the repository already has walk-forward/OOS machinery (`screener/backtest.py`, `screener/optimize.py`). It is the right tool to test, on BTC perps, whether "spring + low-volume test + OI coin pattern" beats arbitrary-level controls. Osler's arbitrary-level bootstrap is a good template for that control.

### Gaps
- I did not find any peer-reviewed or replicable study of **false-breakout frequencies** in crypto, or of Wyckoff springs in any market. Practitioner statistics (for example chart-pattern encyclopedias) were not evaluated.
- Garzarelli et al. report bounce probabilities only in figures, which I could not read. Text values are "well above 0.5" against about 0.5 for shuffled data.
- I did not access the full texts of Kavajecz & Odders-White and Zapranis & Tsinaslanidis; their samples and regression details are not verified.
