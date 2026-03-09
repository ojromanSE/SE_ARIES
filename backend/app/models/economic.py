"""
AC_ECONOMIC — Keyword-driven economic parameters table.
This is the core ARIES table that stores the economic model for each property/scenario.
ARIES uses a keyword language to define production forecasts and economic assumptions.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ACEconomic(Base):
    __tablename__ = "AC_ECONOMIC"

    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False, index=True)
    scenario_id = Column("SCENARIO_ID", Integer, ForeignKey("AC_SCENARIO.id"), nullable=False, index=True)

    # Section 1 — Production (Decline Curve) Keywords
    # Decline type: EXP, HYP, HAR
    oil_decline_type = Column("OIL_DCA_TYPE", String(10), default="EXP")
    oil_initial_rate = Column("OIL_QI", Float, nullable=True)        # Initial oil rate (BBL/day)
    oil_decline_rate = Column("OIL_DI", Float, nullable=True)        # Nominal decline rate (/yr or /mo)
    oil_b_factor = Column("OIL_B", Float, default=0.0)               # Hyperbolic b-factor (0=exp,1=harm)
    oil_terminal_decline = Column("OIL_DT", Float, nullable=True)    # Terminal decline rate (switches to exp)
    oil_eur = Column("OIL_EUR", Float, nullable=True)                # Estimated ultimate recovery (MSTB)

    gas_decline_type = Column("GAS_DCA_TYPE", String(10), default="EXP")
    gas_initial_rate = Column("GAS_QI", Float, nullable=True)        # Initial gas rate (MMCFD)
    gas_decline_rate = Column("GAS_DI", Float, nullable=True)
    gas_b_factor = Column("GAS_B", Float, default=0.0)
    gas_terminal_decline = Column("GAS_DT", Float, nullable=True)
    gas_eur = Column("GAS_EUR", Float, nullable=True)                # EUR (MMCF)

    ngl_yield = Column("NGL_YIELD", Float, default=0.0)              # NGL yield (BBL/MMCF)
    shrinkage = Column("SHRINKAGE", Float, default=1.0)              # Gas shrink factor (SHRINK keyword)
    btu_factor = Column("BTU_FACTOR", Float, default=1.0)            # BTU adjustment (BTU keyword)

    water_oil_ratio = Column("WOR", Float, default=0.0)              # Water-oil ratio
    gas_oil_ratio = Column("GOR", Float, default=0.0)                # Gas-oil ratio (MCF/BBL)

    # Section 2 — Pricing & Revenue Keywords
    oil_price_diff = Column("OIL_PRICE_DIFF", Float, default=0.0)    # Price differential $/BBL
    gas_price_diff = Column("GAS_PRICE_DIFF", Float, default=0.0)    # Price differential $/MCF
    ngl_price_pct = Column("NGL_PRICE_PCT", Float, default=0.4)     # NGL price as % of oil price

    # Section 3 — Expenses Keywords (OPEX)
    fixed_opex = Column("FIXED_OPEX", Float, default=0.0)            # Fixed operating cost $/month
    variable_oil_opex = Column("VAR_OIL_OPEX", Float, default=0.0)  # Variable oil opex $/BBL
    variable_gas_opex = Column("VAR_GAS_OPEX", Float, default=0.0)  # Variable gas opex $/MCF
    overhead = Column("OVERHEAD", Float, default=0.0)                 # G&A overhead $/month
    workovers = Column("WORKOVERS", Float, default=0.0)               # Workover cost $/year

    # Section 4 — Capital (CAPEX) Keywords
    capex = Column("CAPEX", Float, default=0.0)                       # Initial capital investment ($M)
    capex_date = Column("CAPEX_DATE", DateTime, nullable=True)
    abandonment_cost = Column("ABANDONMENT_COST", Float, default=0.0)  # Plug & abandonment cost ($)
    capex_schedule = Column("CAPEX_SCHEDULE", JSON, nullable=True)    # [{date, amount, description}]

    # Section 5 — Economic Limit Keywords (LOSS)
    economic_limit_type = Column("ECON_LIMIT_TYPE", String(20), default="NET_REVENUE")  # NET_REVENUE, OIL_RATE, GAS_RATE
    economic_limit_value = Column("ECON_LIMIT_VALUE", Float, default=0.0)  # $ or rate threshold
    max_life_months = Column("MAX_LIFE_MONTHS", Integer, nullable=True)  # LIFE keyword

    # Raw keyword text (AC_ECONOMIC Section format — for import/export compatibility)
    keyword_text = Column("KEYWORD_TEXT", Text, nullable=True)        # Raw ARIES keyword lines

    # Calculated results (cached after simulation run)
    npv10 = Column("NPV10", Float, nullable=True)
    npv15 = Column("NPV15", Float, nullable=True)
    irr = Column("IRR", Float, nullable=True)
    payout_months = Column("PAYOUT_MONTHS", Float, nullable=True)
    total_capex = Column("TOTAL_CAPEX", Float, nullable=True)
    total_opex = Column("TOTAL_OPEX", Float, nullable=True)
    total_revenue = Column("TOTAL_REVENUE", Float, nullable=True)
    cum_oil_mstb = Column("CUM_OIL_MSTB", Float, nullable=True)
    cum_gas_mmcf = Column("CUM_GAS_MMCF", Float, nullable=True)
    cum_ngl_mstb = Column("CUM_NGL_MSTB", Float, nullable=True)

    # Run tracking
    last_run_at = Column("LAST_RUN_AT", DateTime, nullable=True)
    run_status = Column("RUN_STATUS", String(20), default="PENDING")  # PENDING, SUCCESS, ERROR

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    property = relationship("ACProperty", back_populates="economics")
    scenario = relationship("ACScenario", back_populates="economics")

    def __repr__(self):
        return f"<ACEconomic propnum={self.propnum} scenario_id={self.scenario_id}>"
