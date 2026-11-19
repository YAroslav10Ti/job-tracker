import pytest


# ============================================================
# Хелперы
# ============================================================

DEFAULT_PASSWORD = "password123"


async def register(client, email, password=DEFAULT_PASSWORD):
    return await client.post(
        "/api/jobs/register",
        json={"email": email, "password": password},
    )


async def login(client, email, password=DEFAULT_PASSWORD):
    return await client.post(
        "/api/jobs/login",
        json={"email": email, "password": password},
    )


async def get_auth_headers(
    client,
    email="job@example.com",
    password=DEFAULT_PASSWORD,
):
    await register(client, email, password)
    r = await login(client, email, password)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ============================================================
# Фикстуры
# ============================================================

@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    """Celery в тестах не нужен: брокер недоступен."""
    monkeypatch.setattr(
        "app.routers.jobs.calculate_job_statistics.delay",
        lambda *a, **k: None,
    )


# ============================================================
# Метрики / health
# ============================================================

@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "HELP" in r.text  # prometheus всегда отдаёт HELP-комментарии


# ============================================================
# Регистрация
# ============================================================

@pytest.mark.asyncio
async def test_register_and_login(client):
    email = "user@example.com"
    password = "password123"

    r = await register(client, email, password)
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert "id" in r.json()
    assert "hashed_password" not in r.json()

    r = await login(client, email, password)
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client):
    email = "dup@example.com"
    await register(client, email)

    r = await register(client, email)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_short_password_fails(client):
    r = await register(client, "short@example.com", password="1234567")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_fails(client):
    r = await register(client, "not-an-email")
    assert r.status_code == 422


# ============================================================
# Логин
# ============================================================

@pytest.mark.asyncio
async def test_login_with_wrong_password_fails(client):
    email = "wrong@example.com"
    await register(client, email)

    r = await login(client, email, password="wrong-pass-123")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(client):
    r = await login(client, "nobody@example.com")
    assert r.status_code == 400


# ============================================================
# Создание вакансий
# ============================================================

@pytest.mark.asyncio
async def test_create_job(client):
    headers = await get_auth_headers(client, "create1@example.com")

    payload = {
        "company": "Яндекс",
        "position": "Backend Dev",
        "url": "https://example.com/job",
        "status": "Подана заявка",
        "last_date": "2026-11-15",
        "notes": "Ждём ответа",
    }

    r = await client.post("/api/jobs/", json=payload, headers=headers)
    assert r.status_code == 201, r.text

    data = r.json()
    assert data["company"] == "Яндекс"
    assert data["position"] == "Backend Dev"
    assert data["status"] == "Подана заявка"
    assert data["last_date"] == "2026-11-15"
    assert data["notes"] == "Ждём ответа"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_job_with_default_values(client):
    headers = await get_auth_headers(client, "create2@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "X", "position": "Y"},
        headers=headers,
    )
    assert r.status_code == 201

    data = r.json()
    assert data["status"] == "Заинтересован"
    assert data["last_date"] == "Неизвестно"
    assert data["notes"] == ""
    assert data["url"] is None


@pytest.mark.asyncio
async def test_create_job_with_invalid_status_fails(client):
    headers = await get_auth_headers(client, "create3@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "X", "position": "Y", "status": "Ошибка"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_job_without_company_fails(client):
    headers = await get_auth_headers(client, "create4@example.com")

    r = await client.post(
        "/api/jobs/", json={"position": "Y"}, headers=headers
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_job_with_empty_company_fails(client):
    headers = await get_auth_headers(client, "create5@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "", "position": "Y"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_job_with_too_long_company_fails(client):
    headers = await get_auth_headers(client, "create6@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "A" * 101, "position": "Y"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_job_requires_auth(client):
    r = await client.post(
        "/api/jobs/",
        json={"company": "X", "position": "Y"},
    )
    assert r.status_code in (401, 403)


# ============================================================
# Чтение
# ============================================================

@pytest.mark.asyncio
async def test_list_jobs_empty(client):
    headers = await get_auth_headers(client, "list1@example.com")

    r = await client.get("/api/jobs/", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_jobs(client):
    headers = await get_auth_headers(client, "list2@example.com")

    await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P1"},
        headers=headers,
    )
    await client.post(
        "/api/jobs/",
        json={"company": "B", "position": "P2"},
        headers=headers,
    )

    r = await client.get("/api/jobs/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_get_job_by_id(client):
    headers = await get_auth_headers(client, "get1@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P"},
        headers=headers,
    )
    job_id = r.json()["id"]

    r = await client.get(f"/api/jobs/{job_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == job_id
    assert r.json()["company"] == "A"


@pytest.mark.asyncio
async def test_get_nonexistent_job_fails(client):
    headers = await get_auth_headers(client, "get2@example.com")

    r = await client.get("/api/jobs/99999", headers=headers)
    assert r.status_code == 404


# ============================================================
# Обновление
# ============================================================

@pytest.mark.asyncio
async def test_update_job(client):
    headers = await get_auth_headers(client, "upd1@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P"},
        headers=headers,
    )
    job_id = r.json()["id"]

    r = await client.patch(
        f"/api/jobs/{job_id}",
        json={"status": "Собеседование", "notes": "Интервью в среду"},
        headers=headers,
    )
    assert r.status_code == 200

    data = r.json()
    assert data["status"] == "Собеседование"
    assert data["notes"] == "Интервью в среду"
    assert data["company"] == "A"  # не изменилось


@pytest.mark.asyncio
async def test_update_job_with_invalid_status_fails(client):
    headers = await get_auth_headers(client, "upd2@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P"},
        headers=headers,
    )
    job_id = r.json()["id"]

    r = await client.patch(
        f"/api/jobs/{job_id}",
        json={"status": "Нет такого"},
        headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_nonexistent_job_fails(client):
    headers = await get_auth_headers(client, "upd3@example.com")

    r = await client.patch(
        "/api/jobs/99999",
        json={"status": "Собеседование"},
        headers=headers,
    )
    assert r.status_code == 404


# ============================================================
# Удаление
# ============================================================

@pytest.mark.asyncio
async def test_delete_job(client):
    headers = await get_auth_headers(client, "del1@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P"},
        headers=headers,
    )
    job_id = r.json()["id"]

    r = await client.delete(f"/api/jobs/{job_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == job_id

    r = await client.get(f"/api/jobs/{job_id}", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_job_fails(client):
    headers = await get_auth_headers(client, "del2@example.com")

    r = await client.delete("/api/jobs/99999", headers=headers)
    assert r.status_code == 404


# ============================================================
# Поиск
# ============================================================

@pytest.mark.asyncio
async def test_search_jobs_by_position(client):
    headers = await get_auth_headers(client, "search1@example.com")

    await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "Python Developer"},
        headers=headers,
    )
    await client.post(
        "/api/jobs/",
        json={"company": "B", "position": "Java Developer"},
        headers=headers,
    )

    r = await client.get("/api/jobs/?search=Python", headers=headers)
    assert r.status_code == 200

    data = r.json()
    assert len(data) == 1
    assert data[0]["position"] == "Python Developer"


@pytest.mark.asyncio
async def test_search_jobs_no_matches(client):
    headers = await get_auth_headers(client, "search2@example.com")

    await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "Python Developer"},
        headers=headers,
    )

    r = await client.get("/api/jobs/?search=Golang", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


# ============================================================
# Изоляция пользователей
# ============================================================

@pytest.mark.asyncio
async def test_user_cannot_see_other_users_job(client):
    owner = await get_auth_headers(client, "owner@example.com")
    other = await get_auth_headers(client, "other@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "X", "position": "Y"},
        headers=owner,
    )
    job_id = r.json()["id"]

    r = await client.get(f"/api/jobs/{job_id}", headers=other)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_job(client):
    owner = await get_auth_headers(client, "owner2@example.com")
    other = await get_auth_headers(client, "other2@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "X", "position": "Y"},
        headers=owner,
    )
    job_id = r.json()["id"]

    r = await client.patch(
        f"/api/jobs/{job_id}",
        json={"status": "Собеседование"},
        headers=other,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_job(client):
    owner = await get_auth_headers(client, "owner3@example.com")
    other = await get_auth_headers(client, "other3@example.com")

    r = await client.post(
        "/api/jobs/",
        json={"company": "X", "position": "Y"},
        headers=owner,
    )
    job_id = r.json()["id"]

    r = await client.delete(f"/api/jobs/{job_id}", headers=other)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_user_sees_only_own_jobs(client):
    user1 = await get_auth_headers(client, "u1@example.com")
    user2 = await get_auth_headers(client, "u2@example.com")

    await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P1"},
        headers=user1,
    )
    await client.post(
        "/api/jobs/",
        json={"company": "B", "position": "P2"},
        headers=user1,
    )
    await client.post(
        "/api/jobs/",
        json={"company": "C", "position": "P3"},
        headers=user2,
    )

    r1 = await client.get("/api/jobs/", headers=user1)
    r2 = await client.get("/api/jobs/", headers=user2)

    assert len(r1.json()) == 2
    assert len(r2.json()) == 1


# ============================================================
# Защита эндпоинтов
# ============================================================

@pytest.mark.asyncio
async def test_list_jobs_requires_auth(client):
    r = await client.get("/api/jobs/")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    r = await client.get(
        "/api/jobs/",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert r.status_code == 401


# ============================================================
# Статистика и insights
# ============================================================

@pytest.mark.asyncio
async def test_statistics_endpoint(client):
    headers = await get_auth_headers(client, "stat1@example.com")

    r = await client.get("/api/jobs/statistics", headers=headers)
    assert r.status_code == 200

    data = r.json()
    assert "status" in data
    assert data["status"] in ("processing", "ready")


@pytest.mark.asyncio
async def test_insights_empty_for_new_user(client):
    headers = await get_auth_headers(client, "insights1@example.com")

    r = await client.get("/insights/", headers=headers)
    assert r.status_code == 200

    data = r.json()
    assert data["total"] == 0
    assert data["interview"] == 0
    assert data["rejected"] == 0
    assert data["interview_rate"] == 0.0
    assert data["rejection_rate"] == 0.0


@pytest.mark.asyncio
async def test_insights_requires_auth(client):
    r = await client.get("/insights/")
    assert r.status_code in (401, 403)


# ============================================================
# Управление аккаунтом
# ============================================================

@pytest.mark.asyncio
async def test_change_password(client):
    email = "chpwd@example.com"
    old_password = "password123"
    new_password = "newpassword456"

    await register(client, email, old_password)
    r = await login(client, email, old_password)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.patch(
        "/api/jobs/update",
        json={"email": email, "password": new_password},
        headers=headers,
    )
    assert r.status_code == 200

    # Старый пароль больше не работает
    r = await login(client, email, old_password)
    assert r.status_code == 400

    # Новый работает
    r = await login(client, email, new_password)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_email_forbidden(client):
    email = "chpwd2@example.com"
    await register(client, email)
    r = await login(client, email)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.patch(
        "/api/jobs/update",
        json={"email": "other@example.com", "password": "newpassword456"},
        headers=headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_account(client):
    email = "delme@example.com"
    await register(client, email)
    r = await login(client, email)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Создаём вакансию, чтобы проверить каскад
    await client.post(
        "/api/jobs/",
        json={"company": "A", "position": "P"},
        headers=headers,
    )

    r = await client.delete("/api/jobs/me", headers=headers)
    assert r.status_code == 200

    # Логин после удаления невозможен
    r = await login(client, email)
    assert r.status_code == 400