"""Model calibration using historical forward returns.

Since valuation_results only stores current predictions (not historical),
we calibrate by analyzing how fundamental characteristics predict actual
forward returns using the forward_returns + fundamental_history tables.

This answers: "When fundamentals look like X, what actually happens?"

Coverage in fundamental_history:
  - profit_margins: 23% of rows (best coverage)
  - return_on_equity: 20%
  - current_ratio: 20%
  - debt_to_equity: 13%
  - pb_ratio / ps_ratio: ~5%
  - pe_ratio: <1% (nearly empty)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from invest.valuation.db_utils import get_db_connection


@dataclass
class CalibrationBucket:
    label: str
    count: int
    mean_return: float
    median_return: float
    hit_rate: float  # fraction with positive return
    percentile_5: float
    percentile_95: float


@dataclass
class ModelCalibration:
    """Calibration results for adjusting Kelly p estimates."""

    horizon: str
    base_rate: float  # what % of all stocks go up at this horizon
    mean_return: float
    median_return: float
    total_snapshots: int
    buckets_by_margin: list[CalibrationBucket] = field(default_factory=list)
    buckets_by_roe: list[CalibrationBucket] = field(default_factory=list)
    buckets_by_pb: list[CalibrationBucket] = field(default_factory=list)

    def adjustment_for(
        self,
        profit_margin: float | None = None,
        roe: float | None = None,
        pb_ratio: float | None = None,
    ) -> float:
        """Return an adjusted win probability based on fundamentals.

        Blends base rate with bucket-specific hit rates.
        Returns a value in [0.1, 0.95].
        """
        adjustments = []

        if profit_margin is not None and self.buckets_by_margin:
            bucket = _find_bucket(profit_margin, self.buckets_by_margin, _MARGIN_THRESHOLDS)
            if bucket and bucket.count >= 20:
                adjustments.append(bucket.hit_rate)

        if roe is not None and self.buckets_by_roe:
            bucket = _find_bucket(roe, self.buckets_by_roe, _ROE_THRESHOLDS)
            if bucket and bucket.count >= 20:
                adjustments.append(bucket.hit_rate)

        if pb_ratio is not None and self.buckets_by_pb:
            bucket = _find_bucket(pb_ratio, self.buckets_by_pb, _PB_THRESHOLDS)
            if bucket and bucket.count >= 20:
                adjustments.append(bucket.hit_rate)

        if not adjustments:
            return self.base_rate

        avg = sum(adjustments) / len(adjustments)
        return max(0.1, min(0.95, avg))


# Thresholds — focused on metrics with actual data coverage
_MARGIN_THRESHOLDS = [0, 0.05, 0.10, 0.20, 0.30]
_MARGIN_LABELS = ["negative", "0-5%", "5-10%", "10-20%", "20-30%", "30%+"]

_ROE_THRESHOLDS = [0, 0.05, 0.10, 0.20, 0.30, 0.50]
_ROE_LABELS = ["negative", "0-5%", "5-10%", "10-20%", "20-30%", "30-50%", "50%+"]

_PB_THRESHOLDS = [0, 1, 2, 3, 5, 10]
_PB_LABELS = ["negative", "0-1", "1-2", "2-3", "3-5", "5-10", "10+"]


class ModelCalibrator:
    """Analyze historical forward returns to calibrate model predictions."""

    def __init__(self, db_path: Path | None = None):
        self.conn = get_db_connection(db_path)

    def calibrate(self, horizon: str = "1y") -> ModelCalibration:
        """Compute calibration data for a given horizon."""
        rows = self._fetch_data(horizon)
        if not rows:
            return ModelCalibration(
                horizon=horizon, base_rate=0.5, mean_return=0.0,
                median_return=0.0, total_snapshots=0,
            )

        returns = [r["return_pct"] for r in rows]
        returns_sorted = sorted(returns)
        n = len(returns)

        base_rate = sum(1 for r in returns if r > 0) / n
        mean_ret = sum(returns) / n
        median_ret = returns_sorted[n // 2]

        margin_buckets = self._bucket_by_metric(
            rows, "profit_margins", _MARGIN_THRESHOLDS, _MARGIN_LABELS
        )
        roe_buckets = self._bucket_by_metric(
            rows, "roe", _ROE_THRESHOLDS, _ROE_LABELS
        )
        pb_buckets = self._bucket_by_metric(
            rows, "pb_ratio", _PB_THRESHOLDS, _PB_LABELS
        )

        return ModelCalibration(
            horizon=horizon,
            base_rate=base_rate,
            mean_return=mean_ret,
            median_return=median_ret,
            total_snapshots=n,
            buckets_by_margin=margin_buckets,
            buckets_by_roe=roe_buckets,
            buckets_by_pb=pb_buckets,
        )

    def print_report(self, horizon: str = "1y") -> None:
        """Print a human-readable calibration report."""
        cal = self.calibrate(horizon)
        print(f"\n{'=' * 78}")
        print(f"CALIBRATION REPORT — {cal.horizon} forward returns")
        print(f"{'=' * 78}")
        print(f"Total observations: {cal.total_snapshots:,}")
        print(f"Base rate (% positive): {cal.base_rate:.1%}")
        print(f"Mean return: {cal.mean_return:+.1%} | Median: {cal.median_return:+.1%}")

        for label, buckets in [
            ("Profit Margin", cal.buckets_by_margin),
            ("Return on Equity", cal.buckets_by_roe),
            ("P/B Ratio", cal.buckets_by_pb),
        ]:
            if not buckets:
                print(f"\n--- By {label} --- (no data)")
                continue
            total_in_buckets = sum(b.count for b in buckets)
            print(f"\n--- By {label} ({total_in_buckets:,} obs) ---")
            print(
                f"{'Bucket':<12} | {'Count':>6} | {'Hit Rate':>8} | "
                f"{'Mean Ret':>8} | {'Median':>8} | {'5th pct':>8} | {'95th pct':>8}"
            )
            print("-" * 78)
            for b in buckets:
                print(
                    f"{b.label:<12} | {b.count:>6} | {b.hit_rate:>7.1%} | "
                    f"{b.mean_return:>+7.1%} | {b.median_return:>+7.1%} | "
                    f"{b.percentile_5:>+7.1%} | {b.percentile_95:>+7.1%}"
                )

    def print_all_horizons(self) -> None:
        """Print calibration for all available horizons."""
        for h in ["1m", "3m", "6m", "1y", "2y", "3y"]:
            self.print_report(h)

    def print_base_rates(self) -> None:
        """Print base rates across all horizons — the most useful calibration data."""
        print(f"\n{'=' * 60}")
        print("BASE RATES — Historical forward returns")
        print(f"{'=' * 60}")
        print(f"{'Horizon':<10} | {'Obs':>7} | {'Hit Rate':>8} | {'Mean':>8} | {'Median':>8}")
        print("-" * 60)
        for h in ["1m", "3m", "6m", "1y", "2y", "3y"]:
            cal = self.calibrate(h)
            if cal.total_snapshots == 0:
                continue
            print(
                f"{h:<10} | {cal.total_snapshots:>7,} | {cal.base_rate:>7.1%} | "
                f"{cal.mean_return:>+7.1%} | {cal.median_return:>+7.1%}"
            )
        print(f"\nInterpretation: base_rate is the % of stocks with positive")
        print(f"returns at each horizon. Use to sanity-check Kelly p estimates.")
        print(f"If your model says p=0.90 but base rate is 0.73, be skeptical.")

    def _fetch_data(self, horizon: str) -> list[dict]:
        """Join forward_returns with fundamental_history."""
        query = """
            SELECT
                a.symbol AS ticker,
                fh.snapshot_date,
                fh.pb_ratio,
                fh.ps_ratio,
                fh.profit_margins,
                fh.return_on_equity AS roe,
                fh.current_ratio,
                fh.debt_to_equity,
                fr.return_pct
            FROM forward_returns fr
            JOIN fundamental_history fh ON fr.snapshot_id = fh.id
            JOIN assets a ON fh.asset_id = a.id
            WHERE fr.horizon = ?
              AND fr.return_pct IS NOT NULL
        """
        cursor = self.conn.execute(query, (horizon,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _bucket_by_metric(
        self,
        rows: list[dict],
        metric: str,
        thresholds: list[float],
        labels: list[str],
    ) -> list[CalibrationBucket]:
        """Bucket rows by a fundamental metric and compute stats per bucket."""
        valid_rows = [
            (r[metric], r["return_pct"])
            for r in rows
            if r.get(metric) is not None
        ]
        if len(valid_rows) < 10:
            return []

        buckets: dict[str, list[float]] = {label: [] for label in labels}

        for metric_val, ret in valid_rows:
            bucket_label = self._assign_bucket(metric_val, thresholds, labels)
            buckets[bucket_label].append(ret)

        result = []
        for label in labels:
            returns = buckets[label]
            if not returns:
                continue
            returns_sorted = sorted(returns)
            n = len(returns_sorted)
            result.append(
                CalibrationBucket(
                    label=label,
                    count=n,
                    mean_return=sum(returns) / n,
                    median_return=returns_sorted[n // 2],
                    hit_rate=sum(1 for r in returns if r > 0) / n,
                    percentile_5=returns_sorted[max(0, int(n * 0.05))],
                    percentile_95=returns_sorted[min(n - 1, int(n * 0.95))],
                )
            )
        return result

    @staticmethod
    def _assign_bucket(
        value: float, thresholds: list[float], labels: list[str]
    ) -> str:
        if value < thresholds[0]:
            return labels[0]
        for i, thresh in enumerate(thresholds[1:], 1):
            if value < thresh:
                return labels[i]
        return labels[-1]


def _find_bucket(
    value: float,
    buckets: list[CalibrationBucket],
    thresholds: list[float],
) -> CalibrationBucket | None:
    """Find the calibration bucket for a given metric value."""
    # Determine which label this value falls into
    labels = [b.label for b in buckets]
    if not labels:
        return None

    # Use the same bucketing logic
    if value < thresholds[0]:
        target_idx = 0
    else:
        target_idx = len(thresholds)
        for i, thresh in enumerate(thresholds[1:], 1):
            if value < thresh:
                target_idx = i
                break

    # Map index to bucket — thresholds produce len(thresholds)+1 buckets
    # but we only have buckets for non-empty ones
    # Build full label list to find the right one
    all_labels = []
    if thresholds[0] > float("-inf"):
        all_labels.append("negative" if thresholds[0] == 0 else f"<{thresholds[0]}")
    for i in range(len(thresholds) - 1):
        all_labels.append(f"placeholder_{i}")  # we don't need exact labels
    all_labels.append("last")

    # Just find by index clamped to available buckets
    target_idx = min(target_idx, len(buckets) - 1)
    target_idx = max(0, target_idx)
    return buckets[target_idx]
