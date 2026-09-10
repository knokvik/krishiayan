import httpx
from sqlalchemy.orm import Session

from krishiayan.models.entities import Field
from krishiayan.services.agronomy_features import moisture_deficit, soil_health_score, water_stress_index
from krishiayan.services.weather import summarize, weather_for_field


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def get(self, url, params=None):
        return _FakeResp(
            {
                "daily": {
                    "temperature_2m_max": [34, 33, 32, 31, 30, 29, 28],
                    "temperature_2m_min": [22, 21, 21, 20, 20, 19, 19],
                    "precipitation_sum": [0, 12, 0, 0, 2, 0, 0],
                    "et0_fao_evapotranspiration": [5.5, 5.1, 4.8, 4.4, 4.0, 3.8, 3.5],
                    "wind_speed_10m_max": [12, 10, 8, 8, 9, 7, 6],
                    "shortwave_radiation_sum": [220, 200, 180, 190, 210, 205, 198],
                },
                "hourly": {"relative_humidity_2m": [48]},
            }
        )


def test_summarize_rain_forecast():
    payload = _FakeClient().get("x").json()
    s = summarize(payload)
    assert s["rain_forecast_7d_mm"] == 14
    assert s["rain_next_48h_mm"] == 12


def test_weather_for_field_uses_cache(db: Session, client, auth_headers):
    farm = client.post("/v1/farms", json={"name": "Wx"}, headers=auth_headers).json()
    field_json = client.post(
        f"/v1/farms/{farm['id']}/fields",
        json={"name": "P", "crop_code": "wheat"},
        headers=auth_headers,
    ).json()
    field = db.get(Field, field_json["id"])
    a = weather_for_field(db, field, client=_FakeClient())
    b = weather_for_field(db, field, client=_FakeClient())
    assert a["cached"] is False
    assert b["cached"] is True


def test_agronomy_indices():
    assert moisture_deficit(10, 18, 32) > 0
    assert water_stress_index(10, 18, 32, et0_mm=6, rain_48h=0) > 0.3
    score = soil_health_score(
        moisture_pct=24, ph=6.7, ec=0.6, soc=0.9, n_idx=1.0, p_idx=1.0, k_idx=1.0
    )
    assert score > 80
