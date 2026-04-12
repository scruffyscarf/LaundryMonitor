def test_get_machines_empty(client):
    response = client.get("/machines/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_report_free_without_time(client, seed_machines):
    """Тест для отчета о свободной машине без указания времени"""
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
    """Тест для отчета о занятой машине с указанием времени"""
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


def test_get_history(client, seed_machines):
    # Проверяем, что машина существует
    machines_response = client.get("/machines/")
    assert machines_response.status_code == 200
    machines = machines_response.json()
    machine_ids = [m["id"] for m in machines]
    assert 1 in machine_ids, "Machine with id=1 not found in database"
    
    # Создаем репорт
    post_response = client.post("/report/", json={
        "machine_id": 1,
        "status": "free"
    })
    assert post_response.status_code == 200, f"Failed to create report: {post_response.text}"
    
    # Получаем историю
    response = client.get("/machines/1/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1, "History should contain at least one report"


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


def test_history_limit(client, seed_machines):
    for _ in range(15):
        client.post("/report/", json={
            "machine_id": 1,
            "status": "free"
        })

    response = client.get("/machines/1/history")
    data = response.json()

    assert len(data) == 10


def test_busy_without_time(client, seed_machines):
    # Проверяем, что можно создать отчет busy без time_remaining
    report_resp = client.post("/report/", json={
        "machine_id": 1,
        "status": "busy"
    })
    
    # Должно быть 200, так как time_remaining опционален
    assert report_resp.status_code == 200
    
    # Получаем статус машин
    response = client.get("/machines/")
    data = response.json()
    
    # Находим машину с id=1
    machine = next((m for m in data if m["id"] == 1), None)
    assert machine is not None
    # Статус должен быть Busy или Probably_Free (в зависимости от времени)
    assert machine["status"] in ["Busy", "Probably_Free"]
