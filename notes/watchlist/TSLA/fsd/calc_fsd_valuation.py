from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib

DEFAULT_ASSUMPTIONS_PATH = Path(__file__).with_name('assumptions.toml')


@dataclass(frozen=True)
class Assumptions:
    """Input assumptions for the FSD valuation model.

    Parameters
    ----------
    currency : str
        Currency code used in outputs.
    operating_hours_per_day : float
        Monetizable hours per day.
    avg_speed_kph : float
        Average effective speed in kilometers per hour.
    days_per_year : int
        Days of operation per year.
    km_per_year_override : int | None
        Optional override for annual kilometers per vehicle.
    price_per_km : float
        Rider price per kilometer.
    electricity_per_km : float
        Electricity cost per kilometer.
    maintenance_per_km : float
        Maintenance and tires cost per kilometer.
    insurance_cleaning_misc_per_year : float
        Fixed annual costs per vehicle.
    vehicle_cost : float
        Vehicle purchase cost.
    required_return_rate : float
        Required annual return on vehicle cost.
    tesla_capture_rate : float
        Tesla share of surplus economics.
    fleet_size : int | None
        Active robotaxi fleet size when modeled directly.
    total_km_per_year : float | None
        Total annual kilometers served, used to infer fleet size.
    population : int | None
        Population used to estimate annual kilometers.
    km_per_person_per_day : float | None
        Daily kilometers per person used to estimate annual kilometers.
    adoption_rate : float
        Share of total travel assumed to use FSD.
    operating_margin : float
        Operating margin applied to Tesla revenue.
    valuation_multiple : float
        Multiple applied to operating profit.
    """

    currency: str
    operating_hours_per_day: float
    avg_speed_kph: float
    days_per_year: int
    km_per_year_override: int | None
    price_per_km: float
    electricity_per_km: float
    maintenance_per_km: float
    insurance_cleaning_misc_per_year: float
    vehicle_cost: float
    required_return_rate: float
    tesla_capture_rate: float
    fleet_size: int | None
    total_km_per_year: float | None
    population: int | None
    km_per_person_per_day: float | None
    adoption_rate: float
    operating_margin: float
    valuation_multiple: float


@dataclass(frozen=True)
class ValuationMetrics:
    """Computed metrics for the FSD valuation model.

    Attributes
    ----------
    km_per_day : float
        Average kilometers driven per day.
    km_per_year : float
        Annual kilometers driven per vehicle.
    total_km_per_year : float
        Total annual kilometers served.
    fleet_size : float
        Fleet size used to scale Tesla-level economics.
    gross_revenue_per_vehicle : float
        Annual gross revenue per vehicle.
    operating_cost_per_vehicle : float
        Annual operating cost per vehicle.
    required_return_per_vehicle : float
        Annual required return on vehicle cost.
    required_cash_out_per_vehicle : float
        Total annual cash out per vehicle.
    surplus_per_vehicle : float
        Annual economic surplus per vehicle.
    tesla_capture_per_vehicle : float
        Annual Tesla capture per vehicle.
    tesla_revenue_total : float
        Total Tesla revenue across the fleet.
    tesla_operating_profit_total : float
        Total Tesla operating profit across the fleet.
    implied_valuation_total : float
        Implied valuation from the operating profit multiple.
    """

    km_per_day: float
    km_per_year: float
    total_km_per_year: float
    fleet_size: float
    gross_revenue_per_vehicle: float
    operating_cost_per_vehicle: float
    required_return_per_vehicle: float
    required_cash_out_per_vehicle: float
    surplus_per_vehicle: float
    tesla_capture_per_vehicle: float
    tesla_revenue_total: float
    tesla_operating_profit_total: float
    implied_valuation_total: float


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with the assumptions path.
    """

    parser = argparse.ArgumentParser(
        description='Calculate FSD valuation from assumptions.'
    )
    parser.add_argument(
        '--assumptions',
        type=Path,
        default=DEFAULT_ASSUMPTIONS_PATH,
        help='Path to assumptions TOML file.'
    )
    return parser.parse_args()


def load_assumptions(path: Path) -> Assumptions:
    """Load assumptions from a TOML file.

    Parameters
    ----------
    path : Path
        Path to the assumptions file.

    Returns
    -------
    Assumptions
        Parsed assumptions.
    """

    if not path.exists():
        raise FileNotFoundError(f'Assumptions file not found: {path}')

    data = tomllib.loads(path.read_text(encoding='utf-8'))
    raw = data.get('assumptions')
    if not isinstance(raw, dict):
        raise ValueError('Missing [assumptions] table in TOML file.')

    km_override = raw.get('km_per_year_override')
    if km_override is not None:
        km_override = int(km_override)
    fleet_size = raw.get('fleet_size')
    if fleet_size is not None:
        fleet_size = int(fleet_size)
    total_km_per_year = raw.get('total_km_per_year')
    if total_km_per_year is not None:
        total_km_per_year = float(total_km_per_year)
    population = raw.get('population')
    if population is not None:
        population = int(population)
    km_per_person_per_day = raw.get('km_per_person_per_day')
    if km_per_person_per_day is not None:
        km_per_person_per_day = float(km_per_person_per_day)
    adoption_rate = float(raw.get('adoption_rate', 1.0))

    try:
        return Assumptions(
            currency=str(raw['currency']),
            operating_hours_per_day=float(raw['operating_hours_per_day']),
            avg_speed_kph=float(raw['avg_speed_kph']),
            days_per_year=int(raw['days_per_year']),
            km_per_year_override=km_override,
            price_per_km=float(raw['price_per_km']),
            electricity_per_km=float(raw['electricity_per_km']),
            maintenance_per_km=float(raw['maintenance_per_km']),
            insurance_cleaning_misc_per_year=float(
                raw['insurance_cleaning_misc_per_year']
            ),
            vehicle_cost=float(raw['vehicle_cost']),
            required_return_rate=float(raw['required_return_rate']),
            tesla_capture_rate=float(raw['tesla_capture_rate']),
            fleet_size=fleet_size,
            total_km_per_year=total_km_per_year,
            population=population,
            km_per_person_per_day=km_per_person_per_day,
            adoption_rate=adoption_rate,
            operating_margin=float(raw['operating_margin']),
            valuation_multiple=float(raw['valuation_multiple'])
        )
    except KeyError as exc:
        raise KeyError(f'Missing assumption: {exc}') from exc


def validate_assumptions(assumptions: Assumptions) -> None:
    """Validate assumptions for basic ranges.

    Parameters
    ----------
    assumptions : Assumptions
        Parsed assumptions to validate.

    Raises
    ------
    ValueError
        If any assumption is out of range.
    """

    if assumptions.operating_hours_per_day <= 0:
        raise ValueError('operating_hours_per_day must be > 0')
    if assumptions.operating_hours_per_day > 24:
        raise ValueError('operating_hours_per_day must be <= 24')
    if assumptions.avg_speed_kph <= 0:
        raise ValueError('avg_speed_kph must be > 0')
    if assumptions.days_per_year <= 0:
        raise ValueError('days_per_year must be > 0')
    if assumptions.km_per_year_override is not None:
        if assumptions.km_per_year_override <= 0:
            raise ValueError('km_per_year_override must be > 0')
    if assumptions.price_per_km <= 0:
        raise ValueError('price_per_km must be > 0')
    if assumptions.electricity_per_km < 0:
        raise ValueError('electricity_per_km must be >= 0')
    if assumptions.maintenance_per_km < 0:
        raise ValueError('maintenance_per_km must be >= 0')
    if assumptions.insurance_cleaning_misc_per_year < 0:
        raise ValueError('insurance_cleaning_misc_per_year must be >= 0')
    if assumptions.vehicle_cost <= 0:
        raise ValueError('vehicle_cost must be > 0')
    if not 0 < assumptions.required_return_rate < 1:
        raise ValueError('required_return_rate must be between 0 and 1')
    if not 0 <= assumptions.tesla_capture_rate <= 1:
        raise ValueError('tesla_capture_rate must be between 0 and 1')
    if assumptions.total_km_per_year is not None:
        if assumptions.total_km_per_year <= 0:
            raise ValueError('total_km_per_year must be > 0')
    if assumptions.population is not None:
        if assumptions.population <= 0:
            raise ValueError('population must be > 0')
    if assumptions.km_per_person_per_day is not None:
        if assumptions.km_per_person_per_day <= 0:
            raise ValueError('km_per_person_per_day must be > 0')
    if not 0 < assumptions.adoption_rate <= 1:
        raise ValueError('adoption_rate must be between 0 and 1')
    if assumptions.fleet_size is not None:
        if assumptions.fleet_size <= 0:
            raise ValueError('fleet_size must be > 0')
    if not 0 <= assumptions.operating_margin <= 1:
        raise ValueError('operating_margin must be between 0 and 1')
    if assumptions.valuation_multiple <= 0:
        raise ValueError('valuation_multiple must be > 0')

    has_fleet_size = assumptions.fleet_size is not None
    has_total_km = assumptions.total_km_per_year is not None
    has_person_km = (
        assumptions.population is not None
        or assumptions.km_per_person_per_day is not None
    )
    if has_person_km and (
        assumptions.population is None
        or assumptions.km_per_person_per_day is None
    ):
        raise ValueError(
            'population and km_per_person_per_day must be set together'
        )

    mode_count = sum(
        1
        for flag in (
            has_fleet_size,
            has_total_km,
            assumptions.population is not None
            and assumptions.km_per_person_per_day is not None
        )
        if flag
    )
    if mode_count != 1:
        raise ValueError(
            'Set exactly one: fleet_size, total_km_per_year, or '
            'population + km_per_person_per_day'
        )


def compute_metrics(assumptions: Assumptions) -> ValuationMetrics:
    """Compute valuation metrics from assumptions.

    Parameters
    ----------
    assumptions : Assumptions
        Inputs for the valuation model.

    Returns
    -------
    ValuationMetrics
        Computed metrics based on the assumptions.
    """

    km_per_day = assumptions.operating_hours_per_day * assumptions.avg_speed_kph
    if assumptions.km_per_year_override is not None:
        km_per_year = float(assumptions.km_per_year_override)
    else:
        km_per_year = km_per_day * assumptions.days_per_year

    if assumptions.total_km_per_year is not None:
        total_km_per_year = float(assumptions.total_km_per_year)
        fleet_size = total_km_per_year / km_per_year
    elif (
        assumptions.population is not None
        and assumptions.km_per_person_per_day is not None
    ):
        total_km_per_year = (
            assumptions.population
            * assumptions.km_per_person_per_day
            * assumptions.days_per_year
            * assumptions.adoption_rate
        )
        fleet_size = total_km_per_year / km_per_year
    else:
        fleet_size = float(assumptions.fleet_size)
        total_km_per_year = fleet_size * km_per_year

    gross_revenue_per_vehicle = km_per_year * assumptions.price_per_km
    electricity_cost = km_per_year * assumptions.electricity_per_km
    maintenance_cost = km_per_year * assumptions.maintenance_per_km
    operating_cost_per_vehicle = (
        electricity_cost
        + maintenance_cost
        + assumptions.insurance_cleaning_misc_per_year
    )
    required_return_per_vehicle = (
        assumptions.vehicle_cost * assumptions.required_return_rate
    )
    required_cash_out_per_vehicle = (
        operating_cost_per_vehicle + required_return_per_vehicle
    )
    surplus_per_vehicle = (
        gross_revenue_per_vehicle - required_cash_out_per_vehicle
    )
    tesla_capture_per_vehicle = (
        surplus_per_vehicle * assumptions.tesla_capture_rate
    )
    tesla_revenue_total = tesla_capture_per_vehicle * fleet_size
    tesla_operating_profit_total = (
        tesla_revenue_total * assumptions.operating_margin
    )
    implied_valuation_total = (
        tesla_operating_profit_total * assumptions.valuation_multiple
    )

    return ValuationMetrics(
        km_per_day=km_per_day,
        km_per_year=km_per_year,
        total_km_per_year=total_km_per_year,
        fleet_size=fleet_size,
        gross_revenue_per_vehicle=gross_revenue_per_vehicle,
        operating_cost_per_vehicle=operating_cost_per_vehicle,
        required_return_per_vehicle=required_return_per_vehicle,
        required_cash_out_per_vehicle=required_cash_out_per_vehicle,
        surplus_per_vehicle=surplus_per_vehicle,
        tesla_capture_per_vehicle=tesla_capture_per_vehicle,
        tesla_revenue_total=tesla_revenue_total,
        tesla_operating_profit_total=tesla_operating_profit_total,
        implied_valuation_total=implied_valuation_total
    )


def format_currency(amount: float, currency: str) -> str:
    """Format a currency amount for display.

    Parameters
    ----------
    amount : float
        Amount in currency units.
    currency : str
        Currency code.

    Returns
    -------
    str
        Formatted currency string.
    """

    return f'{currency} {amount:,.0f}'


def format_number(amount: float) -> str:
    """Format a number with thousands separators.

    Parameters
    ----------
    amount : float
        Numeric value to format.

    Returns
    -------
    str
        Formatted number string.
    """

    return f'{amount:,.0f}'


def print_report(
    assumptions: Assumptions,
    metrics: ValuationMetrics,
    assumptions_path: Path
) -> None:
    """Print a valuation report.

    Parameters
    ----------
    assumptions : Assumptions
        Assumptions used in the model.
    metrics : ValuationMetrics
        Computed metrics.
    assumptions_path : Path
        Path to the assumptions file.
    """

    currency = assumptions.currency
    print('FSD / robotaxi valuation')
    print(f'Assumptions file: {assumptions_path}')
    print('')

    print('Utilization')
    print(f'  km/day: {format_number(metrics.km_per_day)}')
    print(f'  km/year: {format_number(metrics.km_per_year)}')
    print('')

    print('Demand scale')
    print(f'  total km/year: {format_number(metrics.total_km_per_year)}')
    fleet_label = (
        'fleet size (implied)'
        if assumptions.fleet_size is None
        else 'fleet size'
    )
    print(f'  {fleet_label}: {format_number(metrics.fleet_size)}')
    print('')

    print('Per-vehicle economics')
    print(
        f'  gross revenue: {format_currency(metrics.gross_revenue_per_vehicle, currency)}'
    )
    print(
        f'  operating cost: {format_currency(metrics.operating_cost_per_vehicle, currency)}'
    )
    print(
        f'  required return: {format_currency(metrics.required_return_per_vehicle, currency)}'
    )
    print(
        f'  required cash out: {format_currency(metrics.required_cash_out_per_vehicle, currency)}'
    )
    print(
        f'  surplus: {format_currency(metrics.surplus_per_vehicle, currency)}'
    )
    print(
        f'  Tesla capture: {format_currency(metrics.tesla_capture_per_vehicle, currency)}'
    )
    print('')

    print('Tesla-level economics')
    print(
        f'  Tesla revenue: {format_currency(metrics.tesla_revenue_total, currency)}'
    )
    print(
        f'  Tesla operating profit: {format_currency(metrics.tesla_operating_profit_total, currency)}'
    )
    print(
        f'  implied valuation: {format_currency(metrics.implied_valuation_total, currency)}'
    )


def main() -> int:
    """Run the valuation script.

    Returns
    -------
    int
        Process exit code.
    """

    args = parse_args()
    try:
        assumptions = load_assumptions(args.assumptions)
        validate_assumptions(assumptions)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f'Error: {exc}')
        return 1

    metrics = compute_metrics(assumptions)
    print_report(assumptions, metrics, args.assumptions)
    return 0


if __name__ == '__main__':
    sys.exit(main())
