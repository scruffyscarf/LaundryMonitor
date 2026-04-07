def test_login_success(client):
    r = client.post("/auth/login", json={"password": "admin123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


def test_login_failure(client):
    r = client.post("/auth/login", json={"password": "wrong"})
    assert r.status_code == 401


def test_create_machine_requires_auth(client, seed_machines):
    r = client.post(
        "/machines/",
        json={"name": "Extra Washer", "type": "wash"},
    )
    assert r.status_code == 403


def test_create_and_update_machine_with_token(client, seed_machines):
    token = client.post("/auth/login", json={"password": "admin123"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/machines/",
        json={"name": "Extra Washer", "type": "wash"},
        headers=headers,
    )
    assert r.status_code == 200
    mid = r.json()["id"]

    r2 = client.put(
        f"/machines/{mid}/",
        json={"name": "Extra Washer Renamed", "type": "dry"},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["name"] == "Extra Washer Renamed"
    assert r2.json()["type"] == "Dry"
