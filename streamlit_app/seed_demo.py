"""
Seed demo data for Streamlit app.
Run: cd streamlit_app && python seed_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import random
from datetime import date
from dateutil.relativedelta import relativedelta
from services.db import (
    init_db, SessionLocal, ACProperty, ACProject, ACScenario, ACEconomic, ACProduct
)

WELLS = [
    {"propnum": "PB-001", "propname": "Smith Unit 1H", "api": "42-003-12345-0000",
     "field": "Midland", "state": "TX", "county": "Midland", "basin": "Permian",
     "qi_oil": 850, "qi_gas": 1200, "di": 0.65, "b": 1.5},
    {"propnum": "PB-002", "propname": "Jones State 2H", "api": "42-227-23456-0000",
     "field": "Wolfcamp", "state": "TX", "county": "Martin", "basin": "Permian",
     "qi_oil": 1100, "qi_gas": 2500, "di": 0.72, "b": 1.3},
    {"propnum": "PB-003", "propname": "Williams Federal 1H", "api": "42-109-34567-0000",
     "field": "Delaware", "state": "TX", "county": "Ector", "basin": "Permian",
     "qi_oil": 650, "qi_gas": 900, "di": 0.55, "b": 1.2},
    {"propnum": "EF-001", "propname": "Eagle Ford 1H", "api": "42-149-56789-0000",
     "field": "Eagle Ford", "state": "TX", "county": "Gonzales", "basin": "Gulf Coast",
     "qi_oil": 500, "qi_gas": 800, "di": 0.50, "b": 1.1},
]


def hyp_rate(qi, di, b, m):
    t = m / 12.0
    return qi / (1 + b * di * t) ** (1 / b) if b > 0.01 else qi * __import__('math').exp(-di * t)


def seed():
    init_db()
    db = SessionLocal()
    try:
        # Project
        proj = db.query(ACProject).filter(ACProject.project_name == "Permian Basin Demo").first()
        if not proj:
            proj = ACProject(
                project_name="Permian Basin Demo",
                project_code="PB-DEMO",
                description="Demo wells — Permian Basin and Gulf Coast",
                default_discount_rate=10.0,
                created_by="seed",
            )
            db.add(proj)
            db.flush()

        # Scenario
        scen = db.query(ACScenario).filter(ACScenario.project_id == proj.id, ACScenario.scenario_name == "Base Case").first()
        if not scen:
            from datetime import datetime
            scen = ACScenario(
                project_id=proj.id,
                scenario_name="Base Case",
                scenario_code="BASE",
                oil_price=70.0,
                gas_price=3.00,
                discount_rate=10.0,
                tax_rate=0.05,
                ad_valorem_rate=0.02,
                apply_economic_limit=True,
                econ_start_date=datetime.combine(date.today().replace(day=1), datetime.min.time()),
                is_base_case=True,
            )
            db.add(scen)
            db.flush()

        for w in WELLS:
            prop = db.query(ACProperty).filter(ACProperty.propnum == w["propnum"]).first()
            if not prop:
                from datetime import datetime
                prop = ACProperty(
                    propnum=w["propnum"], propname=w["propname"], api_num=w["api"],
                    state=w["state"], county=w["county"], field=w["field"], basin=w["basin"],
                    well_type="OIL", working_interest=1.0, net_revenue_interest=0.825,
                    royalty_interest=0.175, operator="Demo Operating Co.",
                    first_prod_date=datetime(2021, 1, 1), status="ACTIVE", created_by="seed",
                )
                db.add(prop)

            # Economic inputs
            if not db.query(ACEconomic).filter(ACEconomic.propnum == w["propnum"], ACEconomic.scenario_id == scen.id).first():
                db.add(ACEconomic(
                    propnum=w["propnum"], scenario_id=scen.id,
                    oil_decline_type="HYP", oil_initial_rate=float(w["qi_oil"]),
                    oil_decline_rate=float(w["di"]), oil_b_factor=float(w["b"]),
                    gas_initial_rate=float(w["qi_gas"]), gas_decline_rate=float(w["di"]),
                    gas_b_factor=float(w["b"]), ngl_yield=30.0, shrinkage=0.85,
                    fixed_opex=5000.0, variable_oil_opex=8.0, capex=6_000_000.0,
                    abandonment_cost=150_000.0, run_status="PENDING",
                ))

            # 36 months production history
            first = date(2021, 1, 1)
            for m in range(36):
                pd_date = first + relativedelta(months=m)
                if db.query(ACProduct).filter(ACProduct.propnum == w["propnum"], ACProduct.prod_date == pd_date).first():
                    continue
                oil = hyp_rate(w["qi_oil"], w["di"], w["b"], m) * random.uniform(0.9, 1.1)
                gas = hyp_rate(w["qi_gas"], w["di"], w["b"], m) * random.uniform(0.9, 1.1)
                days = 30.0
                db.add(ACProduct(
                    propnum=w["propnum"], prod_date=pd_date,
                    prod_year=pd_date.year, prod_month=pd_date.month,
                    days_on=days, gross_oil_bbl=oil * days, gross_gas_mcf=gas * days / 1000.0,
                    gross_water_bbl=oil * 0.5 * days, net_oil_bbl=oil * days,
                    net_gas_mcf=gas * days / 1000.0, oil_rate_bopd=oil, gas_rate_mcfd=gas,
                    data_source="SEED",
                ))

        db.commit()
        print(f"✅ Seeded {len(WELLS)} wells | Project: '{proj.project_name}' | Scenario: '{scen.scenario_name}'")
        print("   Login: admin / admin123")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
