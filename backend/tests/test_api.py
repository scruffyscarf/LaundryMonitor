def test_get_machines_empty(client):
    response = client.get("/machines/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_report(client):
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


def test_get_history(client):
    client.post("/report/", json={
        "machine_id": 1,
        "status": "free"
    })

    response = client.get("/machines/1/history")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_machines_with_data(client, seed_machines):
    client.post("/report/", json={
        "machine_id": 1,
        "status": "busy",
        "time_remaining": 10
    })

    response = client.get("/machines/")
    data = response.json()

    assert len(data) > 0


def test_invalid_report(client):
    response = client.post("/report/", json={
        "machine_id": "bad",
        "status": "busy"
    })

    assert response.status_code == 422


def test_history_limit(client):
    for _ in range(15):
        client.post("/report/", json={
            "machine_id": 1,
            "status": "free"
        })

    response = client.get("/machines/1/history")
    data = response.json()

    assert len(data) == 10


def test_busy_without_time(client, seed_machines):
    client.post("/report/", json={
        "machine_id": 1,
        "status": "busy"
    })

    response = client.get("/machines/")
    data = response.json()

    assert data[0]["status"] in ["Busy", "Probably_Free"]
