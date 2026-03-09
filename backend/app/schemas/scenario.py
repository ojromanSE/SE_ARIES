from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ACScenarioBase(BaseModel):
    scenario_name: str
    scenario_code: Optional[str] = None
    description: Optional[str] = None
    scenario_type: str = "ECONOMIC"
    oil_price: Optional[float] = None
    gas_price: Optional[float] = None
    ngl_price: Optional[float] = None
    oil_price_escalation: float = 0.0
    gas_price_escalation: float = 0.0
    price_deck: Optional[list[dict]] = None
    discount_rate: float = 10.0
    tax_rate: float = 0.0
    ad_valorem_rate: float = 0.0
    chance_of_success: float = 1.0
    apply_economic_limit: bool = True
    econ_start_date: Optional[datetime] = None
    max_life_years: float = 40.0
    is_base_case: bool = False


class ACScenarioCreate(ACScenarioBase):
    project_id: int


class ACScenarioUpdate(ACScenarioBase):
    scenario_name: Optional[str] = None


class ACScenarioResponse(ACScenarioBase):
    id: int
    project_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
