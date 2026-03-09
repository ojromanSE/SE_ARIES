"""
Economic service — bridges API layer with the economic simulator.
Runs the simulator and persists results to AC_ECONOMIC and AC_PRODUCT_FORECAST.
"""
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional

from app.models.economic import ACEconomic
from app.models.production import ACProductForecast
from app.models.scenario import ACScenario
from app.schemas.economic import ACEconomicCreate, ACEconomicUpdate, EconRunResult
from app.services.economics import EconomicInputs, run_economics
from app.services.project_service import get_scenario


async def get_economic(db: AsyncSession, propnum: str, scenario_id: int) -> Optional[ACEconomic]:
    result = await db.execute(
        select(ACEconomic).where(
            ACEconomic.propnum == propnum,
            ACEconomic.scenario_id == scenario_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_economic(
    db: AsyncSession, econ_in: ACEconomicCreate
) -> ACEconomic:
    existing = await get_economic(db, econ_in.propnum, econ_in.scenario_id)
    if existing:
        for field, value in econ_in.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        existing.run_status = "PENDING"
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        db_econ = ACEconomic(**econ_in.model_dump(), run_status="PENDING")
        db.add(db_econ)
        await db.commit()
        await db.refresh(db_econ)
        return db_econ


async def run_econ_simulation(
    db: AsyncSession, propnum: str, scenario_id: int
) -> EconRunResult:
    """
    Runs the full economic simulation for a property/scenario.
    Persists results to AC_ECONOMIC (summary) and AC_PRODUCT_FORECAST (monthly).
    """
    # Load economic inputs
    econ = await get_economic(db, propnum, scenario_id)
    if not econ:
        raise ValueError(f"No economic inputs found for {propnum} / scenario {scenario_id}")

    scenario = await get_scenario(db, scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    # Load property for WI/NRI
    from app.models.property import ACProperty
    prop_result = await db.execute(
        select(ACProperty).where(ACProperty.propnum == propnum)
    )
    prop = prop_result.scalar_one_or_none()
    if not prop:
        raise ValueError(f"Property {propnum} not found")

    # Build economic inputs
    econ_start = scenario.econ_start_date or datetime.utcnow()
    if isinstance(econ_start, datetime):
        econ_start = econ_start.date()

    inputs = EconomicInputs(
        propnum=propnum,
        scenario_id=scenario_id,
        econ_start_date=econ_start,
        # Scenario-level
        oil_price=scenario.oil_price or 70.0,
        gas_price=scenario.gas_price or 3.0,
        ngl_price_pct=econ.ngl_price_pct,
        discount_rate=scenario.discount_rate / 100.0,
        tax_rate=scenario.tax_rate,
        ad_valorem_rate=scenario.ad_valorem_rate,
        chance_of_success=scenario.chance_of_success,
        apply_economic_limit=scenario.apply_economic_limit,
        # Property ownership
        working_interest=prop.working_interest,
        net_revenue_interest=prop.net_revenue_interest,
        # Decline curves
        oil_decline_type=econ.oil_decline_type,
        oil_qi=econ.oil_initial_rate or 0.0,
        oil_di=econ.oil_decline_rate or 0.0,
        oil_b=econ.oil_b_factor,
        oil_dt=econ.oil_terminal_decline,
        gas_decline_type=econ.gas_decline_type,
        gas_qi=econ.gas_initial_rate or 0.0,
        gas_di=econ.gas_decline_rate or 0.0,
        gas_b=econ.gas_b_factor,
        gas_dt=econ.gas_terminal_decline,
        shrinkage=econ.shrinkage,
        btu_factor=econ.btu_factor,
        ngl_yield=econ.ngl_yield,
        gas_oil_ratio=econ.gas_oil_ratio,
        # Pricing adjustments
        oil_price_diff=econ.oil_price_diff,
        gas_price_diff=econ.gas_price_diff,
        # OPEX
        fixed_opex=econ.fixed_opex,
        variable_oil_opex=econ.variable_oil_opex,
        variable_gas_opex=econ.variable_gas_opex,
        overhead=econ.overhead,
        # CAPEX
        initial_capex=econ.capex,
        abandonment_cost=econ.abandonment_cost,
        # Economic limit
        econ_limit_type=econ.economic_limit_type,
        econ_limit_value=econ.economic_limit_value,
        max_life_months=econ.max_life_months or 480,
        oil_price_escalation=scenario.oil_price_escalation,
        gas_price_escalation=scenario.gas_price_escalation,
    )

    result = run_economics(inputs)

    # Persist summary to AC_ECONOMIC
    econ.npv10 = result.npv10
    econ.npv15 = result.npv15
    econ.irr = result.irr
    econ.payout_months = result.payout_months
    econ.total_capex = result.total_capex
    econ.total_opex = result.total_opex
    econ.total_revenue = result.total_revenue
    econ.cum_oil_mstb = result.cum_oil_mstb
    econ.cum_gas_mmcf = result.cum_gas_mmcf
    econ.cum_ngl_mstb = result.cum_ngl_mstb
    econ.last_run_at = datetime.utcnow()
    econ.run_status = "SUCCESS"

    # Clear old forecast and persist new monthly rows
    await db.execute(
        delete(ACProductForecast).where(
            ACProductForecast.propnum == propnum,
            ACProductForecast.scenario_id == scenario_id,
        )
    )

    for row in result.monthly:
        fc = ACProductForecast(
            propnum=propnum,
            scenario_id=scenario_id,
            forecast_date=row.date,
            forecast_year=row.year,
            forecast_month=row.date.month,
            gross_oil_bbl=row.gross_oil_bbl,
            gross_gas_mcf=row.gross_gas_mcf,
            gross_ngl_bbl=row.gross_ngl_bbl,
            net_oil_bbl=row.net_oil_bbl,
            net_gas_mcf=row.net_gas_mcf,
            net_ngl_bbl=row.net_ngl_bbl,
            oil_revenue=row.oil_revenue,
            gas_revenue=row.gas_revenue,
            ngl_revenue=row.ngl_revenue,
            total_revenue=row.total_revenue,
            opex=row.opex,
            capex=row.capex,
            taxes=row.prod_taxes + row.ad_valorem,
            net_cash_flow=row.net_cash_flow,
            cum_cash_flow=row.cum_cash_flow,
            discounted_ncf=row.discounted_ncf,
            oil_rate_bopd=row.oil_rate_bopd,
            gas_rate_mcfd=row.gas_rate_mcfd,
            cum_oil_mstb=row.cum_oil_mstb,
            cum_gas_mmcf=row.cum_gas_mmcf,
        )
        db.add(fc)

    await db.commit()
    await db.refresh(econ)

    return EconRunResult(
        propnum=propnum,
        scenario_id=scenario_id,
        npv10=result.npv10,
        npv15=result.npv15,
        irr=result.irr,
        payout_months=result.payout_months,
        total_capex=result.total_capex,
        total_opex=result.total_opex,
        total_revenue=result.total_revenue,
        cum_oil_mstb=result.cum_oil_mstb,
        cum_gas_mmcf=result.cum_gas_mmcf,
        cum_ngl_mstb=result.cum_ngl_mstb,
        monthly_forecast=[
            {
                "month": r.month,
                "date": r.date.isoformat(),
                "oil_rate_bopd": r.oil_rate_bopd,
                "gas_rate_mcfd": r.gas_rate_mcfd,
                "gross_oil_bbl": r.gross_oil_bbl,
                "gross_gas_mcf": r.gross_gas_mcf,
                "total_revenue": r.total_revenue,
                "opex": r.opex,
                "net_cash_flow": r.net_cash_flow,
                "cum_cash_flow": r.cum_cash_flow,
                "discounted_ncf": r.discounted_ncf,
                "cum_oil_mstb": r.cum_oil_mstb,
                "cum_gas_mmcf": r.cum_gas_mmcf,
            }
            for r in result.monthly
        ],
    )
