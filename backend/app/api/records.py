from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.records import WeightRecord, BodyFatRecord, TrainingRecord
from app.schemas.records import (
    WeightRecordBase, WeightRecordResponse,
    BodyFatRecordBase, BodyFatRecordResponse,
    TrainingRecordBase, TrainingRecordResponse
)

router_weights = APIRouter(prefix="/api/weights", tags=["weights"])
router_body_fat = APIRouter(prefix="/api/body-fat", tags=["body-fat"])
router_trainings = APIRouter(prefix="/api/trainings", tags=["trainings"])


@router_weights.post("", response_model=WeightRecordResponse)
def create_weight(
    record: WeightRecordBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    weight = WeightRecord(
        user_id=current_user.id,
        weight_kg=record.weight_kg,
        record_date=record.record_date,
        note=record.note
    )
    db.add(weight)
    db.commit()
    db.refresh(weight)
    return weight


@router_weights.get("", response_model=List[WeightRecordResponse])
def list_weights(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(WeightRecord).filter(
        WeightRecord.user_id == current_user.id
    ).order_by(WeightRecord.record_date.desc()).limit(limit).all()


@router_weights.delete("/{record_id}")
def delete_weight(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(WeightRecord).filter(
        WeightRecord.id == record_id,
        WeightRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"message": "Weight record deleted"}


@router_body_fat.post("", response_model=BodyFatRecordResponse)
def create_body_fat(
    record: BodyFatRecordBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    body_fat = BodyFatRecord(
        user_id=current_user.id,
        body_fat_percent=record.body_fat_percent,
        record_date=record.record_date,
        note=record.note
    )
    db.add(body_fat)
    db.commit()
    db.refresh(body_fat)
    return body_fat


@router_body_fat.get("", response_model=List[BodyFatRecordResponse])
def list_body_fat(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(BodyFatRecord).filter(
        BodyFatRecord.user_id == current_user.id
    ).order_by(BodyFatRecord.record_date.desc()).limit(limit).all()


@router_body_fat.delete("/{record_id}")
def delete_body_fat(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(BodyFatRecord).filter(
        BodyFatRecord.id == record_id,
        BodyFatRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"message": "Body fat record deleted"}


@router_trainings.post("", response_model=TrainingRecordResponse)
def create_training(
    record: TrainingRecordBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    training = TrainingRecord(
        user_id=current_user.id,
        training_type=record.training_type,
        duration_minutes=record.duration_minutes,
        intensity=record.intensity,
        record_date=record.record_date,
        note=record.note
    )
    db.add(training)
    db.commit()
    db.refresh(training)
    return training


@router_trainings.get("", response_model=List[TrainingRecordResponse])
def list_trainings(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(TrainingRecord).filter(
        TrainingRecord.user_id == current_user.id
    ).order_by(TrainingRecord.record_date.desc()).limit(limit).all()


@router_trainings.delete("/{record_id}")
def delete_training(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(TrainingRecord).filter(
        TrainingRecord.id == record_id,
        TrainingRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"message": "Training record deleted"}