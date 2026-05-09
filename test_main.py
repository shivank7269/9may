from fastapi.testclient import TestClient
from main import app

# Create a test client
client = TestClient(app)

def test_home_status():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "LibTrack System Online"}

def test_fetch_logs():
    response = client.get("/logs")
    assert response.status_code == 200
    # Verify that the response is a list (even if it's an empty list)
    assert isinstance(response.json(), list)

def test_invalid_borrow():
    # Test borrowing a book that doesn't exist
    response = client.post("/borrow", json={
        "admission_number": "TEST999",
        "book_id": 99999
    })
    # We expect a 400 Bad Request because the book ID is fake
    assert response.status_code == 400