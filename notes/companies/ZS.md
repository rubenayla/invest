# Zscaler, Inc. (ZS)

**Sector:** Technology | **Industry:** Software — Infrastructure
**Price:** $175.25 (2026-05-20) | **Market Cap:** $28.2B
**Analysis Date:** 2026-05-20

## Business Primer

**What they do today.** Zscaler sells cloud-delivered security as a subscription service to large enterprises. When an employee at a customer (banks, manufacturers, government agencies, retailers) opens a browser, accesses a software-as-a-service application like Salesforce or Microsoft 365, or tries to reach an internal corporate application, that traffic does not go through the company's own data center or office firewall. Instead, the traffic is routed to one of Zscaler's roughly 150 globally-distributed data centers, where Zscaler inspects every packet, decrypts encrypted traffic, scans it for malware, blocks data exfiltration, applies the company's access policies, and then forwards the traffic on. Revenue is essentially all subscription. The three flagship products are: (1) Zscaler Internet Access — a secure web gateway in the cloud that sits between the user and the public internet; (2) Zscaler Private Access — a replacement for legacy corporate Virtual Private Networks where the user connects to a Zscaler broker which then brokers an outbound connection from inside the customer's network, so private applications are never exposed to the public internet; (3) Zscaler Digital Experience — monitoring that measures end-to-end latency and packet loss from each employee's laptop to each application. Adjacent and newer offerings include Data Protection, AI Protect, and a recently-launched security-operations data fabric built on the acquired Avalor platform. Annual recurring revenue reached $3.36B in Q2 fiscal 2026 (ended January 31, 2026), with 728 customers paying more than $1M per year.

**Why customers choose them (the value proposition).** The traditional corporate security model is "castle and moat." A company puts a stack of physical firewalls at the edge of its office building or data center, points every employee's laptop at the corporate Virtual Private Network, hauls all the traffic — including traffic destined for cloud applications hosted on someone else's data center — back through the corporate perimeter so the firewalls can inspect it, then sends it back out to the cloud. This was already inefficient when most applications lived in the corporate data center; once applications moved to the public cloud and employees moved out of offices, it became expensive (hardware everywhere, backhaul bandwidth) and slow (an employee in Singapore opening Microsoft 365 first sends the request to a corporate firewall in Frankfurt, then to Microsoft in Dublin, then back). It is also dangerous, because the legacy Virtual Private Network exposes the entire corporate network to anyone who steals one employee's credentials — once you are "inside" the moat, you can move sideways to other servers. Zscaler replaces this with what the industry calls "zero trust": the network itself is treated as hostile, and every individual user/device/application connection is independently authenticated and authorized at the moment of the request, by a policy engine sitting in Zscaler's cloud. Concretely, an employee in Singapore opening Microsoft 365 sends the request to the nearest Zscaler data center (Singapore), Zscaler verifies the user's identity with the company's identity provider, inspects the request, and forwards it directly to Microsoft — no backhaul, no Virtual Private Network, no exposure of other corporate servers. The Chief Information Security Officer at a customer like a Fortune 500 bank picks Zscaler over building their own firewall stack (Palo Alto Networks, Cisco, Fortinet) because: there is no hardware to buy, rack, patch, or replace every 5 years; capacity scales automatically as the workforce moves between offices and home; the attack surface of a legacy Virtual Private Network — which keeps generating zero-day exploits across the industry — is eliminated; and end-user experience is faster because traffic takes a shorter path. The lock-in is that once a company's identity policies, data-loss-prevention rules, and 30,000-employee traffic flows are configured in Zscaler, ripping it out is roughly as painful as a multi-year network re-architecture project.

**Where they want to grow.** Three explicit strategic bets. First, expand from "secure internet access" into adjacent security categories so each existing customer pays more per year — Data Protection (preventing data leakage to cloud apps and to generative AI tools), Identity Threat Detection, and AI Protect (a recently-launched bundle that inventories which AI tools employees are using, governs prompt-level data flows, and red-teams the customer's own AI deployments). Second, move into the security operations center, traditionally the turf of Splunk and CrowdStrike, by combining the recently-acquired Avalor data-fabric platform (a security data lake that normalizes telemetry from 150+ pre-built tool integrations) with the company's existing 400 billion daily transaction signals to sell an Agentic AI-driven Security Operations product that triages alerts automatically. The 2026 acquisition of Red Canary (a managed-detection-and-response firm) and SPLX (an AI-application red-teaming vendor) for $692M combined slots into this strategy. Third, broaden the customer base — international markets, the U.S. federal and state-local-education vertical, and the mid-market through channel partners (the 2026 Google Cloud Security Partner of the Year award helps here). Management's stated 5-year aspiration is to roughly double annual recurring revenue from the current $3.4B toward $7B+, with non-GAAP operating margins expanding from ~22% today into the high 20s.

**What could go wrong (business risks).** Competition is intense and well-funded. Palo Alto Networks has built its own cloud-delivered "Prisma" stack and is bundling it aggressively with its firewall installed base; Cloudflare offers a similar zero-trust product at a lower price point and is winning mid-market and developer-led deployments; Microsoft bundles "Entra Internet Access" and "Entra Private Access" into the same Microsoft 365 E5 license that most large enterprises already pay for, which is the single largest distribution threat — the Chief Information Security Officer's incentive to use a product they already paid for is enormous. Net new annual recurring revenue growth has decelerated from 50%+ a few years ago to 19% in the most recent quarter, suggesting either market maturity or share loss. The company has historically run GAAP unprofitable on heavy stock-based compensation (roughly $700M+ per year), so dilution is material and reported earnings look much worse than non-GAAP earnings. Execution risk on the security-operations expansion is real — Splunk, CrowdStrike, and Palo Alto all have stronger incumbencies in the security operations center and Zscaler's brand is still associated with "network security" not "security analytics." Federal-government revenue is meaningful and could be hit by U.S. budget freezes or shutdowns. A breach of Zscaler itself — which would be catastrophic because customer traffic flows through their cloud — has not happened but cannot be ruled out.

**How to think about it.** Best-of-breed cloud-native zero-trust platform with a wide moat in its core secure-web-gateway and zero-trust-network-access market, transitioning from a single-product story to a multi-product platform play with optionality in security operations and AI security, but valuation is rich and decelerating net new annual recurring revenue means the next leg of the growth story has to come from new products (AI Protect, Avalor-powered security operations) rather than core seat expansion.

## Situation Summary

Zscaler reported strong Q2 fiscal 2026 results on February 26, 2026: revenue $815.8M (+26% year-over-year), annual recurring revenue $3.36B (+25% year-over-year), non-GAAP earnings per share $1.01 (beat by ~13%), and management raised FY26 annual recurring revenue guidance to 24% growth. The stock initially fell 12% on the print on concerns about GAAP losses and rich multiples, then declined further into April. From April 23 to May 18, 2026 the stock rallied ~30% from ~$133 to ~$175 on: (1) a B. Riley upgrade from Neutral to Buy citing AI-driven secure-access demand; (2) KeyBanc raising its price target to $190 from $160 on positive reseller channel checks; (3) Google Cloud naming Zscaler 2026 Partner of the Year for Security; and (4) general AI-cybersecurity sector rotation. The next major event is Q3 fiscal 2026 earnings on May 26, 2026 — six days away. Management's framing is that Zscaler is "the cybersecurity platform for the AI age" with new product traction in AI Protect, the Avalor data fabric for security operations, and three 2026 tuck-in acquisitions (Red Canary, SPLX, SquareX) extending into managed detection, AI red-teaming, and browser security.

## Variant Perception

- **Consensus view:** The Street is broadly constructive — 45 analyst opinions, Buy consensus, mean target $224 (range $155-$330), recent consensus upgrades 44-to-zero. Bulls believe the AI security narrative re-accelerates net new annual recurring revenue from the current 19% growth back toward 25%+ as customers adopt AI Protect, the Avalor-powered Security Operations Center play unlocks a new $30B+ total addressable market, and operating margins expand into the high 20s. Bears worry about Microsoft Entra bundling, Cloudflare share gains in the mid-market, and a $28B market cap on a still-GAAP-unprofitable business at ~9× revenue.
- **Our view:** Near-term skewed against fresh buyers, structurally favorable long-term. The stock has rallied 30% in three weeks directly into a Q3 earnings print six days away — this is the worst possible setup risk-reward. Q2 to Q3 sequential net new annual recurring revenue typically softens (Q2 is the seasonally strongest quarter), and the bar after the price target raises and B. Riley upgrade is high. Longer-term the platform-expansion thesis is real — AI Protect monetization is early-innings, the Avalor data fabric meaningfully extends total addressable market into security operations, and the Microsoft-Entra threat is overstated for large enterprises (where Chief Information Security Officers want a security-specialist vendor, not "the company that also runs my email"). But you do not need to buy at $175 six days before earnings to express that thesis.
- **Trigger:** Q3 fiscal 2026 earnings on May 26, 2026. A net new annual recurring revenue beat with raised FY26 guidance re-rates the stock toward $210-$220; an in-line print with the stock already +30% in three weeks likely gives back 10-15%; a miss or guidance hold (not raise) takes it to $140-$150.

## Financial Snapshot

| Metric | Value (FY25 ended Jul 2025) | 3yr Trend |
|--------|-----------------------------|-----------|
| Revenue | $2.67B | +35% CAGR (FY22 $1.09B → FY25 $2.67B) |
| Annual Recurring Revenue (Q2 FY26) | $3.36B | +25% year-over-year |
| Net Income (GAAP) | -$41M | Improving (FY22 -$390M → FY25 -$41M) |
| Operating Cash Flow | $972M | +44% CAGR |
| Free Cash Flow | $727M | +47% CAGR |
| Gross Margin (non-GAAP) | ~80% | Stable |
| Non-GAAP Operating Margin | 22% (Q2 FY26) | Expanding |
| Net Debt | -$0.7B (net cash) | Stable |
| FCF Yield (trailing/market cap) | ~2.6% | |
| Forward Price/Earnings | ~38× | |
| Price/Sales (trailing) | 9.4× | |

Revenue compounded at ~35% over three years while free cash flow compounded faster at ~47%, evidence of real operating leverage. Net cash balance sheet (~$2.4B cash vs ~$1.7B debt, mostly convertibles). Persistent GAAP losses are stock-based compensation driven (~$700M+/year, meaningful dilution) — non-GAAP picture is solidly profitable.

## Valuation Models

| Model | Fair Value | Upside vs $175.25 | Confidence | Run Date | Model's Price |
|-------|-----------|-------------------|------------|----------|---------------|
| gbm_opportunistic_1y | $227.67 | +29.9% | 0.89 | 2026-05-18 | $134.11 |
| gbm_lite_3y | $217.17 | +23.9% | 0.68 | 2026-05-18 | $134.11 |
| gbm_opportunistic_3y | $187.40 | +6.9% | 0.78 | 2026-05-18 | $134.11 |
| autoresearch | $179.64 | +2.5% | 0.90 | 2026-05-18 | $134.11 |
| gbm_3y | $155.04 | -11.5% | 0.60 | 2026-05-18 | $134.11 |
| gbm_lite_1y | $154.81 | -11.7% | 0.88 | 2026-05-18 | $134.11 |
| gbm_1y | $153.90 | -12.2% | 0.93 | 2026-05-18 | $134.11 |
| dcf_enhanced | $142.61 | -18.6% | 0.70 | 2026-05-18 | $134.11 |
| dcf | $86.00 | -50.9% | 0.70 | 2026-05-18 | $134.11 |
| simple_ratios | $77.71 | -55.7% | 0.70 | 2026-05-18 | $134.11 |
| multi_stage_dcf | $57.38 | -67.3% | 0.70 | 2026-05-18 | $134.11 |
| Analyst mean | $224.27 | +28.0% | — | live | $175.25 |

*All model `current_price` is $134.11 from May 18; live is $175.25 (+30%). Upside vs live is recalculated above. Note ZS rallied 30% in two trading days after model runs.*

**Model consensus:** Bimodal. GBM-opportunistic models (which weight upside skew) and analyst consensus see $215-$228 fair value (+23-30%). Mid-tier GBM and autoresearch see ~$155-$180 (around current price, no edge). Traditional value models (DCF, simple-ratios, multi-stage-DCF) see $57-$86 (-55% to -67%), reflecting their structural bias against high-multiple, GAAP-unprofitable software with heavy stock-based compensation. After the 30% three-week rally, almost no model sees meaningful upside from $175 — only the opportunistic-1y model and analyst consensus, both of which were calibrated before the rally.

## Business Quality (19/25)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Moat | 4/5 | High switching costs (multi-year network re-architecture to rip out), 150+ data center footprint is capex-heavy to replicate, 9000+ enterprise customers with 728 paying >$1M each. Threat: Microsoft Entra bundling. |
| Management | 4/5 | Founder-CEO Jay Chaudhry (35% insider ownership — large skin in the game), strong forecasting track record, transparent guidance. Aggressive 2026 M&A (3 deals) raises integration-execution risk. |
| Profitability | 4/5 | ~80% gross margin, 22% non-GAAP operating margin expanding, ~21% free cash flow margin. GAAP unprofitable on stock-based compensation — real dilution cost. |
| Balance Sheet | 4/5 | Net cash position (~$2.4B cash vs ~$1.7B debt, mostly convertibles), current ratio 1.9, no near-term liquidity risk. |
| Growth | 3/5 | Revenue +26% Q2, annual recurring revenue +25%, but net new annual recurring revenue growth has decelerated from 50%+ historically to 19%. New product traction (AI Protect, Avalor) needed to re-accelerate. |

## Inflection Point

**Mixed.** The positive inflection is product-portfolio expansion — Zscaler is transitioning from a single-product secure-web-gateway company to a multi-product platform with AI Protect, Avalor-powered Security Operations Center, and managed detection (Red Canary) all early-innings on monetization. If these gain traction, the deceleration in net new annual recurring revenue reverses and re-rating is justified. The negative is that the inflection has not yet shown up in the headline net-new-ARR number, and the next observable evidence point is Q3 on May 26. Best practice per the timing principle ("don't try to buy bottoms — wait for observable evidence the inflection has begun") says wait for the Q3 print to confirm or deny.

## Bull Case

- AI Protect attaches to a meaningful share of installed base over the next 4 quarters, lifting net new annual recurring revenue back toward 25%+ growth.
- Avalor-powered Security Operations Center product gains real traction, expanding total addressable market by $30B+ and competitive positioning versus Splunk, CrowdStrike, and Palo Alto Networks.
- Q3 fiscal 2026 print (May 26) beats and raises FY26 annual recurring revenue guidance again, validating the re-acceleration narrative.
- Free cash flow margins expand from 21% toward 25-27% on operating leverage; free cash flow compounds ~25%+ annually for 3+ years.
- Sector rotation into cybersecurity continues; ZS captures premium multiple as "the AI-age cybersecurity platform."

## Bear Case

- Stock has rallied 30% in three weeks directly into Q3 print — setup risk is severe; an in-line quarter likely gives back 10-15%.
- Net new annual recurring revenue growth has structurally decelerated (from 50%+ to 19%); core market may be approaching maturity faster than bulls think.
- **Microsoft Entra Internet Access / Entra Private Access bundling into E5 licenses applies persistent pricing pressure on renewals — under-discussed by the sell-side narrative.** Management has not directly quantified this in disclosures but it is the most credible long-term distribution threat and the bundle pricing structurally favors Microsoft.
- Cloudflare and Palo Alto Networks compete aggressively in mid-market and the firewall-replacement category respectively.
- Three 2026 acquisitions (Red Canary, SPLX, SquareX, plus Avalor previously) — integration and culture risk is real for a company that historically grew organically; could distract from core execution. Management disclosed acquired-deal consideration of $692M but the operational drag on margins is a near-term watch item.
- Stock-based compensation dilution (~$700M+/year on a $28B market cap ≈ ~2.5%/year ongoing dilution) is a real cost not reflected in non-GAAP earnings per share.

## Scenario Table

| Scenario | Prob | Earnings Driver | Multiple Driver | Target | Return |
|----------|------|----------------|-----------------|--------|--------|
| Bull | 30% | Q3 beats + raises guidance; AI Protect/Avalor inflect; FY27 annual recurring revenue growth 22-24% | Re-rating to 11× sales on platform-story validation | $230 | +31% |
| Base | 45% | Q3 in-line, FY26 guide unchanged or modest raise; core annual recurring revenue growth 22% | Multiple normalizes to 9× sales as growth modestly decelerates | $172 | -2% |
| Bear | 25% | Q3 net new annual recurring revenue softens; Microsoft Entra impact visible; FY27 annual recurring revenue growth slows to 18% | De-rating to 7× sales | $135 | -23% |

**Expected value: +3.6%** (0.30 × 31 + 0.45 × -2 + 0.25 × -23)

**Thesis breaks if:** Q3 fiscal 2026 (May 26) shows net new annual recurring revenue decelerating below $130M (versus $156M in Q2) without a credible management explanation, or FY26 annual recurring revenue guidance is held rather than raised. Either signals the AI-driven re-acceleration narrative is wrong and the stock likely retraces to $140-$150.

## Setup & Timing

| Factor | Status |
|--------|--------|
| Crowdedness | Moderately crowded — 58% institutional ownership, 45 analyst coverage, broadly Buy-rated, recently upgraded. Not contrarian. |
| Short interest | 9.8% of float — elevated but not extreme; squeeze-fuel into a beat. |
| Technical position | Overbought — +30% in three weeks; still ~48% below 52-week high of $337 but trading well above recent 50-day moving average. |
| Next catalyst | Q3 fiscal 2026 earnings — May 26, 2026 (6 days out). |
| Recent price action | Has run hard into the catalyst — classic "buy the rumor" setup that often sells the news even on a beat. |

**Verdict on setup:** Unfavorable for new buyers. The thesis (longer-term platform expansion is real) does not require buying at $175 with earnings in six days. Better to wait for the print and react.

## Verdict

**WATCH** — Conviction: MEDIUM

Zscaler is a high-quality cloud-native security platform with a real moat in zero-trust network access and credible optionality in AI security and security operations, but the +30% three-week rally directly into a May 26 earnings print has compressed the risk-reward. Analyst consensus and the bull-skewed models see $215-$230 fair value (+23-30%), but base-case scenario analysis at the current $175 entry gives an expected value of only +3.6% with a real 25% probability of a -23% drawdown if Q3 disappoints. Long-term thesis intact; near-term setup is the worst possible time to initiate a new position.

**If WATCH:**
- **Would upgrade to BUY** on a post-Q3 pullback to $145-$155 (where models cluster and the scenario expected value moves to +15-20%), or on a Q3 beat that raises FY26 annual recurring revenue guidance above $3.75B and net new annual recurring revenue accelerates back above $160M (which would justify entry even at slightly higher prices on a re-rated platform story).
- **Would downgrade to PASS** if Q3 shows net new annual recurring revenue below $130M without a clear explanation, or if Microsoft Entra-driven renewal pricing pressure shows up in commentary.
- Existing holders with cost basis well below $175 can hold through the print; trimming 20-30% into the rally is reasonable risk management given the setup.

<!-- Public file — generic research only. Personal position context belongs in ~/vault/finance/notes/positions/ZS.md per the public-vs-private rule. -->
