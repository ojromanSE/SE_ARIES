"""
AC_SCENARIO — Economic scenario definitions.
ARIES supports multiple price decks / scenarios (e.g., Base, High, Low).
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ACScenario(Base):
    __tablename__ = "AC_SCENARIO"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("AC_PROJECT.id"), nullable=False, index=True)

    # Scenario identification
    scenario_name = Column("SCENARIO_NAME", String(50), nullable=False)
    scenario_code = Column("SCENARIO_CODE", String(10), nullable=True)
    description = Column("DESCRIPTION", Text, nullable=True)
    scenario_type = Column("SCENARIO_TYPE", String(20), default="ECONOMIC")  # ECONOMIC, RESERVE, PRODUCTION

    # Price deck
    oil_price = Column("OIL_PRICE", Float, nullable=True)         # Base oil price $/BBL
    gas_price = Column("GAS_PRICE", Float, nullable=True)         # Base gas price $/MCF
    ngl_price = Column("NGL_PRICE", Float, nullable=True)         # NGL price $/BBL
    oil_price_escalation = Column("OIL_PRICE_ESC", Float, default=0.0)  # Annual % escalation
    gas_price_escalation = Column("GAS_PRICE_ESC", Float, default=0.0)
    price_deck = Column("PRICE_DECK", JSON, nullable=True)         # Full price deck [{date, oil, gas, ngl}]

    # Economic parameters
    discount_rate = Column("DISCOUNT_RATE", Float, default=10.0)
    tax_rate = Column("TAX_RATE", Float, default=0.0)           # Severance / production tax rate
    ad_valorem_rate = Column("AD_VALOREM_RATE", Float, default=0.0)
    chance_of_success = Column("CHANCE_OF_SUCCESS", Float, default=1.0)  # XINVWT keyword
    apply_economic_limit = Column("APPLY_ECON_LIMIT", Boolean, default=True)  # LOSS keyword

    # Date settings
    econ_start_date = Column("ECON_START_DATE", DateTime, nullable=True)
    max_life_years = Column("MAX_LIFE_YEARS", Float, default=40.0)  # LIFE keyword

    # Status
    is_base_case = Column("IS_BASE_CASE", Boolean, default=False)
    is_active = Column("IS_ACTIVE", Boolean, default=True)

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("ACProject", back_populates="scenarios")
    economics = relationship("ACEconomic", back_populates="scenario", cascade="all, delete-orphan")
    forecasts = relationship("ACProductForecast", back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ACScenario id={self.id} name={self.scenario_name}>"
