"""CRUD service for AC_PROPERTY."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from app.models.property import ACProperty
from app.schemas.property import ACPropertyCreate, ACPropertyUpdate


async def get_property(db: AsyncSession, propnum: str) -> Optional[ACProperty]:
    result = await db.execute(select(ACProperty).where(ACProperty.propnum == propnum))
    return result.scalar_one_or_none()


async def get_properties(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    well_type: Optional[str] = None,
    state: Optional[str] = None,
    basin: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[list[ACProperty], int]:
    query = select(ACProperty)
    count_query = select(func.count()).select_from(ACProperty)

    filters = []
    if search:
        filters.append(
            or_(
                ACProperty.propnum.ilike(f"%{search}%"),
                ACProperty.propname.ilike(f"%{search}%"),
                ACProperty.api_num.ilike(f"%{search}%"),
                ACProperty.field.ilike(f"%{search}%"),
            )
        )
    if well_type:
        filters.append(ACProperty.well_type == well_type)
    if state:
        filters.append(ACProperty.state == state)
    if basin:
        filters.append(ACProperty.basin == basin)
    if status:
        filters.append(ACProperty.status == status)

    if filters:
        from sqlalchemy import and_
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = await db.execute(count_query)
    total_count = total.scalar()

    query = query.order_by(ACProperty.propname).offset(skip).limit(limit)
    result = await db.execute(query)
    properties = result.scalars().all()

    return list(properties), total_count


async def create_property(
    db: AsyncSession, prop_in: ACPropertyCreate, created_by: Optional[str] = None
) -> ACProperty:
    db_prop = ACProperty(**prop_in.model_dump(), created_by=created_by)
    db.add(db_prop)
    await db.commit()
    await db.refresh(db_prop)
    return db_prop


async def update_property(
    db: AsyncSession, propnum: str, prop_in: ACPropertyUpdate
) -> Optional[ACProperty]:
    db_prop = await get_property(db, propnum)
    if not db_prop:
        return None
    update_data = prop_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_prop, field, value)
    await db.commit()
    await db.refresh(db_prop)
    return db_prop


async def delete_property(db: AsyncSession, propnum: str) -> bool:
    db_prop = await get_property(db, propnum)
    if not db_prop:
        return False
    await db.delete(db_prop)
    await db.commit()
    return True


async def bulk_import_properties(
    db: AsyncSession, properties: list[ACPropertyCreate], created_by: Optional[str] = None
) -> list[ACProperty]:
    """Bulk import properties — skips duplicates."""
    created = []
    for prop_in in properties:
        existing = await get_property(db, prop_in.propnum)
        if not existing:
            db_prop = ACProperty(**prop_in.model_dump(), created_by=created_by)
            db.add(db_prop)
            created.append(db_prop)
    await db.commit()
    for p in created:
        await db.refresh(p)
    return created
