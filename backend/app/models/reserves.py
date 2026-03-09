"""
AC_RESERVES — Reserves bookings per property per year.
Tracks proved reserves, probable, possible per PRMS categories.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ACReserves(Base):
    __tablename__ = "AC_RESERVES"

    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False, index=True)

    # Booking year and category
    booking_year = Column("BOOKING_YEAR", Integer, nullable=False)
    reserves_category = Column("RESERVES_CAT", String(20), nullable=False)  # 1P, 2P, 3P, PDP, PUD, etc.

    # Proved reserves (1P)
    proved_oil_mstb = Column("PROVED_OIL_MSTB", Float, default=0.0)
    proved_gas_mmcf = Column("PROVED_GAS_MMCF", Float, default=0.0)
    proved_ngl_mstb = Column("PROVED_NGL_MSTB", Float, default=0.0)
    proved_boe = Column("PROVED_BOE", Float, default=0.0)               # Barrels of oil equivalent (6:1)

    # Probable reserves (2P incremental)
    probable_oil_mstb = Column("PROBABLE_OIL_MSTB", Float, default=0.0)
    probable_gas_mmcf = Column("PROBABLE_GAS_MMCF", Float, default=0.0)
    probable_ngl_mstb = Column("PROBABLE_NGL_MSTB", Float, default=0.0)

    # Possible reserves (3P incremental)
    possible_oil_mstb = Column("POSSIBLE_OIL_MSTB", Float, default=0.0)
    possible_gas_mmcf = Column("POSSIBLE_GAS_MMCF", Float, default=0.0)
    possible_ngl_mstb = Column("POSSIBLE_NGL_MSTB", Float, default=0.0)

    # Economic values at booking
    npv10_proved = Column("NPV10_PROVED", Float, default=0.0)           # PV10 for SEC reporting
    npv10_probable = Column("NPV10_PROBABLE", Float, default=0.0)
    npv10_possible = Column("NPV10_POSSIBLE", Float, default=0.0)

    # Reconciliation items
    prior_year_reserves = Column("PRIOR_YR_RESERVES", Float, default=0.0)
    revision_up = Column("REVISION_UP", Float, default=0.0)
    revision_down = Column("REVISION_DOWN", Float, default=0.0)
    improved_recovery = Column("IMPROVED_RECOVERY", Float, default=0.0)
    extensions_discoveries = Column("EXT_DISC", Float, default=0.0)
    acquisitions = Column("ACQUISITIONS", Float, default=0.0)
    divestitures = Column("DIVESTITURES", Float, default=0.0)
    production = Column("PRODUCTION", Float, default=0.0)

    # Status
    is_approved = Column("IS_APPROVED", Boolean, default=False)
    approved_by = Column("APPROVED_BY", String(100), nullable=True)
    approved_date = Column("APPROVED_DATE", DateTime, nullable=True)

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("PROPNUM", "BOOKING_YEAR", "RESERVES_CAT", name="uq_reserves_prop_year_cat"),
    )

    # Relationships
    property = relationship("ACProperty", back_populates="reserves")

    def __repr__(self):
        return f"<ACReserves propnum={self.propnum} year={self.booking_year} cat={self.reserves_category}>"
