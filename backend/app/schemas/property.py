from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ACPropertyBase(BaseModel):
    propname: Optional[str] = None
    api_num: Optional[str] = None
    uwi: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    field: Optional[str] = None
    formation: Optional[str] = None
    basin: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    well_type: Optional[str] = "OIL"
    prop_type: Optional[str] = "PRODUCING"
    entity_type: Optional[str] = "WELL"
    working_interest: float = 1.0
    net_revenue_interest: float = 1.0
    royalty_interest: float = 0.0
    overriding_royalty: float = 0.0
    operator: Optional[str] = None
    spud_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    first_prod_date: Optional[datetime] = None
    currency: str = "USD"
    volume_unit: str = "BBL"
    status: str = "ACTIVE"
    notes: Optional[str] = None
    user_defined_1: Optional[str] = None
    user_defined_2: Optional[str] = None
    user_defined_3: Optional[float] = None


class ACPropertyCreate(ACPropertyBase):
    propnum: str = Field(..., min_length=1, max_length=20, description="Unique property number")


class ACPropertyUpdate(ACPropertyBase):
    pass


class ACPropertyResponse(ACPropertyBase):
    propnum: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ACPropertyList(BaseModel):
    items: list[ACPropertyResponse]
    total: int
    page: int
    size: int
