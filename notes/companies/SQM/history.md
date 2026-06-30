# SQM history — forecast track record

Calibration log. The point is **not** to record what happened to the stock (that's
in any chart) — it's to record **what we predicted, what actually happened, and what
the gap says about how we forecast.** So we stop being wrong *confidently* the same way
twice, and can see our own patterns.

Format per entry, chronological (oldest first, append at the end):
- **Call** — the verdict/conviction/numbers we committed to, with price at the time.
- **Falsifiable bits** — the specific dated, numeric predictions and thesis-break lines.
- **Outcome** — filled in later, when a dated event passes: what actually happened.
- **Self-pattern** — what the miss/hit reveals about *our* process, not just the stock.

The live thesis lives in `notes/companies/SQM.md`; this file is append-only and should
survive any `/research SQM` regeneration of that note.

---

## 2026-05-19 — Initial deep-dive call: BUY (MEDIUM), $82.66

**Call.** BUY, conviction MEDIUM. Entry up to $85, scale-in thirds ($85 now / $75 pullback
/ post-Q2 confirmation). Expected value +33.2%.

**Falsifiable bits (what we committed to):**
- Scenario targets: Bull $150 (+81%, 30%), Base $110 (+33%, 50%), Bear $55 (-33%, 20%).
- Variant perception: iodine/SPN cash cushion ($700M+ EBITDA) structurally underpriced;
  Codelco JV is *risk-removed* not a tax; lithium cost curve steepening puts a floor under price.
- **Explicit upgrade trigger:** "Upgrade to HIGH conviction on Q2 print showing realized
  lithium price >$11/kg AND Salar Futuro filing accepted." Base case assumed ~$11/kg realized.
- **Thesis breaks if:** realized lithium <$9/kg for two consecutive quarters in 2026; OR
  Codelco JV mechanics materially worse than disclosed; OR Salar Futuro permit rejected/pulled.
- Model snapshot (run 2026-05-18 vs $84): GBM cluster $112–142 (+33%/+68%), autoresearch $115,
  DCF cluster bearish $30–59. We weighted GBM+autoresearch → fair value $115–130 (+40%/+55%).

---

## 2026-06-30 — Reconciliation: trigger fired hard, stock fell anyway. $69.28

**What actually happened.**
- **Q1 2026 (reported ~mid-May): realized lithium $18/kg** — vs our base-case ~$11 and our
  ">$11 = upgrade conviction" trigger. The trigger didn't just clear, it was crushed.
- Q1 adj EBITDA **$837M in a single quarter** — ~46% of our *full-year* base-case $1.8B.
- Lithium volume **+25% YoY**; full-year guide raised to **~+15%**. Iodine rev +8.2% YoY,
  higher pricing guided for Q2. Codelco JV (Nova Andino) operating, ~$530M state contributions.
- Sell-side raised targets *into* the move: Scotiabank $100, Deutsche Bank $106.
- **And yet the stock went the other way.** Peaked ~$95 early/mid-May, then fell to **$69.28
  by 2026-06-29 (−27%)**, with a sharp final leg ($83 on 06-17 → $69).

**Why the stock fell despite the beat.** SQM is a near-pure lithium-spot beta name. Lithium
carbonate hit a 2.5-yr high (~CNY 200k/t) mid-May, then corrected ~15–18% to ~CNY 163–169k in
June on fears of **CATL's Jianxiawo mine restart → oversupply**, plus softening demand. The
$18/kg Q1 realized was a contract-lag **high-water mark, not a run-rate** (South America carbonate
spot was only ~$8.3/kg in June). The stock had also already run **+140% over the prior year**.

**Scorecard.** Fundamental call: **right, decisively** (trigger fired, EBITDA/volume/iodine all
beat). Near-term stock call: **wrong** — "entry up to $85" would have bought near a local top, and
the thing is now 16% cheaper than where we said buy. Net: right thesis, mistimed entry.

**Self-pattern (the reason this file exists).**
1. **Second time SQM-specific over-confidence bit us.** Auto-memory already carries
   "stale data led to a wrong SQM conclusion." Same name, same failure family: confident on SQM
   off a snapshot that the market had already moved past.
2. **The recurring error: anchoring conviction to the company's *trailing realized print* on a
   commodity-beta name.** We set the upgrade trigger on SQM's realized price (>$11/kg). But the
   stock discounts **forward spot**, not last quarter's contract-lagged realized. Being right that
   the company would print a great number told us almost nothing about the stock from here, because
   the move had already happened and spot had already turned.
3. **Calibration fix going forward:** for commodity-beta names, the falsifiable prediction must be
   on (a) the **spot commodity direction** and (b) **how much is already priced in after a big run**,
   not just the company's own realized/EBITDA. "Great Q is coming" ≠ "stock goes up" once it's up 140%.

**Current expectation (to be reconciled at the next entry).** Lean BUY / accumulate at ~$69 — start
a third, leave room toward ~$60 if the spot correction deepens. This is explicitly a lithium-spot bet,
not a value-stock bet. **Watch:** Q2 2026 print (Aug 2026) — does realized hold above ~$13–14/kg as
spot cools? **Thesis breaks if** realized falls back toward $9–10/kg for two quarters, OR the CATL
Jianxiawo restart turns the supply picture structurally loose. *Prediction to grade later: at $69 with
spot mid-correction, was this a good accumulation entry, or did we again confuse "good company news"
with "good stock entry" on a beta name?*

Sources (2026-06-30): Investing.com SQM Q1 2026 earnings transcript; StockTitan SQM 2026 volume-guidance
release; Simply Wall St "why SQM rose 7.1% on Q1"; TradingEconomics lithium price; SunSirs/SMM China
lithium carbonate June 2026.
