import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    # Arrange - no setup needed, activities are pre-populated

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_get_activities_structure():
    # Arrange - no setup needed

    # Act
    response = client.get("/activities")

    # Assert
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    # Arrange
    email = "new_student@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email in activities[activity_name]["participants"]


def test_signup_activity_not_found():
    # Arrange
    email = "student@mergington.edu"
    activity_name = "Nonexistent Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_duplicate_registration():
    # Arrange - michael is already enrolled in Chess Club
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_signup_activity_full():
    # Arrange - fill Chess Club up to its max capacity
    activity_name = "Chess Club"
    participants = activities[activity_name]["participants"]
    max_participants = activities[activity_name]["max_participants"]
    while len(participants) < max_participants:
        participants.append(f"filler{len(participants)}@mergington.edu")

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "late_student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    # Arrange - michael is already enrolled in Chess Club
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_unregister_activity_not_found():
    # Arrange
    email = "student@mergington.edu"
    activity_name = "Nonexistent Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_student_not_signed_up():
    # Arrange - nobody@mergington.edu is not enrolled in Chess Club
    email = "nobody@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "not signed up" in response.json()["detail"].lower()
