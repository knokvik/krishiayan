from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from krishiayan.api.deps import get_current_user
from krishiayan.core.db import get_db
from krishiayan.models.entities import Crop, Device, Farm, Field, User
from krishiayan.schemas.farm import (
    CropOut,
    DeviceIn,
    DeviceOut,
    FarmIn,
    FarmOut,
    FieldIn,
    FieldOut,
)

router = APIRouter(prefix="/v1", tags=["farms"])


def _owned_farm(db: Session, user: User, farm_id: str) -> Farm:
    farm = db.get(Farm, farm_id)
    if farm is None or farm.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


def _owned_field(db: Session, user: User, field_id: str) -> Field:
    field = db.get(Field, field_id)
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    farm = db.get(Farm, field.farm_id)
    if farm is None or farm.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


@router.get("/crops", response_model=list[CropOut])
def list_crops(db: Session = Depends(get_db)) -> list[Crop]:
    return db.query(Crop).order_by(Crop.code).all()


@router.post("/farms", response_model=FarmOut)
def create_farm(body: FarmIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Farm:
    farm = Farm(owner_id=user.id, **body.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/farms", response_model=list[FarmOut])
def list_farms(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Farm]:
    return db.query(Farm).filter(Farm.owner_id == user.id).all()


@router.get("/farms/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Farm:
    return _owned_farm(db, user, farm_id)


@router.post("/farms/{farm_id}/fields", response_model=FieldOut)
def create_field(
    farm_id: str,
    body: FieldIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Field:
    farm = _owned_farm(db, user, farm_id)
    data = body.model_dump()
    crop_code = data.pop("crop_code")
    crop_id = None
    if crop_code:
        crop = db.query(Crop).filter(Crop.code == crop_code).first()
        if crop is None:
            raise HTTPException(status_code=400, detail=f"Unknown crop {crop_code}")
        crop_id = crop.id
    field = Field(farm_id=farm.id, crop_id=crop_id, **data)
    if field.lat is None:
        field.lat = farm.lat
    if field.lon is None:
        field.lon = farm.lon
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.get("/farms/{farm_id}/fields", response_model=list[FieldOut])
def list_fields(farm_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Field]:
    _owned_farm(db, user, farm_id)
    return db.query(Field).filter(Field.farm_id == farm_id).all()


@router.get("/fields/{field_id}", response_model=FieldOut)
def get_field(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Field:
    return _owned_field(db, user, field_id)


@router.post("/devices", response_model=DeviceOut)
def register_device(
    body: DeviceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Device:
    if body.field_id:
        _owned_field(db, user, body.field_id)
    existing = db.query(Device).filter(Device.hardware_id == body.hardware_id).first()
    if existing:
        existing.field_id = body.field_id
        existing.firmware_version = body.firmware_version
        db.commit()
        db.refresh(existing)
        return existing
    device = Device(
        hardware_id=body.hardware_id,
        field_id=body.field_id,
        firmware_version=body.firmware_version,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/devices", response_model=list[DeviceOut])
def list_devices(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Device]:
    farm_ids = [f.id for f in db.query(Farm).filter(Farm.owner_id == user.id).all()]
    field_ids = [x.id for x in db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()] if farm_ids else []
    if not field_ids:
        return []
    return db.query(Device).filter(Device.field_id.in_(field_ids)).all()
