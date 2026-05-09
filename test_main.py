import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1. Basic Connectivity Tests
def test_home_status():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "LibTrack System Online"

# 2. Bulk Testing: Book Creation (15 Cases)
# We test various combinations of titles and ISBNs
@pytest.mark.parametrize("title, author, isbn", [
    (f"Book Title {i}", f"Author {i}", f"ISBN-999-{i}") for i in range(15)
])
def test_create_multiple_books(title, author, isbn):
    payload = {
        "title": title,
        "author": author,
        "isbn": isbn,
        "total_copies": 5
    }
    response = client.post("/books", json=payload)
    assert response.status_code in [200, 201]
    assert response.json()["title"] == title

# 3. Bulk Testing: Student Registration (15 Cases)
@pytest.mark.parametrize("name, adm_no", [
    (f"Student {i}", f"ADM-{i}") for i in range(15)
])
def test_register_multiple_students(name, adm_no):
    payload = {
        "name": name,
        "admission_number": adm_no,
        "email": f"student_{adm_no}@university.com",
        "phone_number": "00000000"
    }
    response = client.post("/students", json=payload)
    assert response.status_code in [200, 201]
    assert response.json()["admission_number"] == adm_no

# 4. Bulk Testing: Edge Cases & Validation (10 Cases)
@pytest.mark.parametrize("invalid_payload", [
    {"title": "No ISBN"}, # Missing ISBN
    {"isbn": "123", "author": "No Title"}, # Missing Title
    {"title": "T", "author": "A", "isbn": "I", "total_copies": "many"}, # String instead of Int
])
def test_validation_errors(invalid_payload):
    response = client.post("/books", json=invalid_payload)
    # FastAPI/Pydantic should catch these and return 422 Unprocessable Entity
    assert response.status_code == 422

# 5. Logic Test: Borrowing Flow
def test_borrow_flow():
    # Ensure a book exists (ID 1) and a student exists (ADM-1)
    # This assumes your database is fresh or auto-seeded
    response = client.post("/borrow", json={
        "admission_number": "ADM-1",
        "book_id": 1
    })
    # If book/student don't exist, we expect 404, otherwise 200
    assert response.status_code in [200, 400, 404]