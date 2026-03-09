"""Production history API."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import csv
import io
from datetime import date

from app.db.base import get_db
from app.models.production import ACProduct
from app.schemas.production import ACProductCreate, ACProductResponse

router = APIRouter(prefix="/production", tags=["Production"])


@router.get("/{propnum}", response_model=list[ACProductResponse])
async def get_production_history(
    propnum: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ACProduct).where(ACProduct.propnum == propnum)
    if start_date:
        query = query.where(ACProduct.prod_date >= start_date)
    if end_date:
        query = query.where(ACProduct.prod_date <= end_date)
    query = query.order_by(ACProduct.prod_date)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=ACProductResponse, status_code=201)
async def add_production_record(record: ACProductCreate, db: AsyncSession = Depends(get_db)):
    db_record = ACProduct(
        propnum=record.propnum,
        prod_date=record.prod_date,
        prod_year=record.prod_date.year,
        prod_month=record.prod_date.month,
        days_on=record.days_on,
        gross_oil_bbl=record.gross_oil_bbl,
        gross_gas_mcf=record.gross_gas_mcf,
        gross_ngl_bbl=record.gross_ngl_bbl,
        gross_water_bbl=record.gross_water_bbl,
        net_oil_bbl=record.net_oil_bbl,
        net_gas_mcf=record.net_gas_mcf,
        net_ngl_bbl=record.net_ngl_bbl,
        oil_rate_bopd=record.oil_rate_bopd,
        gas_rate_mcfd=record.gas_rate_mcfd,
        data_source=record.data_source,
        is_estimated=record.is_estimated,
    )
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)
    return db_record


@router.post("/{propnum}/bulk-upload")
async def upload_production_csv(
    propnum: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload production history CSV.
    Expected columns: date (YYYY-MM-DD), oil_bbl, gas_mcf, water_bbl, days_on
    """
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    errors = []
    for i, row in enumerate(reader):
        try:
            prod_date = date.fromisoformat(row.get("date", "").strip())
            db_record = ACProduct(
                propnum=propnum,
                prod_date=prod_date,
                prod_year=prod_date.year,
                prod_month=prod_date.month,
                days_on=float(row.get("days_on", 30)),
                gross_oil_bbl=float(row.get("oil_bbl", 0)),
                gross_gas_mcf=float(row.get("gas_mcf", 0)),
                gross_water_bbl=float(row.get("water_bbl", 0)),
                data_source="CSV_UPLOAD",
            )
            db.add(db_record)
            imported += 1
        except Exception as e:
            errors.append({"row": i + 2, "error": str(e)})

    await db.commit()
    return {"imported": imported, "errors": errors}
