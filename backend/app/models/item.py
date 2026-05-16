from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    items = relationship("Item", back_populates="location", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    qr_code = Column(String, unique=True, index=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    min_stock = Column(Integer, default=1, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Location", back_populates="items")

class MovementLog(Base):
    __tablename__ = "item_movements"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    type = Column(String, nullable=False)

    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    notes = Column(String, nullable=True)
    
    item = relationship("Item")

