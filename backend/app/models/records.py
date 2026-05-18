from sqlalchemy import Column, BigInteger, String, DateTime, DECIMAL, Date, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class WeightRecord(Base):
    __tablename__ = "weight_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    weight_kg = Column(DECIMAL(5, 2), nullable=False)
    record_date = Column(Date, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())

    user = relationship("User", back_populates="weight_records")


class BodyFatRecord(Base):
    __tablename__ = "body_fat_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body_fat_percent = Column(DECIMAL(5, 2), nullable=False)
    record_date = Column(Date, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())

    user = relationship("User", back_populates="body_fat_records")


class TrainingRecord(Base):
    __tablename__ = "training_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    training_type = Column(String(128))
    duration_minutes = Column(BigInteger)
    intensity = Column(String(64))
    record_date = Column(Date, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())

    user = relationship("User", back_populates="training_records")