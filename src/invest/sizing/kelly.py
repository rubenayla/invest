"""Kelly Criterion position sizing using trusted prediction models.

Uses GBM models (standard, lite, opportunistic) at the 3-year horizon plus
the autoresearch model. These predict actual expected returns, unlike DCF/RIM
which estimate theoretical fair values. Agreement among models drives win
probability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from invest.data.stock_data_reader import StockDataReader
from invest.valuation.db_utils import get_db_connection

from .risk_checks import RiskChecker, RiskReport

# Trusted models for Kelly sizing.
# gbm_3y: actual hold-to-horizon return (median +12%, 77% bullish — well calibrated)
# gbm_lite_3y: limited-history variant (median +53%, 100% bullish — overoptimistic)
# gbm_opportunistic_3y: peak return within window (median +18%, 82% bullish)
# autoresearch: LLM-driven fair value model (~700 stocks, high confidence, well calibrated)
# Use all 4 as committee for agreement signal, but weight gbm_3y as primary.
_TRUSTED_MODELS = ("gbm_3y", "gbm_lite_3y", "gbm_opportunistic_3y", "autoresearch")

# Dual-class share mappings: skip the less liquid class.
_DUAL_CLASS_SKIP = {
    "FOXA": "FOX",
    "GOOGL": "GOOG",
    "NWSA": "NWS",
}


@dataclass
class KellyResult:
    ticker: str
    current_price: float
    expected_return: float  # median predicted return from GBM models
    win_probability: float  # p — fraction of models predicting positive return
    win_loss_ratio: float  # b = upside / downside
    kelly_fraction: float  # raw f*
    adjusted_fraction: float  # after half-kelly + caps
    dollar_amount: float
    shares_to_buy: int
    model_predictions: dict[str, float] = field(default_factory=dict)  # model -> predicted return
    risk: RiskReport | None = None
    flags: list[str] = field(default_factory=list)

    @property
    def edge(self) -> float:
        """p * b - q. Positive = trade has edge."""
        return self.win_probability * self.win_loss_ratio - (1 - self.win_probability)

    def summary_line(self) -> str:
        flag_str = ", ".join(self.flags) if self.flags else "ok"
        models_str = f"{sum(1 for r in self.model_predictions.values() if r > 0)}/{len(self.model_predictions)}"
        return (
            f"{self.ticker:<8} | {self.expected_return:>+7.1%} | "
            f"{self.win_probability:.2f} | {self.win_loss_ratio:>5.2f} | "
            f"{self.kelly_fraction:>6.1%} | {self.adjusted_fraction:>6.1%} | "
            f"{self.shares_to_buy:>6} | ${self.dollar_amount:>9,.0f} | "
            f"{models_str:>5} | {flag_str}"
        )


HEADER = (
    f"{'TICKER':<8} | {'Return':>7} | {'p':>4} | {'b':>5} | "
    f"{'Kelly':>6} | {'Adj-K':>6} | {'Shares':>6} | "
    f"{'$Amount':>10} | {'Bulls':>5} | Flags"
)
SEPARATOR = "-" * len(HEADER)


class KellyPositionSizer:
    """Compute position sizes using Kelly Criterion on GBM 3y predictions."""

    def __init__(
        self,
        portfolio_value: float,
        fraction: float = 0.5,
        max_position_pct: float = 0.15,
        max_sector_pct: float = 0.35,
        db_path: Path | None = None,
        current_holdings: dict[str, float] | None = None,
    ):
        self.portfolio_value = portfolio_value
        self.fraction = fraction
        self.max_position_pct = max_position_pct
        self.max_sector_pct = max_sector_pct
        self.conn = get_db_connection(db_path)
        self.reader = StockDataReader(db_path)
        self.risk_checker = RiskChecker(self.reader, self.conn)
        self.current_holdings = current_holdings or {}

    def size_position(self, ticker: str) -> KellyResult:
        """Compute Kelly-optimal position size for a single ticker."""
        # Get GBM 3y predictions only
        predictions = self._get_trusted_predictions(ticker)
        if not predictions:
            return self._no_data_result(ticker, "no trusted model predictions")

        current_price = self._get_current_price(ticker)
        if not current_price or current_price <= 0:
            return self._no_data_result(ticker, "no valid price")

        # Extract predicted returns from each model
        model_returns: dict[str, float] = {}
        for model_name, data in predictions.items():
            ret = data.get("margin_of_safety")  # this is the predicted return
            if ret is not None:
                model_returns[model_name] = ret

        if not model_returns:
            return self._no_data_result(ticker, "no valid return predictions")

        # Confidence-weighted expected return across trusted models.
        # Models with confidence scores get weighted by confidence;
        # GBM models without explicit confidence default to 0.80.
        _DEFAULT_CONFIDENCE = 0.80
        weighted_sum = 0.0
        weight_total = 0.0
        for model_name, ret in model_returns.items():
            conf = predictions.get(model_name, {}).get("confidence") or _DEFAULT_CONFIDENCE
            # Cap upside at 100% to prevent DCF-style outlier inflation
            capped_ret = min(ret, 1.0)
            weighted_sum += capped_ret * conf
            weight_total += conf
        expected_return = weighted_sum / weight_total if weight_total > 0 else 0.0

        # p from agreement: how many models agree on direction + confidence.
        # Base rate: 77% of stocks go up in gbm_3y.
        n_bullish = sum(1 for r in model_returns.values() if r > 0)
        n_models = len(model_returns)

        # Start from base rate, adjust by model agreement fraction
        base_rate = 0.77
        bull_frac = n_bullish / n_models
        if expected_return > 0:
            # Scale: all agree → +0.08, 75% → +0.02, 50% → -0.04, 25% → -0.10
            agreement_bonus = (bull_frac - 0.67) * 0.24
            p = max(0.1, min(0.88, base_rate + agreement_bonus))
        else:
            # Bearish: more bears = higher p of loss
            p = max(0.1, min(0.40, (1 - base_rate) + (bull_frac - 0.33) * 0.24))

        upside = max(expected_return, 0.0)

        # Historical downside from rolling 1-year returns
        historical_downside = self._compute_historical_downside(ticker)
        if historical_downside <= 0:
            historical_downside = 0.15

        # b = upside / downside
        b = upside / historical_downside if upside > 0 else 0.0

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
        if self._is_stale(ticker):
            flags.append("stale_data")
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
            expected_return=expected_return,
            win_probability=p,
            win_loss_ratio=b,
            kelly_fraction=kelly_f,
            adjusted_fraction=adjusted_f,
            dollar_amount=dollar_amount,
            shares_to_buy=shares,
            model_predictions=model_returns,
            risk=risk,
            flags=flags,
        )

    def build_portfolio(
        self,
        budget: float | None = None,
        tickers: list[str] | None = None,
        max_positions: int = 15,
        min_edge: float = 0.0,
    ) -> list[KellyResult]:
        """Propose a portfolio allocation from all stocks with edge.

        Scans all tickers with GBM 3y predictions, ranks by Kelly fraction,
        enforces sector caps, and allocates budget proportionally.
        """
        budget = budget or self.portfolio_value

        if tickers is None:
            placeholders = ",".join(["%s"] * len(_TRUSTED_MODELS))
            cur = self.conn.cursor()
            cur.execute(
                f"SELECT DISTINCT ticker FROM valuation_results WHERE model_name IN ({placeholders})",
                _TRUSTED_MODELS,
            )
            tickers = [r[0] for r in cur.fetchall()]

        # Remove dual-class duplicates
        tickers = [t for t in tickers if t not in _DUAL_CLASS_SKIP]

        # Size each
        all_results = []
        for t in tickers:
            r = self.size_position(t)
            if r.edge > min_edge and r.kelly_fraction > 0:
                all_results.append(r)

        if not all_results:
            return []

        # Rank by edge (p*b - q) — combines probability and magnitude
        all_results.sort(key=lambda r: r.edge, reverse=True)

        # Allocate with sector caps enforced
        allocated: list[KellyResult] = []
        remaining = budget
        sector_totals: dict[str, float] = {}
        sector_cap = self.max_sector_pct * budget

        for r in all_results:
            if len(allocated) >= max_positions or remaining <= 0:
                break

            sector = r.risk.sector if r.risk else "Unknown"

            if sector_totals.get(sector, 0) >= sector_cap:
                continue

            raw_amount = r.adjusted_fraction * budget
            capped_amount = min(raw_amount, budget * self.max_position_pct)
            capped_amount = min(capped_amount, remaining)
            capped_amount = min(capped_amount, sector_cap - sector_totals.get(sector, 0))

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
                    expected_return=r.expected_return,
                    win_probability=r.win_probability,
                    win_loss_ratio=r.win_loss_ratio,
                    kelly_fraction=r.kelly_fraction,
                    adjusted_fraction=actual_amount / budget if budget > 0 else 0,
                    dollar_amount=actual_amount,
                    shares_to_buy=shares,
                    model_predictions=r.model_predictions,
                    risk=r.risk,
                    flags=r.flags,
                )
            )

        return allocated

    def _get_trusted_predictions(self, ticker: str) -> dict[str, dict]:
        """Get trusted model predictions for a ticker."""
        placeholders = ",".join(["%s"] * len(_TRUSTED_MODELS))
        cur = self.conn.cursor()
        cur.execute(
            f"""SELECT model_name, fair_value, current_price, margin_of_safety, confidence
               FROM valuation_results
               WHERE ticker = %s AND model_name IN ({placeholders})""",
            (ticker, *_TRUSTED_MODELS),
        )
        rows = cur.fetchall()

        predictions = {}
        for model_name, fv, cp, mos, conf in rows:
            predictions[model_name] = {
                "fair_value": fv,
                "current_price": cp,
                "margin_of_safety": mos,
                "confidence": conf,
            }
        return predictions

    def _get_current_price(self, ticker: str) -> float | None:
        """Get current price from DB."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT current_price FROM current_stock_data WHERE ticker = %s",
            (ticker,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def _compute_historical_downside(self, ticker: str) -> float:
        """Compute downside using rolling 1-year returns.

        Uses 10th percentile of rolling 252-day returns — what a bad year
        actually looks like for a long-term holder.
        """
        prices = self.reader.get_recent_price_closes(ticker, limit=600)
        closes = prices.get("closes", [])

        if len(closes) < 300:
            if len(closes) < 60:
                return 0.20
            peak = closes[0]
            max_dd = 0.0
            for price in closes[1:]:
                if price > peak:
                    peak = price
                dd = (peak - price) / peak if peak > 0 else 0
                max_dd = max(max_dd, dd)
            return max(0.05, min(0.60, max_dd))

        period = 252
        rolling_returns = [
            (closes[i] - closes[i - period]) / closes[i - period]
            for i in range(period, len(closes))
            if closes[i - period] > 0
        ]

        if not rolling_returns:
            return 0.20

        rolling_returns.sort()
        idx_10pct = max(0, int(len(rolling_returns) * 0.10))
        bad_year_return = rolling_returns[idx_10pct]
        downside = abs(min(bad_year_return, 0))
        return max(0.05, min(0.60, downside))

    def _is_stale(self, ticker: str, max_age_days: int = 7) -> bool:
        """Check if trusted model predictions are older than max_age_days."""
        placeholders = ",".join(["%s"] * len(_TRUSTED_MODELS))
        cur = self.conn.cursor()
        cur.execute(
            f"SELECT MAX(timestamp) FROM valuation_results WHERE ticker = %s AND model_name IN ({placeholders})",
            (ticker, *_TRUSTED_MODELS),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return True
        try:
            ts = datetime.fromisoformat(row[0])
            return (datetime.now() - ts) > timedelta(days=max_age_days)
        except (ValueError, TypeError):
            return True

    def _no_data_result(self, ticker: str, reason: str) -> KellyResult:
        return KellyResult(
            ticker=ticker,
            current_price=0,
            expected_return=0,
            win_probability=0.5,
            win_loss_ratio=0,
            kelly_fraction=0,
            adjusted_fraction=0,
            dollar_amount=0,
            shares_to_buy=0,
            flags=[f"skip: {reason}"],
        )
