from datetime import UTC, datetime


def test_simple_ingest(client, auth_headers):
    farm = client.post("/v1/farms", json={"name": "F"}, headers=auth_headers).json()
    field = client.post(
        f"/v1/farms/{farm['id']}/fields",
        json={"name": "P", "crop_code": "wheat"},
        headers=auth_headers,
    ).json()
    client.post(
        "/v1/devices",
        json={"hardware_id": "KA-1", "field_id": field["id"]},
        headers=auth_headers,
    )
    r = client.post(
        "/v1/ingest/scan",
        json={
            "device_id": "KA-1",
            "field_id": field["id"],
            "soil_moisture": 22.5,
            "soil_temperature": 29.1,
            "electrical_conductivity": 0.8,
            "ph": 6.7,
            "soc_proxy": 0.9,
            "battery_level": 3.9,
            "captured_at": datetime.now(UTC).isoformat(),
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["soil_moisture"] == 22.5
    assert body["is_anomaly"] is False
    assert body["features"]["moisture_pct"] == 22.5


def test_rich_probe_packet_and_anomaly(client):
    r = client.post(
        "/v1/ingest/scan",
        json={
            "device_id": "KA-RICH",
            "schema_version": "1.0.0",
            "layers": [
                {
                    "depth_cm": 25,
                    "moisture_raw": 1100,
                    "temp_raw": 29,
                    "ec_raw": 0.7,
                    "optical_660": 0.22,
                    "optical_nir": {"nm_1700": 0.18, "nm_2100": 0.12},
                    "eis_real": [0.5, 0.55, 0.6],
                    "colorimetric_rgb": {"n": [20, 90, 30], "p": [30, 70, 20], "k": [40, 40, 80]},
                    "extraction": {"turbidity_660": 0.22, "filtrate_ok": True},
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    feats = r.json()["features"]
    assert feats["optical_660_corr"] > feats["optical_660_raw"]

    bad = client.post(
        "/v1/ingest/scan",
        json={"device_id": "KA-BAD", "soil_moisture": 99, "soil_temperature": 90, "electrical_conductivity": 40},
    )
    assert bad.status_code == 200
    assert bad.json()["is_anomaly"] is True
