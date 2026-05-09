"""
Signal gate registry — measured-alpha metadata per trade-signal source.

The /feed dashboard shows two card categories:
  - NARRATIVE cards (intro, thesis, bull/bear, numbers, verdict) — sourced
    from the user's own notes/companies/*.md analyses. NOT gated here.
  - TRADE-SIGNAL cards (Congress signal, Insider signal) — derived from
    external data, with implicit alpha claims. Gated by this module.

Default policy is DROP UNBACKTESTED. A signal source has to clear the
alpha bar (entry in SIGNAL_GATES with passes=True) before it surfaces.
Surviving signals carry an inline alpha + caveat annotation on the card.

The accompanying human-readable ledger lives at
notes/research/signal_inventory.md — keep it in sync with this dict so we
remember what's curated vs not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class GateResult:
    """One row of measured-alpha metadata for a trade-signal source."""

    passes: bool
    alpha: float            # annualised, signed (e.g. 0.142 for +14.2%)
    horizon: str            # the horizon the alpha was measured at, e.g. "365d"
    p_value: float          # two-sided t-test p-value vs control
    n_nominal: int          # raw observation count
    n_effective: int        # post-clustering / independence-adjusted n
    caveat: str             # one-line caveat shown inline on the card
    last_backtested_at: str # ISO date the metadata was last refreshed


# Tuple key shape: (source, name, kind).
# - source: signal family ("politician", future: "insider", "activist", ...)
# - name:   politician full-name as stored in politician_trades.politician_name,
#           or a regime label for non-per-name signals.
# - kind:   transaction direction for politicians ('P'/'S'), or None.
SIGNAL_GATES: Dict[Tuple[str, str, Optional[str]], GateResult] = {
    # See notes/research/politician_backtest_2026.md for derivation.
    # Tuberville sells: +14.2% annualised alpha at 365d, hit rate 75.5%,
    # p<0.001 vs House control. Trade clustering reduces effective n
    # from 216 to ~20, so headline t-stat is optimistic.
    ('politician', 'Tuberville, Tommy', 'S'): GateResult(
        passes=True,
        alpha=0.142,
        horizon='365d',
        p_value=0.001,
        n_nominal=216,
        n_effective=20,
        caveat='trade clustering reduces effective n',
        last_backtested_at='2026-04-30',
    ),
    # Tuberville buys: -9.2% annualised alpha at 365d, but the
    # statistically robust window is 180d (n=118, p=0.003, alpha -13.3%).
    # Reported here at 180d horizon. Faded, not amplified.
    ('politician', 'Tuberville, Tommy', 'P'): GateResult(
        passes=False,
        alpha=-0.133,
        horizon='180d',
        p_value=0.003,
        n_nominal=118,
        n_effective=10,
        caveat='underperforms SPY post-disclosure',
        last_backtested_at='2026-04-30',
    ),
    # See notes/research/pelosi_backtest_2026.md for derivation.
    # Pelosi buys: +13.7% annualised alpha at 365d, hit rate 62.5%
    # (cluster level 75%), p=0.004 vs House control. n_nominal=16 is
    # small; cluster count 12. Survives leave-2-out robustness check
    # but heavily exposed to bull-market regime (megacap-tech
    # concentration). Provisional pass; revisit in 12mo.
    ('politician', 'Pelosi, Nancy', 'P'): GateResult(
        passes=True,
        alpha=0.137,
        horizon='365d',
        p_value=0.004,
        n_nominal=16,
        n_effective=12,
        caveat='small sample; bull-market regime; megacap-tech concentration',
        last_backtested_at='2026-05-10',
    ),
    # Pelosi sells: -18.9% annualised alpha at 365d, p=0.023, hit
    # rate 22% (cluster 12%). Significant underperformance — she
    # sells names that subsequently beat SPY. Faded, not amplified.
    ('politician', 'Pelosi, Nancy', 'S'): GateResult(
        passes=False,
        alpha=-0.189,
        horizon='365d',
        p_value=0.023,
        n_nominal=9,
        n_effective=8,
        caveat='underperforms SPY post-disclosure (significantly negative)',
        last_backtested_at='2026-05-10',
    ),
    # Other politicians and signal sources: no entry here -> evaluate()
    # returns None -> the gate filter drops the post.
}


def evaluate(
    source: str,
    name: str,
    kind: Optional[str] = None,
) -> Optional[GateResult]:
    """Look up gate metadata for a trade signal.

    Returns the GateResult if the (source, name, kind) tuple has a
    curated entry, else None. Callers should treat None as "drop" under
    the default strict-gate policy.
    """
    return SIGNAL_GATES.get((source, name, kind))


def apply_signal_gates(posts):
    """Filter trade-signal posts by the gate registry.

    Posts with type='signal' must carry signal_source / signal_name /
    signal_kind keys. The gate is looked up; passing posts get the
    GateResult attached as post['gate'] for inline rendering. Failing or
    ungated posts are dropped.

    Posts of any other type (intro, thesis, bull, bear, numbers, verdict)
    pass through untouched — the gate is for external alpha claims, not
    for the user's own narrative analyses.
    """
    out = []
    for post in posts:
        if post.get("type") != "signal":
            out.append(post)
            continue
        result = evaluate(
            post.get("signal_source", ""),
            post.get("signal_name", ""),
            post.get("signal_kind"),
        )
        if result is None or not result.passes:
            continue
        post = dict(post)
        post["gate"] = result
        out.append(post)
    return out
