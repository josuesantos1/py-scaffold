def test_admin_endpoint(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert response.json() == {"admin": "Hello"}
