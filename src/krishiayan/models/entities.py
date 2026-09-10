from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from krishiayan.core.db import Base
from krishiayan.core.security import new_id


def _id() -> str:
    return new_id()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    language: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farms: Mapped[list["Farm"]] = relationship(back_populates="owner")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    village: Mapped[str] = mapped_column(String(255), default="")
    district: Mapped[str] = mapped_column(String(255), default="Pune")
    state: Mapped[str] = mapped_column(String(255), default="Maharashtra")
    lat: Mapped[float] = mapped_column(Float, default=18.5204)
    lon: Mapped[float] = mapped_column(Float, default=73.8567)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="farms")
    fields: Mapped[list["Field"]] = relationship(back_populates="farm", cascade="all, delete-orphan")


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(128))
    name_hi: Mapped[str] = mapped_column(String(128), default="")
    name_mr: Mapped[str] = mapped_column(String(128), default="")
    season: Mapped[str] = mapped_column(String(32), default="kharif")
    duration_days: Mapped[int] = mapped_column(Integer, default=120)
    spec: Mapped[dict] = mapped_column(JSON, default=dict)


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    area_ha: Mapped[float] = mapped_column(Float, default=1.0)
    soil_class: Mapped[str] = mapped_column(String(64), default="black_cotton")
    crop_id: Mapped[str | None] = mapped_column(ForeignKey("crops.id"), nullable=True)
    sowing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm: Mapped[Farm] = relationship(back_populates="fields")
    crop: Mapped[Crop | None] = relationship()
    devices: Mapped[list["Device"]] = relationship(back_populates="field")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    hardware_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    field_id: Mapped[str | None] = mapped_column(ForeignKey("fields.id"), nullable=True, index=True)
    firmware_version: Mapped[str] = mapped_column(String(32), default="0.0.0")
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    battery_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    cal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    field: Mapped[Field | None] = relationship(back_populates="devices")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (UniqueConstraint("device_id", "scan_id", name="uq_device_scan"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    field_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    scan_id: Mapped[str] = mapped_column(String(64), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    soil_moisture: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    electrical_conductivity: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    soc_proxy: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedScan(Base):
    __tablename__ = "processed_scans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    reading_id: Mapped[str] = mapped_column(ForeignKey("sensor_readings.id"), index=True)
    field_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    model_version: Mapped[str] = mapped_column(String(32), default="unfitted")
    n_mgkg: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_mgkg: Mapped[float | None] = mapped_column(Float, nullable=True)
    k_mgkg: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    ec_dsm: Mapped[float | None] = mapped_column(Float, nullable=True)
    moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    soc_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    texture: Mapped[str] = mapped_column(String(32), default="loam")
    n_lo: Mapped[float | None] = mapped_column(Float, nullable=True)
    n_hi: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_lo: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_hi: Mapped[float | None] = mapped_column(Float, nullable=True)
    k_lo: Mapped[float | None] = mapped_column(Float, nullable=True)
    k_hi: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str] = mapped_column(String(16), default="medium")
    soil_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_stress: Mapped[float | None] = mapped_column(Float, nullable=True)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WeatherData(Base):
    __tablename__ = "weather_data"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    field_id: Mapped[str] = mapped_column(String(32), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    valid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain_mm: Mapped[float] = mapped_column(Float, default=0.0)
    rain_forecast_7d_mm: Mapped[float] = mapped_column(Float, default=0.0)
    wind_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    et0_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_wm2: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="open_meteo")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    field_id: Mapped[str] = mapped_column(String(32), index=True)
    scan_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    language: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    field_id: Mapped[str] = mapped_column(String(32), index=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    note: Mapped[str] = mapped_column(Text, default="")
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
