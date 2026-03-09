"""
AC_PROPERTY — Well/Property master data table.
Mirrors ARIES AC_PROPERTY table structure.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ACProperty(Base):
    __tablename__ = "AC_PROPERTY"

    # Primary key — ARIES uses PROPNUM as the unique property identifier
    propnum = Column("PROPNUM", String(20), primary_key=True, index=True)

    # Property identification
    propname = Column("PROPNAME", String(100), nullable=True)
    api_num = Column("API_NUM", String(20), nullable=True, index=True)  # API well number
    uwi = Column("UWI", String(20), nullable=True)                       # Unique Well Identifier

    # Location
    state = Column("STATE", String(50), nullable=True)
    county = Column("COUNTY", String(50), nullable=True)
    field = Column("FIELD", String(100), nullable=True)
    formation = Column("FORMATION", String(100), nullable=True)
    basin = Column("BASIN", String(100), nullable=True)
    latitude = Column("LATITUDE", Float, nullable=True)
    longitude = Column("LONGITUDE", Float, nullable=True)

    # Well classification
    well_type = Column("WELL_TYPE", String(20), nullable=True)    # OIL, GAS, BOTH
    prop_type = Column("PROP_TYPE", String(20), nullable=True)    # PRODUCING, NONPRODUCING
    entity_type = Column("ENTITY_TYPE", String(20), default="WELL")  # WELL, GROUP, AREA

    # Ownership
    working_interest = Column("WORKING_INTEREST", Float, default=1.0)     # WI fraction
    net_revenue_interest = Column("NET_REVENUE_INTEREST", Float, default=1.0)  # NRI fraction
    royalty_interest = Column("ROYALTY_INTEREST", Float, default=0.0)
    overriding_royalty = Column("OVERRIDING_ROYALTY", Float, default=0.0)

    # Operating info
    operator = Column("OPERATOR", String(100), nullable=True)
    spud_date = Column("SPUD_DATE", DateTime, nullable=True)
    completion_date = Column("COMPLETION_DATE", DateTime, nullable=True)
    first_prod_date = Column("FIRST_PROD_DATE", DateTime, nullable=True)

    # Economic parameters
    currency = Column("CURRENCY", String(5), default="USD")
    volume_unit = Column("VOLUME_UNIT", String(10), default="BBL")  # BBL, MCF

    # Status
    status = Column("STATUS", String(20), default="ACTIVE")  # ACTIVE, INACTIVE, ABANDONED
    is_active = Column("IS_ACTIVE", Boolean, default=True)

    # Notes
    notes = Column("NOTES", Text, nullable=True)
    user_defined_1 = Column("USER_DEF_1", String(100), nullable=True)
    user_defined_2 = Column("USER_DEF_2", String(100), nullable=True)
    user_defined_3 = Column("USER_DEF_3", Float, nullable=True)

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column("CREATED_BY", String(50), nullable=True)

    # Relationships
    economics = relationship("ACEconomic", back_populates="property", cascade="all, delete-orphan")
    production = relationship("ACProduct", back_populates="property", cascade="all, delete-orphan")
    forecasts = relationship("ACProductForecast", back_populates="property", cascade="all, delete-orphan")
    qualifiers = relationship("ACQualifier", back_populates="property", cascade="all, delete-orphan")
    reserves = relationship("ACReserves", back_populates="property", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ACProperty propnum={self.propnum} name={self.propname}>"
