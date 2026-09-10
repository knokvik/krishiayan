def test_simulate_deficient_wheat_returns_metrics_and_action(client, auth_headers):
    farm = client.post("/v1/farms", json={"name": "Sim farm"}, headers=auth_headers).json()
    field = client.post(
        f"/v1/farms/{farm['id']}/fields",
        json={"name": "Wheat plot", "crop_code": "wheat", "area_ha": 1.0},
        headers=auth_headers,
    ).json()
    r = client.post(
        f"/v1/simulate?scenario=pune-wheat-n-deficient&field_id={field['id']}",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sim"] is True
    assert body["metrics"]["n_mgkg"] < 250
    assert body["metrics"]["moisture_pct"] > 0
    titles = " ".join(x["title"] for x in body["recommendations"])
    assert "urea" in titles.lower() or "यूरिया" in titles or "युरिया" in titles or "nitrogen" in titles.lower()
    latest = client.get(f"/v1/fields/{field['id']}/latest", headers=auth_headers)
    assert latest.status_code == 200
    assert latest.json()["next_action"]
