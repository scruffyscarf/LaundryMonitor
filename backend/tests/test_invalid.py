def test_report_invalid_machine_id(client):
    response = client.post("/report/", json={
        "machine_id": "abc",
        "status": "busy"
    })
    assert response.status_code == 422


def test_negative_time_remaining(client):
    response = client.post("/report/", json={
        "machine_id": 1,
        "status": "busy",
        "time_remaining": -10
    })
    assert response.status_code == 422


def test_busy_without_time_edge(client):
    response = client.post("/report/", json={
        "machine_id": 1,
        "status": "busy"
    })
    assert response.status_code == 200