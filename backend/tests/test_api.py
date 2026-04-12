def test_get_machines_empty(client):
    response = client.get("/machines/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_report_free_without_time(client, seed_machines):
    payload = {
        "machine_id": 1,
        "status": "free"
    }
    response = client.post("/report/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == 1
    assert data["status"] == "free"
    assert data["time_remaining"] is None


def test_post_report_busy_with_time(client, seed_machines):
    payload = {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 10
    }
    response = client.post("/report/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == 1
    assert data["status"] == "busy"
    assert data["time_remaining"] == 10


def test_post_report_zero_time(client, seed_machines):
    payload = {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 0
    }
    response = client.post("/report/", json=payload)
    assert response.status_code == 403
    assert "cannot be leq 0" in response.json()["detail"]


def test_post_report_negative_time(client, seed_machines):
    payload = {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": -5
    }
    response = client.post("/report/", json=payload)
    assert response.status_code == 403
    assert "cannot be leq 0" in response.json()["detail"]


def test_post_report_exceeds_max_time(client, seed_machines):
    payload = {
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 301
    }
    response = client.post("/report/", json=payload)
    assert response.status_code == 403
    assert "cannot exceed 300" in response.json()["detail"]


def test_get_history(client, seed_machines):
    client.post("/report/", json={"machine_id": 1, "status": "free"})

    response = client.get("/machines/1/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    report = data[0]
    assert "machine_id" in report
    assert "status" in report


def test_get_history_machine_not_found(client):
    response = client.get("/machines/999/history")
    assert response.status_code == 404
    assert "Machine not found or no reports" in response.json()["detail"]


def test_get_machines_with_data(client, seed_machines):
    client.post("/report/", json={"machine_id": 1, "status": "busy", "time_remaining": 10})

    response = client.get("/machines/")
    data = response.json()

    assert len(data) > 0
    machine = next((m for m in data if m["id"] == 1), None)
    assert machine is not None
    assert machine["status"] in ["Busy", "Free"]


def test_invalid_report(client):
    response = client.post("/report/", json={
        "machine_id": "bad",
        "status": "busy"
    })
    assert response.status_code == 422


def test_history_limit(client, seed_machines):
    for _ in range(15):
        client.post("/report/", json={"machine_id": 1, "status": "free"})

    response = client.get("/machines/1/history")
    data = response.json()
    assert len(data) == 10


def test_busy_without_time(client, seed_machines):
    client.post("/report/", json={"machine_id": 1, "status": "busy"})

    response = client.get("/machines/")
    data = response.json()

    machine = next((m for m in data if m["id"] == 1), None)
    assert machine is not None
    assert machine["status"] in ["Busy", "Probably_Free"]


def test_create_machine_with_token(client, seed_machines):
    token = client.post("/auth/login", json={"password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/machines/",
        json={"name": "Brand New", "type": "wash"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Brand New"


def test_create_machine_duplicate_name(client, seed_machines):
    token = client.post("/auth/login", json={"password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r1 = client.post("/machines/", json={"name": "Duplicate", "type": "wash"}, headers=headers)
    assert r1.status_code == 200

    r2 = client.post("/machines/", json={"name": "Duplicate", "type": "dry"}, headers=headers)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"]


def test_update_machine_not_found(client, seed_machines):
    token = client.post("/auth/login", json={"password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/machines/999/", json={"name": "Ghost", "type": "wash"}, headers=headers
        )

    assert response.status_code == 404
