import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


def test_get_activities_returns_seeded_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_new_participant(client):
    email = "new.student@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_existing_participant(client):
    activity_name = "Programming Class"
    existing_email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {existing_email} from {activity_name}"
    }
    assert existing_email not in activities[activity_name]["participants"]


def test_unregister_rejects_non_registered_participant(client):
    response = client.delete(
        "/activities/Programming Class/signup",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_then_unregister_updates_participants_membership(client):
    activity_name = "Gym Class"
    email = "roundtrip.student@mergington.edu"

    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    unregister_response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert email not in activities[activity_name]["participants"]
