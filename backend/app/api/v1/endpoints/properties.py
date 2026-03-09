"""Properties API — CRUD for AC_PROPERTY."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.base import get_db
from app.schemas.property import ACPropertyCreate, ACPropertyUpdate, ACPropertyResponse, ACPropertyList
from app.services import property_service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("/", response_model=ACPropertyList)
async def list_properties(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    well_type: Optional[str] = None,
    state: Optional[str] = None,
    basin: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = await property_service.get_properties(
        db, skip=skip, limit=size,
        search=search, well_type=well_type,
        state=state, basin=basin, status=status,
    )
    return ACPropertyList(items=items, total=total, page=page, size=size)


@router.get("/{propnum}", response_model=ACPropertyResponse)
async def get_property(propnum: str, db: AsyncSession = Depends(get_db)):
    prop = await property_service.get_property(db, propnum)
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property {propnum} not found")
    return prop


@router.post("/", response_model=ACPropertyResponse, status_code=201)
async def create_property(prop_in: ACPropertyCreate, db: AsyncSession = Depends(get_db)):
    existing = await property_service.get_property(db, prop_in.propnum)
    if existing:
        raise HTTPException(status_code=409, detail=f"Property {prop_in.propnum} already exists")
    return await property_service.create_property(db, prop_in)


@router.put("/{propnum}", response_model=ACPropertyResponse)
async def update_property(propnum: str, prop_in: ACPropertyUpdate, db: AsyncSession = Depends(get_db)):
    prop = await property_service.update_property(db, propnum, prop_in)
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property {propnum} not found")
    return prop


@router.delete("/{propnum}", status_code=204)
async def delete_property(propnum: str, db: AsyncSession = Depends(get_db)):
    deleted = await property_service.delete_property(db, propnum)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Property {propnum} not found")


@router.post("/bulk-import", response_model=list[ACPropertyResponse])
async def bulk_import(properties: list[ACPropertyCreate], db: AsyncSession = Depends(get_db)):
    return await property_service.bulk_import_properties(db, properties)
