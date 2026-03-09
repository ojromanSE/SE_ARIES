"""
Seed demo data — creates sample Permian Basin wells with production history.
Run: cd backend && python ../scripts/seed_demo_data.py
"""
import asyncio
import sys
import os
import random
from datetime import date
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.base import init_db, AsyncSessionLocal
from app.models.property import ACProperty
from app.models.project import ACProject
from app.models.scenario import ACScenario
from app.models.economic import ACEconomic
from app.models.production import ACProduct


WELLS = [
    {"propnum": "PB-001", "propname": "Smith Unit 1H", "api": "42-003-12345-0000", "field": "Midland", "state": "TX", "county": "Midland", "basin": "Permian", "qi_oil": 850, "qi_gas": 1200, "di": 0.65, "b": 1.5},
    {"propnum": "PB-002", "propname": "Jones State 2H", "api": "42-227-23456-0000", "field": "Wolfcamp", "state": "TX", "county": "Martin", "basin": "Permian", "qi_oil": 1100, "qi_gas": 2500, "di": 0.72, "b": 1.3},
    {"propnum": "PB-003", "propname": "Williams Federal 1H", "api": "42-109-34567-0000", "field": "Delaware", "state": "TX", "county": "Ector", "basin": "Permian", "qi_oil": 650, "qi_gas": 900, "di": 0.55, "b": 1.2},
    {"propnum": "PB-004", "propname": "Garcia Lease 5H", "api": "42-003-45678-0000", "field": "Spraberry", "state": "TX", "county": "Midland", "basin": "Permian", "qi_oil": 920, "qi_gas": 3200, "di": 0.68, "b": 1.4},
    {"propnum": "PB-005", "propname": "Eagle Ford 1H", "api": "42-149-56789-0000", "field": "Eagle Ford", "state": "TX", "county": "Gonzales", "basin": "Gulf Coast", "qi_oil": 500, "qi_gas": 800, "di": 0.50, "b": 1.1},
    {"propnum": "EF-001", "propname": "Karnes State 3H", "api": "42-149-67890-0000", "field": "Eagle Ford", "state": "TX", "county": "Karnes", "basin": "Gulf Coast", "qi_oil": 430, "qi_gas": 1500, "di": 0.45, "b": 1.0},
]


def hyperbolic_rate(qi: float, di: float, b: float, t_months: int) -> float:
    t_years = t_months / 12.0
    if b < 0.01:
        import math
        return qi * math.exp(-di * t_years)
    return qi / (1.0 + b * di * t_years) ** (1.0 / b)


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Create a project
        project = ACProject(
            project_name="Permian Basin Demo",
            project_code="PB-DEMO",
            description="Demo project with sample Permian Basin wells",
            default_discount_rate=10.0,
            created_by="seed_script",
        )
        db.add(project)
        await db.flush()

        # Create a scenario
        scenario = ACScenario(
            project_id=project.id,
            scenario_name="Base Case",
            scenario_code="BASE",
            oil_price=70.0,
            gas_price=3.00,
            discount_rate=10.0,
            tax_rate=0.05,
            ad_valorem_rate=0.02,
            apply_economic_limit=True,
            econ_start_date=date.today().replace(day=1),
            is_base_case=True,
        )
        db.add(scenario)
        await db.flush()

        for well in WELLS:
            # Property
            prop = ACProperty(
                propnum=well["propnum"],
                propname=well["propname"],
                api_num=well["api"],
                state=well["state"],
                county=well["county"],
                field=well["field"],
                basin=well["basin"],
                well_type="OIL",
                working_interest=1.0,
                net_revenue_interest=0.825,
                royalty_interest=0.175,
                operator="Demo Operating Co.",
                first_prod_date=date(2021, 1, 1),
                status="ACTIVE",
                created_by="seed_script",
            )
            db.add(prop)

            # Economic inputs
            econ = ACEconomic(
                propnum=well["propnum"],
                scenario_id=scenario.id,
                oil_decline_type="HYP",
                oil_initial_rate=float(well["qi_oil"]),
                oil_decline_rate=float(well["di"]),
                oil_b_factor=float(well["b"]),
                gas_initial_rate=float(well["qi_gas"]),
                gas_decline_rate=float(well["di"]),
                gas_b_factor=float(well["b"]),
                ngl_yield=30.0,
                shrinkage=0.85,
                btu_factor=1.0,
                fixed_opex=5000.0,
                variable_oil_opex=8.0,
                variable_gas_opex=0.50,
                capex=6_000_000.0,
                abandonment_cost=150_000.0,
                economic_limit_type="NET_REVENUE",
                economic_limit_value=0.0,
                run_status="PENDING",
            )
            db.add(econ)

            # 36 months of production history
            first_prod = date(2021, 1, 1)
            for m in range(36):
                prod_date = first_prod + relativedelta(months=m)
                oil_rate = hyperbolic_rate(well["qi_oil"], well["di"], well["b"], m)
                gas_rate = hyperbolic_rate(well["qi_gas"], well["di"], well["b"], m)
                noise = random.uniform(0.9, 1.1)
                days = 30.0
                prod = ACProduct(
                    propnum=well["propnum"],
                    prod_date=prod_date,
                    prod_year=prod_date.year,
                    prod_month=prod_date.month,
                    days_on=days,
                    gross_oil_bbl=oil_rate * noise * days,
                    gross_gas_mcf=gas_rate * noise * days / 1000.0,
                    gross_water_bbl=oil_rate * 0.5 * days,
                    net_oil_bbl=oil_rate * noise * days * 1.0,
                    net_gas_mcf=gas_rate * noise * days / 1000.0,
                    oil_rate_bopd=oil_rate * noise,
                    gas_rate_mcfd=gas_rate * noise,
                    data_source="SEED",
                )
                db.add(prod)

        await db.commit()
        print(f"✅ Seeded {len(WELLS)} wells with production history")
        print(f"   Project: '{project.project_name}' (id={project.id})")
        print(f"   Scenario: '{scenario.scenario_name}' (id={scenario.id})")
        print(f"   Login: admin / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
