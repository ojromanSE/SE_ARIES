"""
Economic Simulator — synchronous version for Streamlit.
Replicates ARIES keyword-driven economic model.
"""
import numpy as np
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass, field
from typing import Optional

from services.decline_curve import run_dca


@dataclass
class EconInputs:
    propnum: str = ""
    econ_start_date: date = field(default_factory=date.today)
    # Prices (from scenario)
    oil_price: float = 70.0
    gas_price: float = 3.0
    ngl_price_pct: float = 0.4
    discount_rate: float = 0.10
    tax_rate: float = 0.05
    ad_valorem_rate: float = 0.02
    chance_of_success: float = 1.0
    apply_economic_limit: bool = True
    oil_price_escalation: float = 0.0
    gas_price_escalation: float = 0.0
    # Ownership
    working_interest: float = 1.0
    net_revenue_interest: float = 1.0
    # Decline — oil
    oil_decline_type: str = "EXP"
    oil_qi: float = 0.0
    oil_di: float = 0.0
    oil_b: float = 0.0
    oil_dt: Optional[float] = None
    # Decline — gas
    gas_decline_type: str = "EXP"
    gas_qi: float = 0.0
    gas_di: float = 0.0
    gas_b: float = 0.0
    gas_dt: Optional[float] = None
    # Gas handling
    shrinkage: float = 1.0
    btu_factor: float = 1.0
    ngl_yield: float = 0.0
    gas_oil_ratio: float = 0.0
    # Pricing adjustments
    oil_price_diff: float = 0.0
    gas_price_diff: float = 0.0
    # OPEX
    fixed_opex: float = 0.0
    variable_oil_opex: float = 0.0
    variable_gas_opex: float = 0.0
    overhead: float = 0.0
    # CAPEX
    initial_capex: float = 0.0
    abandonment_cost: float = 0.0
    # Econ limit
    econ_limit_type: str = "NET_REVENUE"
    econ_limit_value: float = 0.0
    max_life_months: int = 480


@dataclass
class EconResult:
    npv10: float
    npv15: float
    irr: Optional[float]
    payout_months: Optional[float]
    total_revenue: float
    total_opex: float
    total_capex: float
    cum_oil_mstb: float
    cum_gas_mmcf: float
    cum_ngl_mstb: float
    monthly_df: pd.DataFrame  # Full monthly cash flow table


def run_economics(inp: EconInputs) -> EconResult:
    days_per_month = 365.25 / 12.0

    oil_dca = run_dca(inp.oil_decline_type, inp.oil_qi, inp.oil_di, inp.oil_b, inp.oil_dt, inp.max_life_months) if inp.oil_qi > 0 else None
    gas_dca = run_dca(inp.gas_decline_type, inp.gas_qi, inp.gas_di, inp.gas_b, inp.gas_dt, inp.max_life_months) if inp.gas_qi > 0 and not (inp.oil_qi > 0 and inp.gas_oil_ratio > 0) else None

    max_m = inp.max_life_months
    if oil_dca: max_m = min(max_m, oil_dca.producing_months)
    if gas_dca: max_m = min(max_m, gas_dca.producing_months)

    rows = []
    cum_oil, cum_gas, cum_ngl = 0.0, 0.0, 0.0
    cum_ncf = 0.0
    payout_month = None
    monthly_disc_rate = (1 + inp.discount_rate) ** (1 / 12) - 1
    monthly_disc_rate_15 = (1.15) ** (1 / 12) - 1
    disc10, disc15 = 1.0, 1.0
    cash_flows = [-inp.initial_capex]

    for m in range(max_m):
        d = inp.econ_start_date + relativedelta(months=m)

        oil_rate = oil_dca.rates_daily[m] if oil_dca and m < len(oil_dca.rates_daily) else 0.0
        if inp.gas_oil_ratio > 0 and oil_rate > 0:
            gas_rate = oil_rate * inp.gas_oil_ratio
        elif gas_dca and m < len(gas_dca.rates_daily):
            gas_rate = gas_dca.rates_daily[m]
        else:
            gas_rate = 0.0

        sales_gas = gas_rate * inp.shrinkage
        ngl_rate = sales_gas * inp.ngl_yield / 1000.0

        gross_oil = oil_rate * days_per_month
        gross_gas = gas_rate * days_per_month * inp.shrinkage / 1000.0  # MMCF
        gross_ngl = ngl_rate * days_per_month
        net_oil = gross_oil * inp.working_interest
        net_gas = gross_gas * inp.working_interest
        net_ngl = gross_ngl * inp.working_interest

        cum_oil += net_oil / 1000.0
        cum_gas += net_gas
        cum_ngl += net_ngl / 1000.0

        t_yr = m / 12.0
        oil_px = (inp.oil_price + inp.oil_price_diff) * (1 + inp.oil_price_escalation / 100) ** t_yr * inp.btu_factor
        gas_px = (inp.gas_price + inp.gas_price_diff) * (1 + inp.gas_price_escalation / 100) ** t_yr
        ngl_px = inp.oil_price * inp.ngl_price_pct

        oil_rev = net_oil * inp.net_revenue_interest * oil_px
        gas_rev = net_gas * 1000 * inp.net_revenue_interest * gas_px
        ngl_rev = net_ngl * inp.net_revenue_interest * ngl_px
        total_rev = oil_rev + gas_rev + ngl_rev

        prod_tax = total_rev * inp.tax_rate
        ad_val = total_rev * inp.ad_valorem_rate
        var_opex = net_oil * inp.variable_oil_opex + net_gas * 1000 * inp.variable_gas_opex
        fixed = (inp.fixed_opex + inp.overhead) * inp.working_interest
        opex = fixed + var_opex
        capex = 0.0

        ncf = (total_rev - prod_tax - ad_val - opex - capex) * inp.chance_of_success

        if inp.apply_economic_limit:
            if inp.econ_limit_type == "NET_REVENUE" and ncf < inp.econ_limit_value:
                break
            elif inp.econ_limit_type == "OIL_RATE" and oil_rate < inp.econ_limit_value:
                break
            elif inp.econ_limit_type == "GAS_RATE" and gas_rate < inp.econ_limit_value:
                break

        cum_ncf += ncf
        if payout_month is None and cum_ncf >= inp.initial_capex:
            payout_month = m + 1

        disc_ncf_10 = ncf * disc10
        disc_ncf_15 = ncf * disc15
        disc10 /= (1 + monthly_disc_rate)
        disc15 /= (1 + monthly_disc_rate_15)
        cash_flows.append(ncf)

        rows.append({
            "month": m,
            "date": d,
            "oil_rate_bopd": round(oil_rate, 2),
            "gas_rate_mcfd": round(gas_rate, 2),
            "gross_oil_bbl": round(gross_oil, 0),
            "gross_gas_mcf": round(gross_gas * 1000, 0),
            "gross_ngl_bbl": round(gross_ngl, 0),
            "net_oil_bbl": round(net_oil, 0),
            "net_gas_mcf": round(net_gas * 1000, 0),
            "oil_revenue": round(oil_rev, 2),
            "gas_revenue": round(gas_rev, 2),
            "ngl_revenue": round(ngl_rev, 2),
            "total_revenue": round(total_rev, 2),
            "prod_taxes": round(prod_tax, 2),
            "opex": round(opex, 2),
            "capex": round(capex, 2),
            "net_cash_flow": round(ncf, 2),
            "cum_cash_flow": round(cum_ncf, 2),
            "discounted_ncf_10": round(disc_ncf_10, 2),
            "discounted_ncf_15": round(disc_ncf_15, 2),
            "cum_oil_mstb": round(cum_oil, 3),
            "cum_gas_mmcf": round(cum_gas, 3),
            "cum_ngl_mstb": round(cum_ngl, 3),
        })

    if not rows:
        empty_df = pd.DataFrame()
        return EconResult(0, 0, None, None, 0, 0, inp.initial_capex, 0, 0, 0, empty_df)

    df = pd.DataFrame(rows)

    # Last row: add abandonment
    df.loc[df.index[-1], "capex"] += inp.abandonment_cost
    df.loc[df.index[-1], "net_cash_flow"] -= inp.abandonment_cost

    npv10 = df["discounted_ncf_10"].sum() - inp.initial_capex
    npv15 = df["discounted_ncf_15"].sum() - inp.initial_capex
    irr = _calc_irr(cash_flows)

    return EconResult(
        npv10=round(npv10, 0),
        npv15=round(npv15, 0),
        irr=irr,
        payout_months=payout_month,
        total_revenue=round(df["total_revenue"].sum(), 0),
        total_opex=round(df["opex"].sum(), 0),
        total_capex=inp.initial_capex,
        cum_oil_mstb=round(df["cum_oil_mstb"].iloc[-1], 2),
        cum_gas_mmcf=round(df["cum_gas_mmcf"].iloc[-1], 2),
        cum_ngl_mstb=round(df["cum_ngl_mstb"].iloc[-1], 2),
        monthly_df=df,
    )


def _calc_irr(cfs: list[float], guess: float = 0.1) -> Optional[float]:
    if not cfs or cfs[0] >= 0:
        return None
    rate = guess
    for _ in range(1000):
        npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cfs))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cfs))
        if abs(dnpv) < 1e-12:
            break
        rate -= npv / dnpv
        if rate <= -1:
            return None
        if abs(npv) < 1e-4:
            break
    annual = (1 + rate) ** 12 - 1
    return round(annual * 100, 2) if -1 < annual < 100 else None
