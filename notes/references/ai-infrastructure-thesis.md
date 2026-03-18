# AI Infrastructure Investment Thesis: The Bottleneck Cascade

**Written:** 2026-03-18
**Status:** Active thesis — update as waves shift

---

## Core Insight: Bottlenecks Move Downstream

AI infrastructure spending follows a predictable pattern: **money hits the most obvious bottleneck first, then cascades to the next one.** Each wave creates the next bottleneck. The investors who see the next bottleneck before the market prices it win.

```
Training compute → Networking → Power → Cooling → Memory → Inference/Edge
     (NVDA)         (AVGO)      (NOW)    (NOW)    (NOW)     (NEXT)
```

---

## Wave 1: Training Compute (2022-2024) — OVER

**Bottleneck:** Not enough GPU compute to train foundation models.
**Winner:** NVIDIA (NVDA) — the only game in town. CUDA lock-in since 2006 meant every AI lab bought H100s.
**Signal it was happening:** ChatGPT launch (Nov 2022), every company scrambling for GPU allocations, 6-month delivery backlogs.
**Why it ended:** Supply caught up. NVIDIA shipped enough H100s/H200s. Training clusters were built. The constraint shifted.

**Return:** NVDA went from ~$15 (split-adjusted) in late 2022 to $140+ by mid 2024. ~9x in 18 months.

**Lesson:** The first bottleneck is always the most obvious and fastest to price in. By the time retail investors understood "AI needs GPUs," the trade was crowded.

---

## Wave 2: Networking + Custom Silicon (2024-2026) — MATURING

**Bottleneck:** You have 100K+ GPUs — now connect them. Off-the-shelf GPUs are too expensive at hyperscale; custom chips are 2-3x more efficient.
**Winners:**
- **Broadcom (AVGO)** — 70%+ share in data center switching (Tomahawk, Jericho). Designs custom ASICs for Google (TPU), Meta (MTIA), OpenAI. AI revenue doubled YoY to $8.4B/quarter.
- **Marvell (MRVL)** — custom silicon for Amazon/AWS (Trainium). Smaller but growing.
- **Arista Networks (ANET)** — data center networking software/switches.

**Signal it was happening:** Hyperscalers announced custom chip programs (2023-2024), networking capex surged, Broadcom AI revenue went parabolic.
**Why it's maturing:** The market now understands the custom silicon story. AVGO trades at 18x forward earnings despite 47% revenue growth — it's priced for success but not yet for dominance.

**Current status:** Still investable. AVGO at $325 is attractive (Kelly sizer: +74% weighted return, 3/4 models bullish). But the "easy" part of the re-rating is happening now.

---

## Wave 3: POWER & ENERGY (2025-2028) — ACTIVE NOW

**Bottleneck:** Data centers need electricity. A LOT of it.
- US data center demand: 74 GW by 2028 (Morgan Stanley), but only ~25 GW available
- **49 GW shortfall** — that's ~50 nuclear reactors worth of power
- 70% of the US grid is approaching end-of-life (built 1950s-1970s)
- Power transformer lead times: 2-4 years. You can't just build this quickly.

**This is the most predictable bottleneck because it's physical.** You can't download more electricity.

### Investment opportunities (ranked by model consensus):

| Ticker | Company | What they do | Autoresearch | GBM 3y | Combined signal |
|--------|---------|-------------|-------------|--------|-----------------|
| **VST** | Vistra Energy | Largest competitive power generator in US, nuclear fleet | +29% | +108% | Very strong — 4/4 models agree |
| **GEV** | GE Vernova | Gas turbines, grid equipment, nuclear services | +32% | +46% | Strong — both models agree |
| **CEG** | Constellation Energy | Largest US nuclear fleet, 20yr PPA with Microsoft | +29% | +37% | Solid — both agree |
| **ETN** | Eaton Corp | Power management, electrical infrastructure, acquired Boyd (liquid cooling) | +22% | +28% | Moderate — steady compounder |
| **PWR** | Quanta Services | Builds transmission lines, substations, grid infrastructure | +28% | +7% | Divergent — autoresearch more bullish |

### Why nuclear specifically:
- AI data centers need **24/7 baseload power** (not intermittent solar/wind)
- Nuclear has the highest capacity factor (~93%) of any power source
- Constellation signed a 20-year PPA with Microsoft to restart Three Mile Island Unit 1
- SMR (Small Modular Reactor) technology from NuScale, Oklo is promising but **too early** — NuScale's first project delayed to 2034. These are venture bets, not infrastructure plays.

### The "non-obvious" power play:
**Natural gas** is the bridge fuel. Every new data center needs reliable power NOW, and gas turbines can be deployed in 18-24 months vs 5-10 years for nuclear. GE Vernova (GEV) builds the turbines.

---

## Wave 4: COOLING (2025-2027) — ACTIVE NOW

**Bottleneck:** Next-gen AI chips (NVIDIA B200, GB200) draw 1000-1500W each. A rack of them draws 120kW+. Traditional air cooling can't handle this.
- Liquid-cooled racks: expected to be 47% of deployments by end of 2026 (up from <10% in 2023)
- CDU (Coolant Distribution Unit) market: $1B → $7.7B at 33% CAGR

### Investment opportunities:

| Ticker | Company | What they do | Autoresearch | GBM 3y | Signal |
|--------|---------|-------------|-------------|--------|--------|
| **VRT** | Vertiv Holdings | #1 data center cooling/power. $15B backlog, 252% order growth | +32% | +90% | Very strong — 4/4 agree |
| **ETN** | Eaton Corp | Acquired Boyd Thermal ($9.5B) for liquid cooling | +22% | +28% | Also a power play — double exposure |
| **MOD** | Modine Manufacturing | Pure-play thermal management, faster growth than Vertiv | Not in DB | Not in DB | Research needed |

**Vertiv (VRT)** is the standout. $15B backlog at 2.9x book-to-bill, 28% organic revenue growth guided for 2026. The stock has already run 50% YTD but the backlog provides 2+ years of visibility.

---

## Wave 5: MEMORY (2025-2028) — EMERGING

**Bottleneck:** AI models are memory-bandwidth limited, not compute-limited. Moving data between memory and compute cores costs more time/energy than the actual math.
- HBM (High Bandwidth Memory) demand is exploding — Micron sold out through 2026
- HBM4 samples delivered to NVIDIA with 2.8 TB/s bandwidth
- DRAM shortage won't end in 2026 — NVIDIA told fabs "build more, we'll buy it all"

### Investment opportunities:

| Ticker | Company | What they do | Autoresearch | GBM 3y | Signal |
|--------|---------|-------------|-------------|--------|--------|
| **MU** | Micron Technology | #3 memory maker. HBM capacity sold out through 2026 | +83% (0.99 conf!) | +2% | Massive divergence — autoresearch very bullish, GBM cautious |

**The MU divergence is interesting.** Autoresearch sees +83% with 0.99 confidence (one of its highest conviction calls), but GBM 3y sees only +2%. This suggests the opportunity is real but timing-dependent — the memory supercycle could play out over 2-3 years, which GBM's historical patterns may not fully capture.

SK Hynix and Samsung are the other HBM leaders but trade on Korean exchanges (harder to access).

---

## Wave 6: INFERENCE & EDGE (2027-2030) — NEXT

**Bottleneck:** Training is a one-time cost. Inference (running models in production) is the ongoing cost — and it's about to explode.
- Inference: ~66% of AI compute in 2026, expected to reach 70-80% by 2027
- Inference-optimized chip market: >$50B in 2026
- Edge AI: 80% of CIOs will use edge inference by 2027
- Small, task-specific models will be used 3x more than general LLMs by 2027

### This wave is still early. Watch for:
- **Custom inference chips** — this is where Broadcom's ASIC business goes next (Google TPU is already inference-optimized)
- **Edge hardware** — NVIDIA's AI Grid for distributed inference, Qualcomm for on-device AI
- **Software optimization** — quantization (8-15x compression), caching (90% cost savings), batching. The winners here are likely software companies, not hardware.
- **Telcos as edge infrastructure** — they own the towers and fiber. NVIDIA is already partnering with telcos for distributed edge inference.

**Too early to invest specifically in inference.** The beneficiaries overlap with existing holdings (AVGO for custom chips, NVIDIA for inference GPUs). The pure-play edge inference companies don't exist yet at scale.

---

## Portfolio Implications

### What we should own (ranked by timing + conviction):

**High conviction — act now:**
1. **AVGO** ($325) — Wave 2 maturing but still 74% upside. Custom silicon + networking moat. Already planning to buy with DIS proceeds.
2. **VST** ($162) — Wave 3 power. 4/4 models agree, +108% GBM 3y. Kelly sizer ranked it top 5.
3. **VRT** ($~130) — Wave 4 cooling. 4/4 models, +90% GBM 3y. $15B backlog provides visibility.

**Moderate conviction — research more:**
4. **MU** (~$105) — Wave 5 memory. Autoresearch loves it (+83%, 0.99 conf) but GBM is flat. HBM sold out through 2026. Needs /research to resolve divergence.
5. **CEG** (~$270) — Wave 3 nuclear. Both models agree (+29-37%). Constellation is the blue-chip nuclear play.
6. **GEV** (~$380) — Wave 3 gas turbines + grid. Both models agree (+32-46%). Bridge fuel thesis.

**Too early / too risky:**
- SMR plays (NuScale, Oklo) — projects delayed to 2030s. Pure speculation.
- Edge inference pure-plays — market doesn't exist yet at investable scale.

### What we already own that benefits:
- **GOOG** — builds custom TPUs (Broadcom-designed), owns massive data center infrastructure, benefits from all waves
- **TSLA** — Dojo custom chips (Broadcom-designed), robotaxi inference at edge. Indirect play on Waves 2+6.

---

## How to Track This Thesis

**Leading indicators that a wave is peaking:**
- Supply catches up to demand (GPU availability was the signal for Wave 1 peaking)
- Revenue growth decelerates for wave leaders
- Market starts pricing in the next bottleneck (analysts publish "power is the new GPU" reports — this is happening NOW)

**Leading indicators for the next wave:**
- Earnings calls mentioning new constraints ("we can't get enough power/cooling/memory")
- Capex shifting to new categories in hyperscaler filings
- Startups raising rounds in the next bottleneck category

**Review this thesis quarterly.** Update wave status, model outputs, and portfolio positioning.

---

Sources:
- [Morgan Stanley: Powering AI Energy Market Outlook 2026](https://www.morganstanley.com/insights/articles/powering-ai-energy-market-outlook-2026)
- [Goldman Sachs: AI to drive 165% increase in data center power demand](https://www.goldmansachs.com/insights/articles/ai-to-drive-165-increase-in-data-center-power-demand-by-2030)
- [IEA: Energy demand from AI](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai)
- [TrendForce: Memory Wall Bottleneck](https://www.trendforce.com/insights/memory-wall)
- [Deloitte: AI compute power demands](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html)
- [GTC 2026: The Inflection of Inference](https://jasonrowe.com/2026/03/16/the-inflection-of-inference-gtc-2026-and-the-edge-ai-shift/)
- [BlackRock: Buy AI Energy Stocks Over Big Tech](https://www.fool.com/investing/2026/03/04/blackrock-says-buy-ai-energy-stocks-over-big-tech/)
