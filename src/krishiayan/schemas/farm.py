from datetime import datetime

from pydantic import BaseModel, Field


class FarmIn(BaseModel):
    name: str
    village: str = ""
    district: str = "Pune"
    state: str = "Maharashtra"
    lat: float = 18.5204
    lon: float = 73.8567


class FarmOut(BaseModel):
    id: str
    name: str
    village: str
    district: str
    state: str
    lat: float
    lon: float

    model_config = {"from_attributes": True}


class FieldIn(BaseModel):
    name: str
    area_ha: float = Field(default=1.0, gt=0)
    soil_class: str = "black_cotton"
    crop_code: str | None = None
    sowing_date: datetime | None = None
    lat: float | None = None
    lon: float | None = None


class FieldOut(BaseModel):
    id: str
    farm_id: str
    name: str
    area_ha: float
    soil_class: str
    crop_id: str | None
    sowing_date: datetime | None
    lat: float | None
    lon: float | None

    model_config = {"from_attributes": True}


class DeviceIn(BaseModel):
    hardware_id: str
    field_id: str | None = None
    firmware_version: str = "0.3.2"


class DeviceOut(BaseModel):
    id: str
    hardware_id: str
    field_id: str | None
    firmware_version: str
    battery_v: float | None
    last_seen: datetime | None

    model_config = {"from_attributes": True}


class CropOut(BaseModel):
    id: str
    code: str
    name_en: str
    name_hi: str
    name_mr: str
    season: str
    duration_days: int

    model_config = {"from_attributes": True}
