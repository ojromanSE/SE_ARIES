"""
Decline Curve Analysis Engine — reused from backend.
Synchronous version for Streamlit.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class DeclineType(str, Enum):
    EXPONENTIAL = "EXP"
    HYPERBOLIC = "HYP"
    HARMONIC = "HAR"
    MOD_HYPERBOLIC = "MHYP"


@dataclass
class DCAResult:
    months: np.ndarray
    rates_daily: np.ndarray
    volumes_monthly: np.ndarray
    cum_volumes: np.ndarray
    eur: float
    producing_months: int


def run_dca(
    decline_type: str,
    qi: float,
    di: float,
    b: float = 0.0,
    dt: Optional[float] = None,
    max_months: int = 480,
    min_rate: float = 0.0,
) -> DCAResult:
    days_per_month = 365.25 / 12.0
    months, rates, volumes, cums = [], [], [], []
    cum_vol = 0.0

    switch_month = None
    switch_rate = None
    if decline_type == DeclineType.MOD_HYPERBOLIC and dt is not None and b > 1e-6 and dt < di:
        t_switch = (di / dt - 1.0) / (b * di)
        switch_month = int(t_switch * 12)
        switch_rate = _hyp_rate(qi, di, b, t_switch)

    for m in range(max_months):
        t = m / 12.0
        if decline_type == DeclineType.EXPONENTIAL:
            rate = _exp_rate(qi, di, t)
        elif decline_type == DeclineType.HARMONIC:
            rate = _har_rate(qi, di, t)
        elif decline_type == DeclineType.HYPERBOLIC:
            rate = _hyp_rate(qi, di, b, t)
        elif decline_type == DeclineType.MOD_HYPERBOLIC:
            if switch_month and m >= switch_month and switch_rate:
                rate = _exp_rate(switch_rate, dt, (m - switch_month) / 12.0)
            else:
                rate = _hyp_rate(qi, di, b, t)
        else:
            rate = _exp_rate(qi, di, t)

        if rate <= min_rate or rate <= 0:
            break

        vol = rate * days_per_month
        cum_vol += vol
        months.append(m)
        rates.append(rate)
        volumes.append(vol)
        cums.append(cum_vol)

    if not months:
        return DCAResult(np.array([]), np.array([]), np.array([]), np.array([]), 0.0, 0)

    return DCAResult(
        months=np.array(months),
        rates_daily=np.array(rates),
        volumes_monthly=np.array(volumes),
        cum_volumes=np.array(cums),
        eur=float(cums[-1]),
        producing_months=len(months),
    )


def _exp_rate(qi, di, t): return qi * np.exp(-di * t)
def _hyp_rate(qi, di, b, t): return qi / (1 + b * di * t) ** (1 / b) if b > 1e-6 else _exp_rate(qi, di, t)
def _har_rate(qi, di, t): return qi / (1 + di * t)


def fit_decline(time_months: np.ndarray, rates: np.ndarray) -> tuple[float, float]:
    """Fit exponential decline. Returns (qi, di_annual)."""
    if len(rates) < 2:
        return float(rates[0]) if len(rates) else 0.0, 0.0
    t = time_months / 12.0
    log_r = np.log(np.maximum(rates, 1e-10))
    coeffs = np.polyfit(t, log_r, 1)
    return float(np.exp(coeffs[1])), float(max(-coeffs[0], 0.0))
