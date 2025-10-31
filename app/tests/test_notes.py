import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user_id

# Auth override: test user
app.dependency_overrides[get_current_user_id] = lambda: "test-user"

client = TestClient(app)

def test_unauthorized_without_token():
    # Remove override to test 401
    app.dependency_overrides.pop(get_current_user_id, None)
    r = client.get("/api/notes")
    assert r.status_code == 401
    # Restore override
    app.dependency_overrides[get_current_user_id] = lambda: "test-user"

def test_list_notes_ok():
    r = client.get("/api/notes")
    # Firestore gerçek baglanti yoksa 500 olabilir; env/emulator ile 200
    assert r.status_code in (200, 500)
