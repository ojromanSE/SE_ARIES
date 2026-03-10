"""
Synchronous SQLAlchemy database layer for Streamlit.
Uses the same SQLite DB as the FastAPI backend (shared file).
"""
import os
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, String, Float, Integer, DateTime, Text,
    Boolean, ForeignKey, Date, UniqueConstraint, Table, MetaData, JSON,
    and_, or_, func, text,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session, sessionmaker
from sqlalchemy.sql import func as sqlfunc
from datetime import datetime

# DB path — use /tmp on Streamlit Cloud (writable), local path otherwise
_default_db = Path("/tmp/se_aries.db")
DB_PATH = os.environ.get("SE_ARIES_DB", str(_default_db))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)


class Base(DeclarativeBase):
    pass


# ── Association table ──────────────────────────────────────────────────────
project_property = Table(
    "AC_PROJECT_PROPERTY", Base.metadata,
    Column("project_id", Integer, ForeignKey("AC_PROJECT.id"), primary_key=True),
    Column("propnum", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), primary_key=True),
    Column("weight_factor", Float, default=1.0),
    Column("sort_order", Integer, default=0),
)


# ── Models ─────────────────────────────────────────────────────────────────
class ACProperty(Base):
    __tablename__ = "AC_PROPERTY"
    propnum = Column("PROPNUM", String(20), primary_key=True)
    propname = Column("PROPNAME", String(100))
    api_num = Column("API_NUM", String(20))
    uwi = Column("UWI", String(20))
    state = Column("STATE", String(50))
    county = Column("COUNTY", String(50))
    field = Column("FIELD", String(100))
    formation = Column("FORMATION", String(100))
    basin = Column("BASIN", String(100))
    latitude = Column("LATITUDE", Float)
    longitude = Column("LONGITUDE", Float)
    well_type = Column("WELL_TYPE", String(20), default="OIL")
    prop_type = Column("PROP_TYPE", String(20), default="PRODUCING")
    entity_type = Column("ENTITY_TYPE", String(20), default="WELL")
    working_interest = Column("WORKING_INTEREST", Float, default=1.0)
    net_revenue_interest = Column("NET_REVENUE_INTEREST", Float, default=1.0)
    royalty_interest = Column("ROYALTY_INTEREST", Float, default=0.0)
    overriding_royalty = Column("OVERRIDING_ROYALTY", Float, default=0.0)
    operator = Column("OPERATOR", String(100))
    spud_date = Column("SPUD_DATE", DateTime)
    completion_date = Column("COMPLETION_DATE", DateTime)
    first_prod_date = Column("FIRST_PROD_DATE", DateTime)
    currency = Column("CURRENCY", String(5), default="USD")
    volume_unit = Column("VOLUME_UNIT", String(10), default="BBL")
    status = Column("STATUS", String(20), default="ACTIVE")
    is_active = Column("IS_ACTIVE", Boolean, default=True)
    notes = Column("NOTES", Text)
    user_defined_1 = Column("USER_DEF_1", String(100))
    user_defined_2 = Column("USER_DEF_2", String(100))
    user_defined_3 = Column("USER_DEF_3", Float)
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    updated_at = Column("UPDATED_AT", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column("CREATED_BY", String(50))
    economics = relationship("ACEconomic", back_populates="property", cascade="all, delete-orphan")
    production = relationship("ACProduct", back_populates="property", cascade="all, delete-orphan")
    forecasts = relationship("ACProductForecast", back_populates="property", cascade="all, delete-orphan")


class ACProject(Base):
    __tablename__ = "AC_PROJECT"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column("PROJECT_NAME", String(100), nullable=False, unique=True)
    project_code = Column("PROJECT_CODE", String(20))
    description = Column("DESCRIPTION", Text)
    project_type = Column("PROJECT_TYPE", String(30), default="WORKING")
    parent_project_id = Column("PARENT_PROJECT_ID", Integer, ForeignKey("AC_PROJECT.id"))
    default_discount_rate = Column("DEFAULT_DISCOUNT_RATE", Float, default=10.0)
    consolidation_method = Column("CONSOLIDATION_METHOD", String(20), default="SUM")
    econ_start_date = Column("ECON_START_DATE", DateTime)
    is_active = Column("IS_ACTIVE", Boolean, default=True)
    is_locked = Column("IS_LOCKED", Boolean, default=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    created_by = Column("CREATED_BY", String(50))
    scenarios = relationship("ACScenario", back_populates="project", cascade="all, delete-orphan")


class ACScenario(Base):
    __tablename__ = "AC_SCENARIO"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("AC_PROJECT.id"), nullable=False)
    scenario_name = Column("SCENARIO_NAME", String(50), nullable=False)
    scenario_code = Column("SCENARIO_CODE", String(10))
    description = Column("DESCRIPTION", Text)
    scenario_type = Column("SCENARIO_TYPE", String(20), default="ECONOMIC")
    oil_price = Column("OIL_PRICE", Float)
    gas_price = Column("GAS_PRICE", Float)
    ngl_price = Column("NGL_PRICE", Float)
    oil_price_escalation = Column("OIL_PRICE_ESC", Float, default=0.0)
    gas_price_escalation = Column("GAS_PRICE_ESC", Float, default=0.0)
    price_deck = Column("PRICE_DECK", JSON)
    discount_rate = Column("DISCOUNT_RATE", Float, default=10.0)
    tax_rate = Column("TAX_RATE", Float, default=0.0)
    ad_valorem_rate = Column("AD_VALOREM_RATE", Float, default=0.0)
    chance_of_success = Column("CHANCE_OF_SUCCESS", Float, default=1.0)
    apply_economic_limit = Column("APPLY_ECON_LIMIT", Boolean, default=True)
    econ_start_date = Column("ECON_START_DATE", DateTime)
    max_life_years = Column("MAX_LIFE_YEARS", Float, default=40.0)
    is_base_case = Column("IS_BASE_CASE", Boolean, default=False)
    is_active = Column("IS_ACTIVE", Boolean, default=True)
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    project = relationship("ACProject", back_populates="scenarios")
    economics = relationship("ACEconomic", back_populates="scenario", cascade="all, delete-orphan")
    forecasts = relationship("ACProductForecast", back_populates="scenario", cascade="all, delete-orphan")


class ACEconomic(Base):
    __tablename__ = "AC_ECONOMIC"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False)
    scenario_id = Column("SCENARIO_ID", Integer, ForeignKey("AC_SCENARIO.id"), nullable=False)
    oil_decline_type = Column("OIL_DCA_TYPE", String(10), default="EXP")
    oil_initial_rate = Column("OIL_QI", Float)
    oil_decline_rate = Column("OIL_DI", Float)
    oil_b_factor = Column("OIL_B", Float, default=0.0)
    oil_terminal_decline = Column("OIL_DT", Float)
    oil_eur = Column("OIL_EUR", Float)
    gas_decline_type = Column("GAS_DCA_TYPE", String(10), default="EXP")
    gas_initial_rate = Column("GAS_QI", Float)
    gas_decline_rate = Column("GAS_DI", Float)
    gas_b_factor = Column("GAS_B", Float, default=0.0)
    gas_terminal_decline = Column("GAS_DT", Float)
    gas_eur = Column("GAS_EUR", Float)
    ngl_yield = Column("NGL_YIELD", Float, default=0.0)
    shrinkage = Column("SHRINKAGE", Float, default=1.0)
    btu_factor = Column("BTU_FACTOR", Float, default=1.0)
    water_oil_ratio = Column("WOR", Float, default=0.0)
    gas_oil_ratio = Column("GOR", Float, default=0.0)
    oil_price_diff = Column("OIL_PRICE_DIFF", Float, default=0.0)
    gas_price_diff = Column("GAS_PRICE_DIFF", Float, default=0.0)
    ngl_price_pct = Column("NGL_PRICE_PCT", Float, default=0.4)
    fixed_opex = Column("FIXED_OPEX", Float, default=0.0)
    variable_oil_opex = Column("VAR_OIL_OPEX", Float, default=0.0)
    variable_gas_opex = Column("VAR_GAS_OPEX", Float, default=0.0)
    overhead = Column("OVERHEAD", Float, default=0.0)
    workovers = Column("WORKOVERS", Float, default=0.0)
    capex = Column("CAPEX", Float, default=0.0)
    capex_date = Column("CAPEX_DATE", DateTime)
    abandonment_cost = Column("ABANDONMENT_COST", Float, default=0.0)
    capex_schedule = Column("CAPEX_SCHEDULE", JSON)
    economic_limit_type = Column("ECON_LIMIT_TYPE", String(20), default="NET_REVENUE")
    economic_limit_value = Column("ECON_LIMIT_VALUE", Float, default=0.0)
    max_life_months = Column("MAX_LIFE_MONTHS", Integer)
    keyword_text = Column("KEYWORD_TEXT", Text)
    npv10 = Column("NPV10", Float)
    npv15 = Column("NPV15", Float)
    irr = Column("IRR", Float)
    payout_months = Column("PAYOUT_MONTHS", Float)
    total_capex = Column("TOTAL_CAPEX", Float)
    total_opex = Column("TOTAL_OPEX", Float)
    total_revenue = Column("TOTAL_REVENUE", Float)
    cum_oil_mstb = Column("CUM_OIL_MSTB", Float)
    cum_gas_mmcf = Column("CUM_GAS_MMCF", Float)
    cum_ngl_mstb = Column("CUM_NGL_MSTB", Float)
    last_run_at = Column("LAST_RUN_AT", DateTime)
    run_status = Column("RUN_STATUS", String(20), default="PENDING")
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    updated_at = Column("UPDATED_AT", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    property = relationship("ACProperty", back_populates="economics")
    scenario = relationship("ACScenario", back_populates="economics")


class ACProduct(Base):
    __tablename__ = "AC_PRODUCT"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False)
    prod_date = Column("PROD_DATE", Date, nullable=False)
    prod_year = Column("PROD_YEAR", Integer, nullable=False)
    prod_month = Column("PROD_MONTH", Integer, nullable=False)
    days_on = Column("DAYS_ON", Float, default=30.0)
    gross_oil_bbl = Column("GROSS_OIL_BBL", Float, default=0.0)
    gross_gas_mcf = Column("GROSS_GAS_MCF", Float, default=0.0)
    gross_ngl_bbl = Column("GROSS_NGL_BBL", Float, default=0.0)
    gross_water_bbl = Column("GROSS_WATER_BBL", Float, default=0.0)
    net_oil_bbl = Column("NET_OIL_BBL", Float, default=0.0)
    net_gas_mcf = Column("NET_GAS_MCF", Float, default=0.0)
    net_ngl_bbl = Column("NET_NGL_BBL", Float, default=0.0)
    oil_rate_bopd = Column("OIL_RATE_BOPD", Float, default=0.0)
    gas_rate_mcfd = Column("GAS_RATE_MCFD", Float, default=0.0)
    data_source = Column("DATA_SOURCE", String(50))
    is_estimated = Column("IS_ESTIMATED", Boolean, default=False)
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("PROPNUM", "PROD_DATE", name="uq_product_propnum_date"),)
    property = relationship("ACProperty", back_populates="production")


class ACProductForecast(Base):
    __tablename__ = "AC_PRODUCT_FORECAST"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False)
    scenario_id = Column("SCENARIO_ID", Integer, ForeignKey("AC_SCENARIO.id"), nullable=False)
    forecast_date = Column("FORECAST_DATE", Date, nullable=False)
    forecast_year = Column("FORECAST_YEAR", Integer, nullable=False)
    forecast_month = Column("FORECAST_MONTH", Integer, nullable=False)
    gross_oil_bbl = Column("GROSS_OIL_BBL", Float, default=0.0)
    gross_gas_mcf = Column("GROSS_GAS_MCF", Float, default=0.0)
    gross_ngl_bbl = Column("GROSS_NGL_BBL", Float, default=0.0)
    net_oil_bbl = Column("NET_OIL_BBL", Float, default=0.0)
    net_gas_mcf = Column("NET_GAS_MCF", Float, default=0.0)
    net_ngl_bbl = Column("NET_NGL_BBL", Float, default=0.0)
    oil_revenue = Column("OIL_REVENUE", Float, default=0.0)
    gas_revenue = Column("GAS_REVENUE", Float, default=0.0)
    ngl_revenue = Column("NGL_REVENUE", Float, default=0.0)
    total_revenue = Column("TOTAL_REVENUE", Float, default=0.0)
    opex = Column("OPEX", Float, default=0.0)
    capex = Column("CAPEX", Float, default=0.0)
    taxes = Column("TAXES", Float, default=0.0)
    net_cash_flow = Column("NET_CASH_FLOW", Float, default=0.0)
    cum_cash_flow = Column("CUM_CASH_FLOW", Float, default=0.0)
    discounted_ncf = Column("DISCOUNTED_NCF", Float, default=0.0)
    oil_rate_bopd = Column("OIL_RATE_BOPD", Float, default=0.0)
    gas_rate_mcfd = Column("GAS_RATE_MCFD", Float, default=0.0)
    cum_oil_mstb = Column("CUM_OIL_MSTB", Float, default=0.0)
    cum_gas_mmcf = Column("CUM_GAS_MMCF", Float, default=0.0)
    __table_args__ = (
        UniqueConstraint("PROPNUM", "SCENARIO_ID", "FORECAST_DATE", name="uq_forecast_prop_scen_date"),
    )
    property = relationship("ACProperty", back_populates="forecasts")
    scenario = relationship("ACScenario", back_populates="forecasts")


class ACQualifier(Base):
    __tablename__ = "AC_QUALIFIER"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False)
    reserves_category = Column("RESERVES_CAT", String(20), default="PD")
    reserves_subcategory = Column("RESERVES_SUBCAT", String(20))
    data_source = Column("DATA_SOURCE", String(50))
    confidence_level = Column("CONFIDENCE_LEVEL", String(10), default="HIGH")
    review_status = Column("REVIEW_STATUS", String(20), default="UNREVIEWED")
    booking_entity = Column("BOOKING_ENTITY", String(100))
    booking_date = Column("BOOKING_DATE", DateTime)
    auditor = Column("AUDITOR", String(100))
    qualifier_notes = Column("QUALIFIER_NOTES", Text)
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    updated_at = Column("UPDATED_AT", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ACReserves(Base):
    __tablename__ = "AC_RESERVES"
    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False)
    booking_year = Column("BOOKING_YEAR", Integer, nullable=False)
    reserves_category = Column("RESERVES_CAT", String(20), nullable=False)
    proved_oil_mstb = Column("PROVED_OIL_MSTB", Float, default=0.0)
    proved_gas_mmcf = Column("PROVED_GAS_MMCF", Float, default=0.0)
    proved_ngl_mstb = Column("PROVED_NGL_MSTB", Float, default=0.0)
    proved_boe = Column("PROVED_BOE", Float, default=0.0)
    probable_oil_mstb = Column("PROBABLE_OIL_MSTB", Float, default=0.0)
    probable_gas_mmcf = Column("PROBABLE_GAS_MMCF", Float, default=0.0)
    npv10_proved = Column("NPV10_PROVED", Float, default=0.0)
    npv10_probable = Column("NPV10_PROBABLE", Float, default=0.0)
    prior_year_reserves = Column("PRIOR_YR_RESERVES", Float, default=0.0)
    revision_up = Column("REVISION_UP", Float, default=0.0)
    revision_down = Column("REVISION_DOWN", Float, default=0.0)
    extensions_discoveries = Column("EXT_DISC", Float, default=0.0)
    acquisitions = Column("ACQUISITIONS", Float, default=0.0)
    production = Column("PRODUCTION", Float, default=0.0)
    is_approved = Column("IS_APPROVED", Boolean, default=False)
    approved_by = Column("APPROVED_BY", String(100))
    approved_date = Column("APPROVED_DATE", DateTime)
    created_at = Column("CREATED_AT", DateTime, default=datetime.utcnow)
    updated_at = Column("UPDATED_AT", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("PROPNUM", "BOOKING_YEAR", "RESERVES_CAT", name="uq_reserves_prop_year_cat"),)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="analyst")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


def init_db():
    Base.metadata.create_all(engine)
    _seed_admin()


def _seed_admin():
    pass  # auth removed


def get_db() -> Session:
    return SessionLocal()
