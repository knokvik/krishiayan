from datetime import datetime

from pydantic import BaseModel, Field


class Gps(BaseModel):
    lat: float
    lon: float
    alt_m: float | None = None
    hdop: float | None = None


class Extraction(BaseModel):
    solvent: str = "2-propanol"
    ratio: float = 0.10
    nacl_pct: float = 30
    turbidity_660: float | None = None
    filtrate_ok: bool = True


class Layer(BaseModel):
    depth_cm: float = 15
    moisture_raw: float | None = None
    temp_raw: float | None = None
    ec_raw: float | None = None
    eis_real: list[float] = Field(default_factory=list)
    eis_imag: list[float] = Field(default_factory=list)
    optical_660: float | None = None
    optical_nir: dict[str, float] = Field(default_factory=dict)
    colorimetric_rgb: dict[str, list[int]] = Field(default_factory=dict)
    enose: list[float] = Field(default_factory=list)
    extraction: Extraction | None = None
    # already-calibrated fallbacks (simple hardware)
    soil_moisture: float | None = None
    soil_temperature: float | None = None
    electrical_conductivity: float | None = None
    ph: float | None = None
    soc_proxy: float | None = None


class ProbePacket(BaseModel):
    """Accepts both the simple hardware JSON and the full Krishiayan probe packet."""

    schema_version: str = "1.0.0"
    device_id: str
    firmware_version: str = "0.0.0"
    scan_id: str | None = None
    captured_at: datetime | None = None
    gps: Gps | None = None
    plot_id: str | None = None
    field_id: str | None = None
    operator_id: str | None = None
    depth_cm_tip: float | None = None
    battery_v: float | None = None
    battery_level: float | None = None
    solar_mw: float | None = None
    rssi_dbm: float | None = None
    flags: dict = Field(default_factory=dict)

    # simple top-level fields (user prompt)
    soil_moisture: float | None = None
    soil_temperature: float | None = None
    electrical_conductivity: float | None = None
    ph: float | None = None
    soc_proxy: float | None = None
    organics: float | None = None

    layers: list[Layer] = Field(default_factory=list)
    camera: dict | None = None
    raw_extra: dict = Field(default_factory=dict)

    def normalized_layers(self) -> list[Layer]:
        if self.layers:
            return self.layers
        return [
            Layer(
                depth_cm=self.depth_cm_tip or 20,
                soil_moisture=self.soil_moisture,
                soil_temperature=self.soil_temperature,
                electrical_conductivity=self.electrical_conductivity,
                ph=self.ph,
                soc_proxy=self.soc_proxy if self.soc_proxy is not None else self.organics,
            )
        ]
