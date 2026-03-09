"""
AC_PRODUCT — Production history (date-series volumes)
AC_PRODUCT_FORECAST — Forecasted production per scenario
Mirrors ARIES production tables.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Date, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ACProduct(Base):
    """Historical production data — one row per property per month."""
    __tablename__ = "AC_PRODUCT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False, index=True)

    # Production date (monthly)
    prod_date = Column("PROD_DATE", Date, nullable=False)
    prod_year = Column("PROD_YEAR", Integer, nullable=False)
    prod_month = Column("PROD_MONTH", Integer, nullable=False)
    days_on = Column("DAYS_ON", Float, default=30.0)  # Producing days in month

    # Volumes (gross — before WI/NRI)
    gross_oil_bbl = Column("GROSS_OIL_BBL", Float, default=0.0)     # Gross oil (BBL)
    gross_gas_mcf = Column("GROSS_GAS_MCF", Float, default=0.0)     # Gross gas (MCF)
    gross_ngl_bbl = Column("GROSS_NGL_BBL", Float, default=0.0)     # Gross NGL (BBL)
    gross_water_bbl = Column("GROSS_WATER_BBL", Float, default=0.0) # Gross water (BBL)

    # Net volumes (after WI)
    net_oil_bbl = Column("NET_OIL_BBL", Float, default=0.0)
    net_gas_mcf = Column("NET_GAS_MCF", Float, default=0.0)
    net_ngl_bbl = Column("NET_NGL_BBL", Float, default=0.0)

    # Rates (daily averages)
    oil_rate_bopd = Column("OIL_RATE_BOPD", Float, default=0.0)    # BOPD
    gas_rate_mcfd = Column("GAS_RATE_MCFD", Float, default=0.0)    # MCFD

    # Data source
    data_source = Column("DATA_SOURCE", String(50), nullable=True)  # IHS, DI, MANUAL, etc.
    is_estimated = Column("IS_ESTIMATED", Boolean, default=False)

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("PROPNUM", "PROD_DATE", name="uq_product_propnum_date"),
    )

    # Relationships
    property = relationship("ACProperty", back_populates="production")

    def __repr__(self):
        return f"<ACProduct propnum={self.propnum} date={self.prod_date}>"


class ACProductForecast(Base):
    """Forecasted production per property per scenario — one row per month."""
    __tablename__ = "AC_PRODUCT_FORECAST"

    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False, index=True)
    scenario_id = Column("SCENARIO_ID", Integer, ForeignKey("AC_SCENARIO.id"), nullable=False, index=True)

    # Forecast date
    forecast_date = Column("FORECAST_DATE", Date, nullable=False)
    forecast_year = Column("FORECAST_YEAR", Integer, nullable=False)
    forecast_month = Column("FORECAST_MONTH", Integer, nullable=False)

    # Gross volumes
    gross_oil_bbl = Column("GROSS_OIL_BBL", Float, default=0.0)
    gross_gas_mcf = Column("GROSS_GAS_MCF", Float, default=0.0)
    gross_ngl_bbl = Column("GROSS_NGL_BBL", Float, default=0.0)

    # Net volumes (after WI/NRI)
    net_oil_bbl = Column("NET_OIL_BBL", Float, default=0.0)
    net_gas_mcf = Column("NET_GAS_MCF", Float, default=0.0)
    net_ngl_bbl = Column("NET_NGL_BBL", Float, default=0.0)

    # Revenue
    oil_revenue = Column("OIL_REVENUE", Float, default=0.0)        # $
    gas_revenue = Column("GAS_REVENUE", Float, default=0.0)        # $
    ngl_revenue = Column("NGL_REVENUE", Float, default=0.0)        # $
    total_revenue = Column("TOTAL_REVENUE", Float, default=0.0)    # $

    # Costs
    opex = Column("OPEX", Float, default=0.0)                       # $ operating expense
    capex = Column("CAPEX", Float, default=0.0)                     # $ capital expense
    taxes = Column("TAXES", Float, default=0.0)                     # $ production taxes

    # Cash flow
    net_cash_flow = Column("NET_CASH_FLOW", Float, default=0.0)    # $ NCF
    cum_cash_flow = Column("CUM_CASH_FLOW", Float, default=0.0)    # $ cumulative NCF
    discounted_ncf = Column("DISCOUNTED_NCF", Float, default=0.0)  # $ discounted NCF

    # Decline curve values (for plotting)
    oil_rate_bopd = Column("OIL_RATE_BOPD", Float, default=0.0)
    gas_rate_mcfd = Column("GAS_RATE_MCFD", Float, default=0.0)
    cum_oil_mstb = Column("CUM_OIL_MSTB", Float, default=0.0)     # Cumulative oil (MSTB)
    cum_gas_mmcf = Column("CUM_GAS_MMCF", Float, default=0.0)     # Cumulative gas (MMCF)

    __table_args__ = (
        UniqueConstraint("PROPNUM", "SCENARIO_ID", "FORECAST_DATE", name="uq_forecast_prop_scen_date"),
    )

    # Relationships
    property = relationship("ACProperty", back_populates="forecasts")
    scenario = relationship("ACScenario", back_populates="forecasts")

    def __repr__(self):
        return f"<ACProductForecast propnum={self.propnum} scenario={self.scenario_id} date={self.forecast_date}>"
