def test_register_login_me(client):
    r = client.post(
        "/v1/auth/register",
        json={"email": "a@b.com", "password": "password1", "full_name": "A"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@b.com"

    bad = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "wrongpass"})
    assert bad.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/v1/auth/me").status_code == 401
