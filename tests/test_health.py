def test_health(client):
    response = client.get("/admin/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready(client):
    response = client.get("/admin/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics(client):
    response = client.get("/admin/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
