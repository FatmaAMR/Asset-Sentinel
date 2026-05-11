from sqlalchemy import Column, String, Integer, Float, JSON
# بص التعديل هنا.. بننادي على Base من نفس الفولدر
from .connection import Base 

class DBAsset(Base):
    __tablename__ = "assets"
    asset_id = Column(String, primary_key=True)
    machine_type = Column(String, nullable=False)
    location_floor = Column(Integer)
    location_section = Column(String)
    specifications = Column(JSON)
    status = Column(String, nullable=False)

class DBStaff(Base):
    __tablename__ = "staff"
    staff_id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(String)

class DBThreshold(Base):
    __tablename__ = "threshold_rules"
    rule_id = Column(String, primary_key=True, index=True)
    machine_type = Column(String, nullable=False)
    warning_limit = Column(Float, nullable=False)
    critical_limit = Column(Float, nullable=False)
    updated_by_staff_id = Column(String, nullable=False)