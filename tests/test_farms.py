def test_farm_field_device_flow(client, auth_headers):
    crops = client.get("/v1/crops")
    assert crops.status_code == 200
    codes = {c["code"] for c in crops.json()}
    assert "wheat" in codes
    assert "soybean" in codes

    farm = client.post(
        "/v1/farms",
        json={"name": "Pune demo farm", "village": "Alandi"},
        headers=auth_headers,
    )
    assert farm.status_code == 200, farm.text
    farm_id = farm.json()["id"]

    field = client.post(
        f"/v1/farms/{farm_id}/fields",
        json={"name": "Plot A", "area_ha": 1.2, "crop_code": "wheat", "soil_class": "black_cotton"},
        headers=auth_headers,
    )
    assert field.status_code == 200, field.text
    field_id = field.json()["id"]

    device = client.post(
        "/v1/devices",
        json={"hardware_id": "KA-PROBE-0001", "field_id": field_id},
        headers=auth_headers,
    )
    assert device.status_code == 200
    assert device.json()["hardware_id"] == "KA-PROBE-0001"

    listed = client.get(f"/v1/farms/{farm_id}/fields", headers=auth_headers)
    assert len(listed.json()) == 1
