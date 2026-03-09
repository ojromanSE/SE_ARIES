"""
AC_QUALIFIER — Data qualifiers/classifications for properties.
Used for reserves classification (PD, PUD, PROB, POSS) and data QC.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ACQualifier(Base):
    __tablename__ = "AC_QUALIFIER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    propnum = Column("PROPNUM", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), nullable=False, index=True)

    # Reserves classification (SPE-PRMS)
    reserves_category = Column("RESERVES_CAT", String(20), default="PD")
    # PD = Proved Developed (PDP + PDNP)
    # PDP = Proved Developed Producing
    # PDNP = Proved Developed Non-Producing
    # PUD = Proved Undeveloped
    # PROB = Probable
    # POSS = Possible

    reserves_subcategory = Column("RESERVES_SUBCAT", String(20), nullable=True)
    # PDP, PDNP, PUD, PROB, POSS

    # Data quality flags
    data_source = Column("DATA_SOURCE", String(50), nullable=True)
    confidence_level = Column("CONFIDENCE_LEVEL", String(10), default="HIGH")  # HIGH, MED, LOW
    review_status = Column("REVIEW_STATUS", String(20), default="UNREVIEWED")  # UNREVIEWED, REVIEWED, APPROVED

    # Booking entity (for regulatory reporting)
    booking_entity = Column("BOOKING_ENTITY", String(100), nullable=True)
    booking_date = Column("BOOKING_DATE", DateTime, nullable=True)
    auditor = Column("AUDITOR", String(100), nullable=True)

    # Notes
    qualifier_notes = Column("QUALIFIER_NOTES", Text, nullable=True)

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    property = relationship("ACProperty", back_populates="qualifiers")

    def __repr__(self):
        return f"<ACQualifier propnum={self.propnum} category={self.reserves_category}>"
