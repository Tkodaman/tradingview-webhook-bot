from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    Role-based user model for Crowdfunding & Copy-Trading platform.
    Roles: ADMIN, DEVELOPER, INVESTOR
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    
    role = Column(String(20), default="INVESTOR", nullable=False) # ADMIN, DEVELOPER, INVESTOR
    is_active = Column(Boolean, default=True)
    
    # Financial fields for Investors
    invested_amount = Column(Float, default=0.0) # How much USD they put in
    current_shares = Column(Float, default=0.0)  # How many pool shares they own
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PlatformSettings(Base):
    """
    Global platform configuration set by Admin.
    """
    __tablename__ = "platform_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_fee_pct = Column(Float, default=20.0) # E.g., 20% of profits go to developer
    is_funding_open = Column(Boolean, default=True)
