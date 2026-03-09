from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ACProductCreate(BaseModel):
    propnum: str
    prod_date: date
    days_on: float = 30.0
    gross_oil_bbl: float = 0.0
    gross_gas_mcf: float = 0.0
    gross_ngl_bbl: float = 0.0
    gross_water_bbl: float = 0.0
    net_oil_bbl: float = 0.0
    net_gas_mcf: float = 0.0
    net_ngl_bbl: float = 0.0
    oil_rate_bopd: float = 0.0
    gas_rate_mcfd: float = 0.0
    data_source: Optional[str] = None
    is_estimated: bool = False


class ACProductResponse(ACProductCreate):
    id: int
    prod_year: int
    prod_month: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ACProductForecastResponse(BaseModel):
    id: int
    propnum: str
    scenario_id: int
    forecast_date: date
    forecast_year: int
    forecast_month: int
    gross_oil_bbl: float
    gross_gas_mcf: float
    gross_ngl_bbl: float
    net_oil_bbl: float
    net_gas_mcf: float
    net_ngl_bbl: float
    oil_revenue: float
    gas_revenue: float
    ngl_revenue: float
    total_revenue: float
    opex: float
    capex: float
    taxes: float
    net_cash_flow: float
    cum_cash_flow: float
    discounted_ncf: float
    oil_rate_bopd: float
    gas_rate_mcfd: float
    cum_oil_mstb: float
    cum_gas_mmcf: float

    class Config:
        from_attributes = True
