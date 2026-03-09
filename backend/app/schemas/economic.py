from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ACEconomicBase(BaseModel):
    # Decline curve
    oil_decline_type: str = "EXP"
    oil_initial_rate: Optional[float] = None
    oil_decline_rate: Optional[float] = None
    oil_b_factor: float = 0.0
    oil_terminal_decline: Optional[float] = None
    oil_eur: Optional[float] = None

    gas_decline_type: str = "EXP"
    gas_initial_rate: Optional[float] = None
    gas_decline_rate: Optional[float] = None
    gas_b_factor: float = 0.0
    gas_terminal_decline: Optional[float] = None
    gas_eur: Optional[float] = None

    ngl_yield: float = 0.0
    shrinkage: float = 1.0
    btu_factor: float = 1.0
    water_oil_ratio: float = 0.0
    gas_oil_ratio: float = 0.0

    # Pricing
    oil_price_diff: float = 0.0
    gas_price_diff: float = 0.0
    ngl_price_pct: float = 0.4

    # OPEX
    fixed_opex: float = 0.0
    variable_oil_opex: float = 0.0
    variable_gas_opex: float = 0.0
    overhead: float = 0.0
    workovers: float = 0.0

    # CAPEX
    capex: float = 0.0
    capex_date: Optional[datetime] = None
    abandonment_cost: float = 0.0
    capex_schedule: Optional[list[dict]] = None

    # Economic limit
    economic_limit_type: str = "NET_REVENUE"
    economic_limit_value: float = 0.0
    max_life_months: Optional[int] = None

    keyword_text: Optional[str] = None


class ACEconomicCreate(ACEconomicBase):
    propnum: str
    scenario_id: int


class ACEconomicUpdate(ACEconomicBase):
    pass


class ACEconomicResponse(ACEconomicBase):
    id: int
    propnum: str
    scenario_id: int
    npv10: Optional[float] = None
    npv15: Optional[float] = None
    irr: Optional[float] = None
    payout_months: Optional[float] = None
    total_capex: Optional[float] = None
    total_opex: Optional[float] = None
    total_revenue: Optional[float] = None
    cum_oil_mstb: Optional[float] = None
    cum_gas_mmcf: Optional[float] = None
    cum_ngl_mstb: Optional[float] = None
    last_run_at: Optional[datetime] = None
    run_status: str = "PENDING"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EconRunResult(BaseModel):
    """Result from running the economic simulator."""
    propnum: str
    scenario_id: int
    npv10: float
    npv15: float
    irr: Optional[float]
    payout_months: Optional[float]
    total_capex: float
    total_opex: float
    total_revenue: float
    cum_oil_mstb: float
    cum_gas_mmcf: float
    cum_ngl_mstb: float
    monthly_forecast: list[dict]
