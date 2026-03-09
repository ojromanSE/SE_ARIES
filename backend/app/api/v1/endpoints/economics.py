"""Economics API — inputs, simulation runner, and results."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.economic import ACEconomicCreate, ACEconomicUpdate, ACEconomicResponse, EconRunResult
from app.services.econ_service import get_economic, upsert_economic, run_econ_simulation

router = APIRouter(prefix="/economics", tags=["Economics"])


@router.get("/{propnum}/{scenario_id}", response_model=ACEconomicResponse)
async def get_economic_inputs(propnum: str, scenario_id: int, db: AsyncSession = Depends(get_db)):
    econ = await get_economic(db, propnum, scenario_id)
    if not econ:
        raise HTTPException(status_code=404, detail="Economic inputs not found")
    return econ


@router.post("/", response_model=ACEconomicResponse, status_code=201)
async def save_economic_inputs(econ_in: ACEconomicCreate, db: AsyncSession = Depends(get_db)):
    return await upsert_economic(db, econ_in)


@router.put("/{propnum}/{scenario_id}", response_model=ACEconomicResponse)
async def update_economic_inputs(
    propnum: str, scenario_id: int, econ_in: ACEconomicUpdate, db: AsyncSession = Depends(get_db)
):
    from app.schemas.economic import ACEconomicCreate
    create_schema = ACEconomicCreate(propnum=propnum, scenario_id=scenario_id, **econ_in.model_dump())
    return await upsert_economic(db, create_schema)


@router.post("/{propnum}/{scenario_id}/run", response_model=EconRunResult)
async def run_simulation(propnum: str, scenario_id: int, db: AsyncSession = Depends(get_db)):
    """
    Run the economic simulator for a property/scenario.
    Calculates NPV, IRR, cash flows, and stores monthly forecast in AC_PRODUCT_FORECAST.
    """
    try:
        return await run_econ_simulation(db, propnum, scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{propnum}/{scenario_id}/forecast")
async def get_forecast(propnum: str, scenario_id: int, db: AsyncSession = Depends(get_db)):
    """Return stored monthly forecast for a property/scenario."""
    from sqlalchemy import select
    from app.models.production import ACProductForecast
    result = await db.execute(
        select(ACProductForecast)
        .where(
            ACProductForecast.propnum == propnum,
            ACProductForecast.scenario_id == scenario_id,
        )
        .order_by(ACProductForecast.forecast_date)
    )
    rows = result.scalars().all()
    return [
        {
            "date": r.forecast_date.isoformat(),
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
        for r in rows
    ]
