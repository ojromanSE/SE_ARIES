"""
Economic Simulator
Replicates ARIES keyword-driven economic model.
Generates monthly cash flow and calculates NPV, IRR, payout, etc.
"""
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional
from dataclasses import dataclass, field

from app.services.decline_curve import DCAParameters, DeclineType, run_dca


@dataclass
class EconomicInputs:
    """Full economic model inputs for one property/scenario — mirrors AC_ECONOMIC."""
    propnum: str
    scenario_id: int
    econ_start_date: date

    # Scenario-level inputs
    oil_price: float = 70.0         # $/BBL flat price
    gas_price: float = 3.0          # $/MCF flat price
    ngl_price_pct: float = 0.4      # NGL as % of oil price
    discount_rate: float = 0.10     # 10% annual discount rate
    tax_rate: float = 0.05          # Severance tax rate (fraction)
    ad_valorem_rate: float = 0.02   # Ad valorem tax rate
    chance_of_success: float = 1.0  # Risk factor (XINVWT)
    apply_economic_limit: bool = True  # LOSS keyword

    # Property-level: ownership
    working_interest: float = 1.0
    net_revenue_interest: float = 1.0

    # Decline curve inputs — oil
    oil_decline_type: str = "EXP"
    oil_qi: float = 0.0             # BOPD initial rate
    oil_di: float = 0.0             # Annual nominal decline (/yr)
    oil_b: float = 0.0
    oil_dt: Optional[float] = None
    oil_eur: Optional[float] = None

    # Decline curve inputs — gas
    gas_decline_type: str = "EXP"
    gas_qi: float = 0.0             # MCFD initial rate
    gas_di: float = 0.0
    gas_b: float = 0.0
    gas_dt: Optional[float] = None

    # Gas handling
    shrinkage: float = 1.0          # SHRINK keyword — wet to dry gas factor
    btu_factor: float = 1.0         # BTU keyword — price adjustment
    ngl_yield: float = 0.0          # BBL NGL per MMCF gas
    gas_oil_ratio: float = 0.0      # MCF/BBL — if gas driven by oil decline

    # Pricing adjustments
    oil_price_diff: float = 0.0     # $/BBL differential
    gas_price_diff: float = 0.0     # $/MCF differential

    # OPEX
    fixed_opex: float = 0.0         # $/month
    variable_oil_opex: float = 0.0  # $/BBL oil
    variable_gas_opex: float = 0.0  # $/MCF gas
    overhead: float = 0.0           # $/month G&A

    # CAPEX
    initial_capex: float = 0.0      # $ upfront capital
    abandonment_cost: float = 0.0   # $ at end of life

    # Economic limit
    econ_limit_type: str = "NET_REVENUE"  # NET_REVENUE, OIL_RATE, GAS_RATE
    econ_limit_value: float = 0.0   # $ or rate
    max_life_months: int = 480

    # Price escalation (annual %)
    oil_price_escalation: float = 0.0
    gas_price_escalation: float = 0.0


@dataclass
class MonthlyRow:
    """One row of monthly cash flow output."""
    month: int
    date: date
    year: int

    # Production (gross)
    gross_oil_bbl: float = 0.0
    gross_gas_mcf: float = 0.0
    gross_ngl_bbl: float = 0.0

    # Production (net to WI)
    net_oil_bbl: float = 0.0
    net_gas_mcf: float = 0.0
    net_ngl_bbl: float = 0.0

    # Revenue (net to NRI)
    oil_revenue: float = 0.0
    gas_revenue: float = 0.0
    ngl_revenue: float = 0.0
    total_revenue: float = 0.0

    # Costs
    prod_taxes: float = 0.0
    ad_valorem: float = 0.0
    opex: float = 0.0
    capex: float = 0.0

    # Cash flow
    net_cash_flow: float = 0.0
    cum_cash_flow: float = 0.0
    discounted_ncf: float = 0.0
    cum_discounted_ncf: float = 0.0

    # Rates / cumulative
    oil_rate_bopd: float = 0.0
    gas_rate_mcfd: float = 0.0
    cum_oil_mstb: float = 0.0
    cum_gas_mmcf: float = 0.0
    cum_ngl_mstb: float = 0.0


@dataclass
class EconomicResult:
    """Output of economic simulation."""
    propnum: str
    scenario_id: int
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
    monthly: list[MonthlyRow] = field(default_factory=list)


def run_economics(inputs: EconomicInputs) -> EconomicResult:
    """
    Run the full economic simulator for one property/scenario.
    Implements ARIES keyword-driven logic:
      - Decline curves for oil and gas
      - Pricing with differentials and BTU/SHRINK adjustments
      - OPEX (fixed + variable), taxes, CAPEX
      - Economic limit check (LOSS keyword)
      - Chance of success risking (XINVWT)
    """
    monthly = []
    days_per_month = 365.25 / 12.0

    # Build oil DCA
    oil_params = DCAParameters(
        decline_type=DeclineType(inputs.oil_decline_type),
        qi=inputs.oil_qi,
        di=inputs.oil_di,
        b=inputs.oil_b,
        dt=inputs.oil_dt,
        max_months=inputs.max_life_months,
        min_rate=0.0,
    )
    oil_dca = run_dca(oil_params) if inputs.oil_qi > 0 else None

    # Build gas DCA (independent, unless driven by GOR from oil)
    if inputs.gas_qi > 0:
        gas_params = DCAParameters(
            decline_type=DeclineType(inputs.gas_decline_type),
            qi=inputs.gas_qi,
            di=inputs.gas_di,
            b=inputs.gas_b,
            dt=inputs.gas_dt,
            max_months=inputs.max_life_months,
            min_rate=0.0,
        )
        gas_dca = run_dca(gas_params)
    else:
        gas_dca = None

    max_months = inputs.max_life_months
    if oil_dca:
        max_months = min(max_months, oil_dca.producing_months)
    if gas_dca and not (inputs.oil_qi > 0 and inputs.gas_oil_ratio > 0):
        max_months = min(max_months, gas_dca.producing_months)

    cum_cash_flows = []  # For IRR and payout calc
    cum_ncf = 0.0
    cum_disc_ncf = 0.0
    cum_oil = 0.0    # MSTB
    cum_gas = 0.0    # MMCF
    cum_ngl = 0.0    # MSTB

    monthly_disc_rate = (1.0 + inputs.discount_rate) ** (1.0 / 12.0) - 1.0
    monthly_disc_rate_15 = (1.0 + 0.15) ** (1.0 / 12.0) - 1.0
    disc_factor = 1.0
    disc_factor_15 = 1.0
    payout_month = None

    # Initial CAPEX at month 0
    capex_cash_flows = [-inputs.initial_capex]  # For IRR calculation

    for m in range(max_months):
        row = MonthlyRow(
            month=m,
            date=inputs.econ_start_date + relativedelta(months=m),
            year=(inputs.econ_start_date + relativedelta(months=m)).year,
        )

        # ---- Production ----
        if oil_dca and m < len(oil_dca.rates_daily):
            oil_rate = oil_dca.rates_daily[m]
        else:
            oil_rate = 0.0

        # Gas: either from gas DCA or from GOR applied to oil
        if inputs.gas_oil_ratio > 0 and oil_rate > 0:
            gas_rate = oil_rate * inputs.gas_oil_ratio  # MCF/day from GOR
        elif gas_dca and m < len(gas_dca.rates_daily):
            gas_rate = gas_dca.rates_daily[m]
        else:
            gas_rate = 0.0

        # Apply shrinkage to get sales gas
        sales_gas_rate = gas_rate * inputs.shrinkage

        # NGL from gas
        ngl_rate = sales_gas_rate * inputs.ngl_yield / 1000.0  # BBL/day (yield is BBL/MMCF)

        # Monthly volumes (gross WI = 100%)
        gross_oil = oil_rate * days_per_month
        gross_gas = gas_rate * days_per_month / 1000.0 * inputs.shrinkage  # MMCF
        gross_ngl = ngl_rate * days_per_month

        # Net to working interest
        net_oil = gross_oil * inputs.working_interest
        net_gas = gross_gas * inputs.working_interest
        net_ngl = gross_ngl * inputs.working_interest

        row.gross_oil_bbl = gross_oil
        row.gross_gas_mcf = gross_gas * 1000.0   # Back to MCF
        row.gross_ngl_bbl = gross_ngl
        row.net_oil_bbl = net_oil
        row.net_gas_mcf = net_gas * 1000.0
        row.net_ngl_bbl = net_ngl
        row.oil_rate_bopd = oil_rate
        row.gas_rate_mcfd = gas_rate

        # Cumulative volumes
        cum_oil += net_oil / 1000.0     # MSTB
        cum_gas += net_gas              # MMCF
        cum_ngl += net_ngl / 1000.0    # MSTB
        row.cum_oil_mstb = cum_oil
        row.cum_gas_mmcf = cum_gas
        row.cum_ngl_mstb = cum_ngl

        # ---- Pricing ----
        # Price escalation
        years_elapsed = m / 12.0
        oil_px = (inputs.oil_price + inputs.oil_price_diff) * (1.0 + inputs.oil_price_escalation / 100.0) ** years_elapsed
        gas_px = (inputs.gas_price + inputs.gas_price_diff) * inputs.btu_factor * (1.0 + inputs.gas_price_escalation / 100.0) ** years_elapsed
        ngl_px = inputs.oil_price * inputs.ngl_price_pct

        # Revenue (net to NRI)
        oil_rev = net_oil * inputs.net_revenue_interest * oil_px
        gas_rev = net_gas * 1000.0 * inputs.net_revenue_interest * gas_px
        ngl_rev = net_ngl * inputs.net_revenue_interest * ngl_px
        total_rev = oil_rev + gas_rev + ngl_rev

        row.oil_revenue = oil_rev
        row.gas_revenue = gas_rev
        row.ngl_revenue = ngl_rev
        row.total_revenue = total_rev

        # ---- Costs ----
        prod_tax = total_rev * inputs.tax_rate
        ad_val = total_rev * inputs.ad_valorem_rate
        var_opex = (net_oil * inputs.variable_oil_opex) + (net_gas * 1000.0 * inputs.variable_gas_opex)
        fixed_opex = (inputs.fixed_opex + inputs.overhead) * inputs.working_interest
        total_opex = fixed_opex + var_opex
        capex = 0.0  # Initial CAPEX is separate; future CAPEX from schedule not yet implemented

        row.prod_taxes = prod_tax
        row.ad_valorem = ad_val
        row.opex = total_opex
        row.capex = capex

        # ---- Net Cash Flow ----
        ncf = total_rev - prod_tax - ad_val - total_opex - capex
        ncf *= inputs.chance_of_success  # XINVWT risking

        # Economic limit check (LOSS keyword)
        if inputs.apply_economic_limit:
            if inputs.econ_limit_type == "NET_REVENUE" and ncf < inputs.econ_limit_value:
                break
            elif inputs.econ_limit_type == "OIL_RATE" and oil_rate < inputs.econ_limit_value:
                break
            elif inputs.econ_limit_type == "GAS_RATE" and gas_rate < inputs.econ_limit_value:
                break

        row.net_cash_flow = ncf
        cum_ncf += ncf
        row.cum_cash_flow = cum_ncf

        # Payout calculation
        if payout_month is None and cum_ncf >= inputs.initial_capex:
            payout_month = m + 1

        # Discounted NCF
        row.discounted_ncf = ncf * disc_factor
        cum_disc_ncf += row.discounted_ncf
        row.cum_discounted_ncf = cum_disc_ncf

        disc_factor /= (1.0 + monthly_disc_rate)

        capex_cash_flows.append(ncf)
        monthly.append(row)

    # Add abandonment cost at end
    if monthly:
        monthly[-1].capex += inputs.abandonment_cost
        monthly[-1].net_cash_flow -= inputs.abandonment_cost
        monthly[-1].cum_cash_flow -= inputs.abandonment_cost

    # NPV10 = sum of discounted NCF - initial capex
    npv10 = cum_disc_ncf - inputs.initial_capex

    # NPV15
    disc_15 = 1.0
    npv15_sum = 0.0
    for row in monthly:
        npv15_sum += row.net_cash_flow * disc_15
        disc_15 /= (1.0 + monthly_disc_rate_15)
    npv15 = npv15_sum - inputs.initial_capex

    # IRR calculation (Newton-Raphson on NPV = 0)
    irr = _calculate_irr(capex_cash_flows)

    return EconomicResult(
        propnum=inputs.propnum,
        scenario_id=inputs.scenario_id,
        npv10=round(npv10, 2),
        npv15=round(npv15, 2),
        irr=irr,
        payout_months=payout_month,
        total_revenue=sum(r.total_revenue for r in monthly),
        total_opex=sum(r.opex for r in monthly),
        total_capex=inputs.initial_capex,
        cum_oil_mstb=monthly[-1].cum_oil_mstb if monthly else 0.0,
        cum_gas_mmcf=monthly[-1].cum_gas_mmcf if monthly else 0.0,
        cum_ngl_mstb=monthly[-1].cum_ngl_mstb if monthly else 0.0,
        monthly=monthly,
    )


def _calculate_irr(cash_flows: list[float], guess: float = 0.1, max_iter: int = 1000) -> Optional[float]:
    """
    Calculate IRR using Newton-Raphson method.
    Returns annual IRR as decimal (0.15 = 15%), or None if no solution.
    """
    if not cash_flows or cash_flows[0] >= 0:
        return None

    rate = guess
    for _ in range(max_iter):
        npv = sum(cf / (1.0 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1.0 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-12:
            break
        rate -= npv / dnpv
        if rate <= -1.0:
            return None
        if abs(npv) < 1e-6:
            break

    # Convert monthly rate to annual
    annual_rate = (1.0 + rate) ** 12 - 1.0
    if annual_rate < -1.0 or annual_rate > 100.0:
        return None
    return round(annual_rate * 100, 2)  # Return as percentage
