async def test_health(client):
    response = await client.get("/admin/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_ready(client):
    response = await client.get("/admin/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_metrics(client):
    response = await client.get("/admin/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
