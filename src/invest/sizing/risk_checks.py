"""Risk checks for position sizing: VaR, exposure limits, sector caps."""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass, field

from invest.data.stock_data_reader import StockDataReader


@dataclass
class RiskReport:
    ticker: str
    var_95_annual: float  # annualized VaR at 95% confidence
    volatility_annual: float
    max_drawdown_1y: float
    sector: str
    sector_exposure_after: float  # % of portfolio in this sector after trade
    position_exposure_after: float  # % of portfolio in this ticker after trade
    flags: list[str] = field(default_factory=list)


class RiskChecker:
    """Validates proposed trades against risk limits."""

    def __init__(self, reader: StockDataReader, conn: sqlite3.Connection):
        self.reader = reader
        self.conn = conn

    def check(
        self,
        ticker: str,
        proposed_amount: float,
        portfolio_value: float,
        current_holdings: dict[str, float],
        max_sector_pct: float = 0.35,
    ) -> RiskReport:
        """Run all risk checks on a proposed trade."""
        prices = self.reader.get_recent_price_closes(ticker, limit=600)
        closes = prices.get("closes", [])

        vol = self._compute_annual_volatility(closes)
        var_95 = self._compute_var_95(closes)
        mdd = self._compute_max_drawdown(closes)
        sector = self._get_sector(ticker)

        # Position exposure
        existing = current_holdings.get(ticker, 0.0)
        position_after = (existing + proposed_amount) / portfolio_value if portfolio_value > 0 else 0

        # Sector exposure
        sector_total = sum(
            v for t, v in current_holdings.items() if self._get_sector(t) == sector
        )
        sector_after = (sector_total + proposed_amount) / portfolio_value if portfolio_value > 0 else 0

        flags: list[str] = []

        if vol > 0.50:
            flags.append("high_volatility")
        if mdd > 0.40:
            flags.append("severe_drawdown_history")
        if sector_after > max_sector_pct:
            flags.append(f"BLOCK: sector {sector} at {sector_after:.0%} exceeds {max_sector_pct:.0%}")

        return RiskReport(
            ticker=ticker,
            var_95_annual=var_95,
            volatility_annual=vol,
            max_drawdown_1y=mdd,
            sector=sector,
            sector_exposure_after=sector_after,
            position_exposure_after=position_after,
            flags=flags,
        )

    def _compute_annual_volatility(self, closes: list[float]) -> float:
        if len(closes) < 20:
            return 0.30  # default

        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
            if closes[i - 1] > 0
        ]
        if not returns:
            return 0.30

        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        daily_vol = math.sqrt(variance)
        return daily_vol * math.sqrt(252)

    def _compute_var_95(self, closes: list[float]) -> float:
        if len(closes) < 60:
            return 0.20

        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
            if closes[i - 1] > 0
        ]
        if not returns:
            return 0.20

        returns.sort()
        idx = max(0, int(len(returns) * 0.05))
        daily_var = abs(returns[idx])
        return daily_var * math.sqrt(252)

    def _compute_max_drawdown(self, closes: list[float]) -> float:
        """Max drawdown over the given price series."""
        if len(closes) < 2:
            return 0.0

        peak = closes[0]
        max_dd = 0.0
        for price in closes[1:]:
            if price > peak:
                peak = price
            dd = (peak - price) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        return max_dd

    def _get_sector(self, ticker: str) -> str:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT sector FROM current_stock_data WHERE ticker = %s",
            (ticker,),
        )
        row = cur.fetchone()
        return row[0] if row and row[0] else "Unknown"
