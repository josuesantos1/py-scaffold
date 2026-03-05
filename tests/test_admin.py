async def test_admin_endpoint(client):
    response = await client.get("/admin/")
    assert response.status_code == 200
    assert response.json() == {"admin": "Hello"}
