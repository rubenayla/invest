#!/usr/bin/env python3
"""
Polymarket prediction market lookup.

Fetches prediction market probabilities from Polymarket's public API.
Useful for anchoring scenario probabilities in thesis evaluation.

Usage:
    uv run python scripts/polymarket_lookup.py "tariff"
    uv run python scripts/polymarket_lookup.py "fed rate" --min-liquidity 50000
    uv run python scripts/polymarket_lookup.py "bitcoin" --limit 20
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GAMMA_API = "https://gamma-api.polymarket.com"
POLYMARKET_URL = "https://polymarket.com/event"
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "invest-polymarket-lookup/1.0",
}


def _fetch_json(url: str) -> list | dict:
    """Fetch JSON from a URL, returning empty list on error."""
    req = Request(url, headers=_HEADERS)
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return []


def search_markets(
    query: str,
    *,
    limit: int = 10,
    min_liquidity: float = 0,
    active_only: bool = True,
) -> list[dict]:
    """Search Polymarket for markets matching a query string.

    Uses the gamma API to fetch active markets, then filters client-side
    by keyword since the API lacks native text search.
    """
    base_params: dict = {
        "limit": 100,
        "order": "volume",
        "ascending": "false",
        "active": str(active_only).lower(),
        "closed": "false",
    }
    if min_liquidity > 0:
        base_params["liquidity_num_min"] = str(int(min_liquidity))

    # Fetch multiple pages of markets (API caps at ~100 per page)
    all_markets: list[dict] = []
    max_pages = 5
    for page in range(max_pages):
        params = {**base_params, "offset": str(page * 100)}
        url = f"{GAMMA_API}/markets?{urlencode(params)}"
        batch = _fetch_json(url)
        if not isinstance(batch, list) or not batch:
            break
        all_markets.extend(batch)

    # Also search events (groups of related markets, better coverage)
    events_url = f"{GAMMA_API}/events?limit=50&active=true&closed=false&order=volume&ascending=false"
    events = _fetch_json(events_url)
    if isinstance(events, list):
        for event in events:
            for market in event.get("markets", []):
                if market.get("active") and not market.get("closed"):
                    all_markets.append(market)

    # Client-side keyword filter (case-insensitive)
    keywords = query.lower().split()
    results = []
    seen_questions: set[str] = set()
    for market in all_markets:
        question = (market.get("question") or "").lower()
        description = (market.get("description") or "").lower()
        text = f"{question} {description}"
        if all(kw in text for kw in keywords) and question not in seen_questions:
            seen_questions.add(question)
            results.append(_format_market(market))

    # Sort by volume descending
    results.sort(key=lambda m: m["volume_usd"], reverse=True)
    return results[:limit]


def _format_market(raw: dict) -> dict:
    """Extract the useful fields from a raw market object."""
    outcomes = raw.get("outcomes") or ["Yes", "No"]
    prices_raw = raw.get("outcomePrices") or []

    # Both outcomes and outcomePrices may arrive as JSON strings
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except (json.JSONDecodeError, TypeError):
            outcomes = ["Yes", "No"]

    if isinstance(prices_raw, str):
        try:
            prices_raw = json.loads(prices_raw)
        except (json.JSONDecodeError, TypeError):
            prices_raw = []

    prices = []
    for p in prices_raw:
        try:
            prices.append(float(p))
        except (ValueError, TypeError):
            prices.append(0.0)

    # Build outcome dict
    outcome_probs = {}
    for i, outcome in enumerate(outcomes):
        prob = prices[i] if i < len(prices) else 0.0
        outcome_probs[outcome] = round(prob * 100, 1)

    volume = 0.0
    try:
        volume = float(raw.get("volume") or 0)
    except (ValueError, TypeError):
        pass

    liquidity = 0.0
    try:
        liquidity = float(raw.get("liquidity") or 0)
    except (ValueError, TypeError):
        pass

    slug = raw.get("slug") or ""

    return {
        "question": raw.get("question", ""),
        "probabilities": outcome_probs,
        "volume_usd": round(volume, 2),
        "liquidity_usd": round(liquidity, 2),
        "end_date": raw.get("endDate", ""),
        "url": f"https://polymarket.com/event/{slug}" if slug else "",
    }


def print_results(results: list[dict], query: str) -> None:
    """Pretty-print market results to stdout."""
    if not results:
        print(f"No active markets found for '{query}'")
        return

    print(f"\n{'='*70}")
    print(f"  Polymarket: '{query}' — {len(results)} market(s) found")
    print(f"{'='*70}\n")

    for i, m in enumerate(results, 1):
        print(f"  {i}. {m['question']}")

        # Show probabilities
        probs_str = " | ".join(f"{k}: {v}%" for k, v in m["probabilities"].items())
        print(f"     {probs_str}")

        # Volume and liquidity
        vol = m["volume_usd"]
        liq = m["liquidity_usd"]
        vol_str = f"${vol/1e6:.1f}M" if vol >= 1e6 else f"${vol/1e3:.0f}K" if vol >= 1e3 else f"${vol:.0f}"
        liq_str = f"${liq/1e6:.1f}M" if liq >= 1e6 else f"${liq/1e3:.0f}K" if liq >= 1e3 else f"${liq:.0f}"
        print(f"     Volume: {vol_str}  |  Liquidity: {liq_str}")

        if m["end_date"]:
            print(f"     Resolves: {m['end_date'][:10]}")
        if m["url"]:
            print(f"     {m['url']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Polymarket prediction markets")
    parser.add_argument("query", help="Keywords to search for (e.g. 'tariff', 'fed rate')")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--min-liquidity", type=float, default=0, help="Min liquidity in USD")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    results = search_markets(args.query, limit=args.limit, min_liquidity=args.min_liquidity)

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    else:
        print_results(results, args.query)


if __name__ == "__main__":
    main()
