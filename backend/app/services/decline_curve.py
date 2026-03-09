"""
Decline Curve Analysis (DCA) Engine
Implements ARIES-compatible decline curve methods:
  - Exponential (EXP)
  - Hyperbolic (HYP)
  - Harmonic (HAR)  — special case of HYP with b=1
  - Modified Hyperbolic — switches to exponential at terminal decline rate
"""
import numpy as np
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class DeclineType(str, Enum):
    EXPONENTIAL = "EXP"
    HYPERBOLIC = "HYP"
    HARMONIC = "HAR"
    MOD_HYPERBOLIC = "MHYP"  # Hyperbolic → Exponential at terminal decline


@dataclass
class DCAParameters:
    """Input parameters for decline curve analysis."""
    decline_type: DeclineType
    qi: float           # Initial rate (BBL/day or MMCF/day)
    di: float           # Nominal decline rate (/year)
    b: float = 0.0      # Hyperbolic b-factor (0 = EXP, 1 = Harmonic)
    dt: Optional[float] = None  # Terminal decline rate for modified hyperbolic
    max_months: int = 480       # 40 years max
    min_rate: float = 0.0       # Economic limit rate
    cum_start: float = 0.0      # Cumulative production to start of forecast (MSTB or MMCF)


@dataclass
class DCAResult:
    """Monthly production forecast from DCA."""
    months: np.ndarray          # Month indices (0, 1, 2, ...)
    rates_daily: np.ndarray     # Daily rates per month
    volumes_monthly: np.ndarray # Monthly volumes
    cum_volumes: np.ndarray     # Cumulative volumes
    eur: float                  # Estimated Ultimate Recovery
    producing_months: int       # Number of producing months until econ limit


def exponential_rate(qi: float, di_annual: float, t_years: float) -> float:
    """
    q(t) = qi * exp(-di * t)
    """
    return qi * np.exp(-di_annual * t_years)


def hyperbolic_rate(qi: float, di_annual: float, b: float, t_years: float) -> float:
    """
    q(t) = qi / (1 + b * di * t)^(1/b)
    Falls back to exponential when b == 0.
    """
    if abs(b) < 1e-6:
        return exponential_rate(qi, di_annual, t_years)
    return qi / (1.0 + b * di_annual * t_years) ** (1.0 / b)


def harmonic_rate(qi: float, di_annual: float, t_years: float) -> float:
    """
    q(t) = qi / (1 + di * t)   [b=1 case]
    """
    return qi / (1.0 + di_annual * t_years)


def exponential_cum(qi: float, di_annual: float, t_years: float) -> float:
    """
    Np(t) = (qi / di) * (1 - exp(-di * t))
    Returns cumulative volume in same units as qi * time.
    """
    if di_annual < 1e-10:
        return qi * t_years * 365.25
    return (qi / di_annual) * (1.0 - np.exp(-di_annual * t_years)) * 365.25


def hyperbolic_cum(qi: float, di_annual: float, b: float, t_years: float) -> float:
    """
    Np(t) = (qi^b / ((1-b) * di)) * (qi^(1-b) - q^(1-b))
    Or equivalently: Np = qi*t_years*365 / (1-b) * [1 - (1 + b*di*t)^(-(1-b)/b)] ... simplified form.
    """
    if abs(b) < 1e-6:
        return exponential_cum(qi, di_annual, t_years)
    if abs(b - 1.0) < 1e-6:
        return harmonic_cum(qi, di_annual, t_years)
    qt = hyperbolic_rate(qi, di_annual, b, t_years)
    return (qi ** b / ((1.0 - b) * di_annual)) * (qi ** (1.0 - b) - qt ** (1.0 - b)) * 365.25


def harmonic_cum(qi: float, di_annual: float, t_years: float) -> float:
    """
    Np(t) = (qi / di) * ln(qi / q(t))
    """
    qt = harmonic_rate(qi, di_annual, t_years)
    if qt <= 0:
        return 0.0
    return (qi / di_annual) * np.log(qi / qt) * 365.25


def run_dca(params: DCAParameters) -> DCAResult:
    """
    Run decline curve analysis and return monthly production forecast.
    Handles EXP, HYP, HAR, and Modified Hyperbolic (switches to EXP at dt).
    """
    months = []
    rates = []
    volumes = []
    cums = []

    dt_per_month = 1.0 / 12.0  # Each time step = 1 month in years
    di = params.di  # Annual nominal decline rate
    b = params.b
    cum_vol = params.cum_start

    # For modified hyperbolic: find when hyperbolic decline equals terminal decline
    switch_month = None
    switch_rate = None
    if params.decline_type == DeclineType.MOD_HYPERBOLIC and params.dt is not None:
        # Find switch point: di_hyp(t) = dt
        # d(t) = di / (1 + b*di*t) for hyperbolic  => solve for t when d(t) = dt
        if b > 1e-6 and params.dt < di:
            t_switch_years = (di / params.dt - 1.0) / (b * di)
            switch_month = int(t_switch_years * 12)
            switch_rate = hyperbolic_rate(params.qi, di, b, t_switch_years)

    for m in range(params.max_months):
        t_years = m * dt_per_month

        if params.decline_type == DeclineType.EXPONENTIAL:
            rate = exponential_rate(params.qi, di, t_years)
        elif params.decline_type == DeclineType.HARMONIC:
            rate = harmonic_rate(params.qi, di, t_years)
        elif params.decline_type == DeclineType.HYPERBOLIC:
            rate = hyperbolic_rate(params.qi, di, b, t_years)
        elif params.decline_type == DeclineType.MOD_HYPERBOLIC:
            if switch_month is not None and m >= switch_month and switch_rate is not None:
                # Switch to exponential from the switch point
                t_after_switch = (m - switch_month) * dt_per_month
                rate = exponential_rate(switch_rate, params.dt, t_after_switch)
            else:
                rate = hyperbolic_rate(params.qi, di, b, t_years)
        else:
            rate = exponential_rate(params.qi, di, t_years)

        # Check economic limit
        if rate <= params.min_rate or rate <= 0:
            break

        # Monthly volume (rate * days in month, using 365.25/12 avg days)
        days_in_month = 365.25 / 12.0
        monthly_vol = rate * days_in_month

        cum_vol += monthly_vol
        months.append(m)
        rates.append(rate)
        volumes.append(monthly_vol)
        cums.append(cum_vol)

    if not months:
        return DCAResult(
            months=np.array([]),
            rates_daily=np.array([]),
            volumes_monthly=np.array([]),
            cum_volumes=np.array([]),
            eur=0.0,
            producing_months=0,
        )

    return DCAResult(
        months=np.array(months),
        rates_daily=np.array(rates),
        volumes_monthly=np.array(volumes),
        cum_volumes=np.array(cums),
        eur=float(cums[-1]),
        producing_months=len(months),
    )


def fit_exponential_decline(time_months: np.ndarray, rates: np.ndarray) -> tuple[float, float]:
    """
    Fit exponential decline to production data.
    Returns (qi, di_annual) via linear regression on log(q) vs t.
    """
    if len(rates) < 2:
        return rates[0] if len(rates) > 0 else 0.0, 0.0

    log_rates = np.log(np.maximum(rates, 1e-10))
    t_years = time_months / 12.0
    coeffs = np.polyfit(t_years, log_rates, 1)
    di_annual = -coeffs[0]
    qi = np.exp(coeffs[1])
    return float(qi), float(max(di_annual, 0.0))
