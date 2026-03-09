"""
AC_PROJECT — Project/Group definitions for organizing properties.
In ARIES, projects are used to group properties for roll-up analysis.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


# Association table: many-to-many between projects and properties
project_property = Table(
    "AC_PROJECT_PROPERTY",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("AC_PROJECT.id"), primary_key=True),
    Column("propnum", String(20), ForeignKey("AC_PROPERTY.PROPNUM"), primary_key=True),
    Column("weight_factor", Float, default=1.0),   # For weighted roll-ups
    Column("sort_order", Integer, default=0),
)


class ACProject(Base):
    __tablename__ = "AC_PROJECT"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Project identification
    project_name = Column("PROJECT_NAME", String(100), nullable=False, unique=True)
    project_code = Column("PROJECT_CODE", String(20), nullable=True, unique=True)
    description = Column("DESCRIPTION", Text, nullable=True)

    # Project type
    project_type = Column("PROJECT_TYPE", String(30), default="WORKING")  # WORKING, BUDGET, ACQUISITION
    parent_project_id = Column("PARENT_PROJECT_ID", Integer, ForeignKey("AC_PROJECT.id"), nullable=True)

    # Roll-up settings
    default_scenario = Column("DEFAULT_SCENARIO", String(50), nullable=True)
    consolidation_method = Column("CONSOLIDATION_METHOD", String(20), default="SUM")  # SUM, WEIGHTED

    # Economic defaults
    default_discount_rate = Column("DEFAULT_DISCOUNT_RATE", Float, default=10.0)
    econ_start_date = Column("ECON_START_DATE", DateTime, nullable=True)
    econ_end_date = Column("ECON_END_DATE", DateTime, nullable=True)

    # Status
    is_active = Column("IS_ACTIVE", Boolean, default=True)
    is_locked = Column("IS_LOCKED", Boolean, default=False)

    # Audit
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column("CREATED_BY", String(50), nullable=True)

    # Relationships
    scenarios = relationship("ACScenario", back_populates="project", cascade="all, delete-orphan")
    sub_projects = relationship("ACProject", backref="parent", foreign_keys=[parent_project_id])

    def __repr__(self):
        return f"<ACProject id={self.id} name={self.project_name}>"
