from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, unique=True)
    name = Column(String)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)
    name = Column(String)
    last_price = Column(Float)
    last_stock = Column(Boolean)
    track_price = Column(Boolean, default=True)
    alert_when_instock = Column(Boolean, default=True)
    created_by = Column(Integer)  # chat_id

Base.metadata.create_all(bind=engine)
