"""CRUD service for AC_PROJECT and AC_SCENARIO."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.models.project import ACProject, project_property
from app.models.scenario import ACScenario
from app.schemas.project import ACProjectCreate, ACProjectUpdate
from app.schemas.scenario import ACScenarioCreate, ACScenarioUpdate


# ---- PROJECT ----

async def get_project(db: AsyncSession, project_id: int) -> Optional[ACProject]:
    result = await db.execute(select(ACProject).where(ACProject.id == project_id))
    return result.scalar_one_or_none()


async def get_projects(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[ACProject]:
    result = await db.execute(
        select(ACProject).where(ACProject.is_active == True).order_by(ACProject.project_name).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def create_project(
    db: AsyncSession, project_in: ACProjectCreate, created_by: Optional[str] = None
) -> ACProject:
    db_project = ACProject(**project_in.model_dump(), created_by=created_by)
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def update_project(
    db: AsyncSession, project_id: int, project_in: ACProjectUpdate
) -> Optional[ACProject]:
    db_project = await get_project(db, project_id)
    if not db_project:
        return None
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(db_project, field, value)
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    db_project = await get_project(db, project_id)
    if not db_project:
        return False
    db_project.is_active = False
    await db.commit()
    return True


async def add_property_to_project(
    db: AsyncSession, project_id: int, propnum: str, weight_factor: float = 1.0
) -> bool:
    stmt = project_property.insert().values(
        project_id=project_id, propnum=propnum, weight_factor=weight_factor
    )
    try:
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False


async def remove_property_from_project(
    db: AsyncSession, project_id: int, propnum: str
) -> bool:
    stmt = project_property.delete().where(
        project_property.c.project_id == project_id,
        project_property.c.propnum == propnum
    )
    await db.execute(stmt)
    await db.commit()
    return True


async def get_project_properties(db: AsyncSession, project_id: int) -> list[str]:
    result = await db.execute(
        select(project_property.c.propnum).where(project_property.c.project_id == project_id)
    )
    return [row[0] for row in result.fetchall()]


# ---- SCENARIO ----

async def get_scenario(db: AsyncSession, scenario_id: int) -> Optional[ACScenario]:
    result = await db.execute(select(ACScenario).where(ACScenario.id == scenario_id))
    return result.scalar_one_or_none()


async def get_scenarios_for_project(db: AsyncSession, project_id: int) -> list[ACScenario]:
    result = await db.execute(
        select(ACScenario)
        .where(ACScenario.project_id == project_id, ACScenario.is_active == True)
        .order_by(ACScenario.scenario_name)
    )
    return list(result.scalars().all())


async def create_scenario(db: AsyncSession, scenario_in: ACScenarioCreate) -> ACScenario:
    db_scenario = ACScenario(**scenario_in.model_dump())
    db.add(db_scenario)
    await db.commit()
    await db.refresh(db_scenario)
    return db_scenario


async def update_scenario(
    db: AsyncSession, scenario_id: int, scenario_in: ACScenarioUpdate
) -> Optional[ACScenario]:
    db_scenario = await get_scenario(db, scenario_id)
    if not db_scenario:
        return None
    for field, value in scenario_in.model_dump(exclude_unset=True).items():
        setattr(db_scenario, field, value)
    await db.commit()
    await db.refresh(db_scenario)
    return db_scenario


async def delete_scenario(db: AsyncSession, scenario_id: int) -> bool:
    db_scenario = await get_scenario(db, scenario_id)
    if not db_scenario:
        return False
    db_scenario.is_active = False
    await db.commit()
    return True
