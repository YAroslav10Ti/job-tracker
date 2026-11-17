import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    email = "user@example.com"
    password = "password123"

    r = await client.post("/api/jobs/register", json={"email": email, "password": password})
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = await client.post("/api/jobs/login", json={"email": email, "password": password})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_with_wrong_password_fails(client):
    await client.post("/api/jobs/register", json={"email": "a@example.com", "password": "password123"})

    r = await client.post("/api/jobs/login", json={"email": "a@example.com", "password": "wrong-pass"})
    assert r.status_code == 400


async def _auth_headers(client, email="job@example.com"):
    password = "password123"
    await client.post("/api/jobs/register", json={"email": email, "password": password})
    r = await client.post("/api/jobs/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_create_and_list_job(client):
    headers = await _auth_headers(client)

    job = {"company": "Яндекс", "position": "Backend Dev", "status": "Заинтересован"}
    r = await client.post("/api/jobs/", json=job, headers=headers)
    assert r.status_code == 201
    assert r.json()["company"] == "Яндекс"

    r = await client.get("/api/jobs/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_user_cannot_see_other_users_job(client):
    owner = await _auth_headers(client, "owner@example.com")
    other = await _auth_headers(client, "other@example.com")

    r = await client.post("/api/jobs/", json={"company": "X", "position": "Y"}, headers=owner)
    job_id = r.json()["id"]

    r = await client.get(f"/api/jobs/{job_id}", headers=other)
    assert r.status_code == 404