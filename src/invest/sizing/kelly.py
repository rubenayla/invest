"""Kelly Criterion position sizing using existing model consensus."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from invest.config.constants import CONSENSUS_CONFIG
from invest.data.stock_data_reader import StockDataReader
from invest.valuation.consensus import compute_consensus_from_dicts
from invest.valuation.db_utils import get_db_connection, get_latest_predictions

from .risk_checks import RiskChecker, RiskReport


@dataclass
class KellyResult:
    ticker: str
    current_price: float
    consensus_fair_value: float
    consensus_margin: float  # ratio: (fv - price) / price
    win_probability: float  # p
    win_loss_ratio: float  # b = upside / downside
    kelly_fraction: float  # raw f*
    adjusted_fraction: float  # after half-kelly + caps
    dollar_amount: float
    shares_to_buy: int
    model_agreement: dict[str, str] = field(default_factory=dict)  # model -> bull/bear
    risk: RiskReport | None = None
    flags: list[str] = field(default_factory=list)

    @property
    def edge(self) -> float:
        """p * b - q. Positive = trade has edge."""
        return self.win_probability * self.win_loss_ratio - (1 - self.win_probability)

    def summary_line(self) -> str:
        flag_str = ", ".join(self.flags) if self.flags else "ok"
        return (
            f"{self.ticker:<6} | ${self.consensus_fair_value:>8.2f} | "
            f"{self.consensus_margin:>+7.1%} | {self.win_probability:.2f} | "
            f"{self.win_loss_ratio:.2f} | {self.kelly_fraction:>6.1%} | "
            f"{self.adjusted_fraction:>6.1%} | {self.shares_to_buy:>6} | "
            f"${self.dollar_amount:>9,.0f} | {flag_str}"
        )


HEADER = (
    f"{'TICKER':<6} | {'Fair Val':>9} | {'Upside':>7} | {'p':>4} | "
    f"{'b':>4} | {'Kelly':>6} | {'Half-K':>6} | {'Shares':>6} | "
    f"{'$Amount':>10} | Flags"
)
SEPARATOR = "-" * len(HEADER)


class KellyPositionSizer:
    """Compute position sizes using Kelly Criterion on existing model outputs."""

    def __init__(
        self,
        portfolio_value: float,
        fraction: float = 0.5,
        max_position_pct: float = 0.15,
        max_sector_pct: float = 0.35,
        db_path: Path | None = None,
        current_holdings: dict[str, float] | None = None,
        use_calibration: bool = True,
    ):
        self.portfolio_value = portfolio_value
        self.fraction = fraction
        self.max_position_pct = max_position_pct
        self.max_sector_pct = max_sector_pct
        self.conn = get_db_connection(db_path)
        self.reader = StockDataReader(db_path)
        self.risk_checker = RiskChecker(self.reader, self.conn)
        self.current_holdings = current_holdings or {}

        # Load calibration base rate to cap overconfident p estimates
        self._base_rate = 0.733  # default 1y base rate
        if use_calibration:
            try:
                from .calibration import ModelCalibrator

                cal = ModelCalibrator(db_path).calibrate("1y")
                if cal.total_snapshots > 100:
                    self._base_rate = cal.base_rate
            except Exception:
                pass  # fall back to default

    def size_position(self, ticker: str) -> KellyResult:
        """Compute Kelly-optimal position size for a single ticker."""
        predictions = get_latest_predictions(self.conn, ticker)
        if not predictions:
            return self._no_data_result(ticker, "no model predictions found")

        # Get current price from predictions or DB
        current_price = self._get_current_price(ticker, predictions)
        if not current_price or current_price <= 0:
            return self._no_data_result(ticker, "no valid price")

        # Compute consensus
        consensus = compute_consensus_from_dicts(predictions, current_price)
        if consensus is None:
            return self._no_data_result(ticker, "consensus computation failed")

        # Model agreement breakdown
        model_agreement = self._compute_model_agreement(predictions, current_price)

        # Win probability from weighted model agreement
        p = self._compute_win_probability(predictions, current_price)

        # Win/loss ratio: upside from consensus, downside from historical VaR
        historical_downside = self._compute_historical_downside(ticker)

        if historical_downside <= 0:
            historical_downside = 0.15  # default 15% downside if no history

        # Cap consensus upside at 100% — anything beyond is likely model noise
        consensus_upside = max(min(consensus.margin_of_safety, 1.0), 0.0)
        b = consensus_upside / historical_downside if consensus_upside > 0 else 0.0

        # Kelly formula: f* = (p * b - q) / b
        q = 1 - p
        edge = p * b - q
        if edge <= 0:
            kelly_f = 0.0
        else:
            kelly_f = edge / b

        # Apply fractional Kelly
        adjusted_f = kelly_f * self.fraction

        # Apply hard caps
        adjusted_f = min(adjusted_f, self.max_position_pct)

        # Risk checks
        dollar_amount = adjusted_f * self.portfolio_value
        risk = self.risk_checker.check(
            ticker=ticker,
            proposed_amount=dollar_amount,
            portfolio_value=self.portfolio_value,
            current_holdings=self.current_holdings,
            max_sector_pct=self.max_sector_pct,
        )

        # Collect flags
        flags = list(risk.flags)
        if edge <= 0:
            flags.append("no_edge")
        elif edge < 0.04:
            flags.append("thin_edge")

        # If risk flags include hard blocks, reduce to zero
        if any(f.startswith("BLOCK:") for f in risk.flags):
            adjusted_f = 0.0
            dollar_amount = 0.0

        shares = int(dollar_amount / current_price) if current_price > 0 else 0
        dollar_amount = shares * current_price  # round to whole shares

        return KellyResult(
            ticker=ticker,
            current_price=current_price,
            consensus_fair_value=consensus.fair_value,
            consensus_margin=consensus.margin_of_safety,
            win_probability=p,
            win_loss_ratio=b,
            kelly_fraction=kelly_f,
            adjusted_fraction=adjusted_f,
            dollar_amount=dollar_amount,
            shares_to_buy=shares,
            model_agreement=model_agreement,
            risk=risk,
            flags=flags,
        )

    def size_multiple(self, tickers: list[str]) -> list[KellyResult]:
        """Size positions for multiple tickers."""
        return [self.size_position(t) for t in tickers]

    def build_portfolio(
        self,
        budget: float | None = None,
        tickers: list[str] | None = None,
        max_positions: int = 15,
        min_edge: float = 0.0,
    ) -> list[KellyResult]:
        """Propose a portfolio allocation from all stocks with edge.

        Scans all tickers in valuation_results (or a provided list), ranks
        by risk-adjusted Kelly score, enforces sector caps, and allocates
        budget proportionally.

        Args:
            budget: Amount to invest. Defaults to self.portfolio_value.
            tickers: Stocks to consider. None = all stocks in DB.
            max_positions: Maximum number of positions.
            min_edge: Minimum edge (p*b - q) to include.
        """
        budget = budget or self.portfolio_value

        # Get all tickers with model predictions
        if tickers is None:
            rows = self.conn.execute(
                "SELECT DISTINCT ticker FROM valuation_results"
            ).fetchall()
            tickers = [r[0] for r in rows]

        # Size each
        all_results = []
        for t in tickers:
            r = self.size_position(t)
            if r.edge > min_edge and r.kelly_fraction > 0:
                all_results.append(r)

        if not all_results:
            return []

        # Rank by risk-adjusted score: Kelly fraction penalized by risk flags
        def _score(r: KellyResult) -> float:
            score = r.kelly_fraction
            if "high_volatility" in r.flags:
                score *= 0.6
            if "severe_drawdown_history" in r.flags:
                score *= 0.7
            return score

        all_results.sort(key=_score, reverse=True)

        # Allocate with sector caps enforced
        allocated: list[KellyResult] = []
        remaining = budget
        sector_totals: dict[str, float] = {}
        sector_cap = self.max_sector_pct * budget

        for r in all_results:
            if len(allocated) >= max_positions or remaining <= 0:
                break

            sector = r.risk.sector if r.risk else "Unknown"

            # Check sector cap
            if sector_totals.get(sector, 0) >= sector_cap:
                continue

            # Compute allocation: proportional to score, capped
            score = _score(r)
            raw_amount = score * budget  # Kelly fraction * budget
            capped_amount = min(raw_amount, budget * self.max_position_pct)
            capped_amount = min(capped_amount, remaining)
            capped_amount = min(capped_amount, sector_cap - sector_totals.get(sector, 0))

            # Minimum position: at least 0.5% of budget and at least 1 share
            min_amount = budget * 0.005
            if r.current_price > 0 and capped_amount >= max(r.current_price, min_amount):
                shares = int(capped_amount / r.current_price)
                actual_amount = shares * r.current_price
            else:
                continue

            remaining -= actual_amount
            sector_totals[sector] = sector_totals.get(sector, 0) + actual_amount

            allocated.append(
                KellyResult(
                    ticker=r.ticker,
                    current_price=r.current_price,
                    consensus_fair_value=r.consensus_fair_value,
                    consensus_margin=r.consensus_margin,
                    win_probability=r.win_probability,
                    win_loss_ratio=r.win_loss_ratio,
                    kelly_fraction=r.kelly_fraction,
                    adjusted_fraction=actual_amount / budget if budget > 0 else 0,
                    dollar_amount=actual_amount,
                    shares_to_buy=shares,
                    model_agreement=r.model_agreement,
                    risk=r.risk,
                    flags=r.flags,
                )
            )

        return allocated

    def _get_current_price(self, ticker: str, predictions: dict) -> float | None:
        """Extract current price from predictions or DB."""
        for model_data in predictions.values():
            if isinstance(model_data, dict):
                price = model_data.get("current_price")
                if price and price > 0:
                    return price
        # Fallback to DB
        row = self.conn.execute(
            "SELECT current_price FROM current_stock_data WHERE ticker = ?",
            (ticker,),
        ).fetchone()
        return row[0] if row else None

    def _compute_model_agreement(
        self, predictions: dict, current_price: float
    ) -> dict[str, str]:
        """Classify each model as bullish or bearish."""
        agreement = {}
        for model_name, data in predictions.items():
            if not isinstance(data, dict):
                continue
            fv = data.get("fair_value")
            if fv is not None and fv > 0:
                agreement[model_name] = "bull" if fv > current_price else "bear"
        return agreement

    def _compute_win_probability(
        self, predictions: dict, current_price: float
    ) -> float:
        """Weighted fraction of models predicting upside."""
        weights = CONSENSUS_CONFIG.MODEL_WEIGHTS
        default_w = CONSENSUS_CONFIG.DEFAULT_MODEL_WEIGHT

        total_weight = 0.0
        bullish_weight = 0.0

        for model_name, data in predictions.items():
            if not isinstance(data, dict):
                continue
            fv = data.get("fair_value")
            if fv is None or fv <= 0:
                continue

            w = weights.get(model_name, default_w)

            # Boost weight by model confidence if available
            conf = data.get("confidence")
            if conf is not None:
                try:
                    conf_f = float(conf)
                    if 0 < conf_f <= 1:
                        w *= conf_f
                except (ValueError, TypeError):
                    pass  # string confidence like 'high' — ignore

            total_weight += w
            if fv > current_price:
                bullish_weight += w

        if total_weight == 0:
            return 0.5  # no signal

        raw_p = bullish_weight / total_weight

        # Calibration: blend with historical base rate to prevent overconfidence.
        # If all models agree (raw_p=1.0), we still cap at slightly above base rate.
        # Formula: p = base_rate + (raw_p - 0.5) * scaling
        # This anchors to the base rate and adjusts by model signal strength.
        max_p = min(0.95, self._base_rate + 0.15)  # can't exceed base rate + 15%
        return max(0.1, min(max_p, raw_p))

    def _compute_historical_downside(self, ticker: str) -> float:
        """Compute 1-year downside as VaR(5%) from price history."""
        prices = self.reader.get_recent_price_closes(ticker, limit=600)
        closes = prices.get("closes", [])

        if len(closes) < 60:
            return 0.20  # default 20% if insufficient history

        # Daily returns
        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
            if closes[i - 1] > 0
        ]

        if not returns:
            return 0.20

        # Sort returns, take 5th percentile
        returns.sort()
        idx_5pct = max(0, int(len(returns) * 0.05))
        daily_var_5 = abs(returns[idx_5pct])

        # Annualize: daily VaR * sqrt(252)
        annual_var = daily_var_5 * math.sqrt(252)

        # Clamp to reasonable range [5%, 80%]
        return max(0.05, min(0.80, annual_var))

    def _no_data_result(self, ticker: str, reason: str) -> KellyResult:
        return KellyResult(
            ticker=ticker,
            current_price=0,
            consensus_fair_value=0,
            consensus_margin=0,
            win_probability=0.5,
            win_loss_ratio=0,
            kelly_fraction=0,
            adjusted_fraction=0,
            dollar_amount=0,
            shares_to_buy=0,
            flags=[f"skip: {reason}"],
        )
