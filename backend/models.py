import sqlalchemy

from sqlalchemy import Column, Integer, String, JSON, DateTime, create_engine, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

Base = declarative_base()
    
def get_expiry_time():
    return datetime.now(timezone.utc)+timedelta(days=30)

class station_info(Base):
    
    __tablename__ = "station_info"
    
    id = Column(String, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=False)
    stop_lat = Column(Float, nullable=False)
    stop_long = Column(Float, nullable=False)
    stop_lat_raw = Column(String)
    stop_long_raw = Column(String)
    def __repr__(self):
        return f"<station_info(id='{self.id}', name='{self.name}')>"

