"""Projects & Scenarios API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.project import ACProjectCreate, ACProjectUpdate, ACProjectResponse
from app.schemas.scenario import ACScenarioCreate, ACScenarioUpdate, ACScenarioResponse
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


# ---- Projects ----

@router.get("/", response_model=list[ACProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    return await project_service.get_projects(db)


@router.get("/{project_id}", response_model=ACProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=ACProjectResponse, status_code=201)
async def create_project(project_in: ACProjectCreate, db: AsyncSession = Depends(get_db)):
    return await project_service.create_project(db, project_in)


@router.put("/{project_id}", response_model=ACProjectResponse)
async def update_project(project_id: int, project_in: ACProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await project_service.update_project(db, project_id, project_in)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await project_service.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{project_id}/properties")
async def get_project_properties(project_id: int, db: AsyncSession = Depends(get_db)):
    return {"project_id": project_id, "propnums": await project_service.get_project_properties(db, project_id)}


@router.post("/{project_id}/properties/{propnum}")
async def add_property_to_project(
    project_id: int, propnum: str, weight_factor: float = 1.0, db: AsyncSession = Depends(get_db)
):
    success = await project_service.add_property_to_project(db, project_id, propnum, weight_factor)
    if not success:
        raise HTTPException(status_code=409, detail="Property already in project or not found")
    return {"message": f"Added {propnum} to project {project_id}"}


@router.delete("/{project_id}/properties/{propnum}", status_code=204)
async def remove_property_from_project(project_id: int, propnum: str, db: AsyncSession = Depends(get_db)):
    await project_service.remove_property_from_project(db, project_id, propnum)


# ---- Scenarios (nested under projects) ----

@router.get("/{project_id}/scenarios", response_model=list[ACScenarioResponse])
async def list_scenarios(project_id: int, db: AsyncSession = Depends(get_db)):
    return await project_service.get_scenarios_for_project(db, project_id)


@router.post("/{project_id}/scenarios", response_model=ACScenarioResponse, status_code=201)
async def create_scenario(project_id: int, scenario_in: ACScenarioCreate, db: AsyncSession = Depends(get_db)):
    scenario_in.project_id = project_id
    return await project_service.create_scenario(db, scenario_in)


@router.put("/scenarios/{scenario_id}", response_model=ACScenarioResponse)
async def update_scenario(scenario_id: int, scenario_in: ACScenarioUpdate, db: AsyncSession = Depends(get_db)):
    scenario = await project_service.update_scenario(db, scenario_id, scenario_in)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    await project_service.delete_scenario(db, scenario_id)
