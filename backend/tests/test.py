from fastapi.testclient import TestClient
from app.main import app


job_payload = {
    "company": "Google",
    "position": "Python Developer",
    "url": "https://example.com/jobs/python-developer",
    "status": "Заинтересован",
    "notes": "Изучить требования к вакансии",
}


def create_job(client, payload=None):
    """Вспомогательная функция для создания вакансии."""
    response = client.post(
        "/api/jobs/",
        json=payload or job_payload,
    )
    assert response.status_code == 201
    return response.json()



def test_health():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200



def test_create_job(client):
    response = client.post("/api/jobs/", json=job_payload)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["company"] == job_payload["company"]
    assert data["position"] == job_payload["position"]
    assert data["url"] == job_payload["url"]
    assert data["status"] == job_payload["status"]
    assert data["notes"] == job_payload["notes"]


def test_create_job_with_default_values(client):
    payload = {
        "company": "Yandex",
        "position": "Backend Developer",
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["company"] == "Yandex"
    assert data["position"] == "Backend Developer"
    assert data["status"] == "Заинтересован"
    assert data["notes"] == ""


def test_create_job_with_invalid_status(client):
    payload = {
        "company": "Google",
        "position": "Python Developer",
        "status": "ошибка",
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_create_job_without_company(client):
    payload = {
        "position": "Python Developer",
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_create_job_without_position(client):
    payload = {
        "company": "Google",
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_create_job_with_empty_company(client):
    payload = {
        "company": "",
        "position": "Python Developer",
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_create_job_with_too_long_company(client):
    payload = {
        "company": "A" * 101,
        "position": "Python Developer",
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422




def test_get_jobs_empty_list(client):
    response = client.get("/api/jobs/")

    assert response.status_code == 200
    assert response.json() == []


def test_get_jobs(client):
    create_job(client)

    second_payload = {
        "company": "Yandex",
        "position": "Backend Developer",
        "url": "https://example.com/yandex",
        "status": "Подана заявка",
        "notes": "Отправил резюме",
    }
    create_job(client, second_payload)

    response = client.get("/api/jobs/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["company"] == "Google"
    assert data[1]["company"] == "Yandex"




def test_search_jobs_by_position(client):
    create_job(client)

    second_payload = {
        "company": "Yandex",
        "position": "Java Developer",
        "status": "Подана заявка",
    }
    create_job(client, second_payload)

    response = client.get(
        "/api/jobs/",
        params={"search": "Python"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["position"] == "Python Developer"


def test_search_jobs_without_matches(client):
    create_job(client)

    response = client.get(
        "/api/jobs/",
        params={"search": "Несуществующая компания"},
    )

    assert response.status_code == 200
    assert response.json() == []




def test_get_job_by_id(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == job_id
    assert data["company"] == job_payload["company"]
    assert data["position"] == job_payload["position"]


def test_get_nonexistent_job(client):
    response = client.get("/api/jobs/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"




def test_update_job(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    update_payload = {
        "company": "Google",
        "position": "Senior Python Developer",
        "status": "Собеседование",
        "notes": "Назначено техническое интервью",
    }

    response = client.patch(
        f"/api/jobs/{job_id}",
        json=update_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == job_id
    assert data["company"] == "Google"
    assert data["position"] == "Senior Python Developer"
    assert data["status"] == "Собеседование"
    assert data["notes"] == "Назначено техническое интервью"


def test_update_only_status(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    response = client.patch(
        f"/api/jobs/{job_id}",
        json={"status": "Отклонена"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Отклонена"
    assert data["company"] == job_payload["company"]
    assert data["position"] == job_payload["position"]


def test_update_nonexistent_job(client):
    response = client.patch(
        "/api/jobs/99999",
        json={"status": "Собеседование"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_update_job_with_invalid_status(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    response = client.patch(
        f"/api/jobs/{job_id}",
        json={"status": "Неизвестный статус"},
    )

    assert response.status_code == 422


def test_update_job_with_empty_company(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    response = client.patch(
        f"/api/jobs/{job_id}",
        json={"company": ""},
    )

    assert response.status_code == 422




def test_delete_job(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    response = client.delete(f"/api/jobs/{job_id}")

    assert response.status_code == 200


def test_deleted_job_is_not_found(client):
    created_job = create_job(client)
    job_id = created_job["id"]

    delete_response = client.delete(f"/api/jobs/{job_id}")

    assert delete_response.status_code == 200

    get_response = client.get(f"/api/jobs/{job_id}")

    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Job not found"


def test_delete_nonexistent_job(client):
    response = client.delete("/api/jobs/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"