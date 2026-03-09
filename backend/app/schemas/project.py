from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ACProjectBase(BaseModel):
    project_name: str
    project_code: Optional[str] = None
    description: Optional[str] = None
    project_type: str = "WORKING"
    parent_project_id: Optional[int] = None
    default_scenario: Optional[str] = None
    consolidation_method: str = "SUM"
    default_discount_rate: float = 10.0
    econ_start_date: Optional[datetime] = None
    econ_end_date: Optional[datetime] = None


class ACProjectCreate(ACProjectBase):
    pass


class ACProjectUpdate(ACProjectBase):
    project_name: Optional[str] = None


class ACProjectResponse(ACProjectBase):
    id: int
    is_active: bool
    is_locked: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
