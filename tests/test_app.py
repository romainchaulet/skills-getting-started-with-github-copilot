import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)
original_activities = copy.deepcopy(activities)


def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


@pytest.fixture(autouse=True)
def preserve_activity_state():
    reset_activities()
    yield
    reset_activities()


def build_activity_url(activity_name: str, action: str) -> str:
    quoted_name = quote(activity_name, safe="")
    return f"/activities/{quoted_name}/{action}"


class TestActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self):
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()

        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data
        assert "Gym Class" in activities_data
        assert len(activities_data) == len(original_activities)

    def test_get_activities_contains_required_fields(self):
        response = client.get("/activities")
        activity_data = response.json()["Chess Club"]

        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    def test_signup_success(self):
        response = client.post(
            build_activity_url("Basketball Team", "signup") + "?email=student@test.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_activity_not_found(self):
        response = client.post(
            build_activity_url("Nonexistent Activity", "signup") + "?email=student@test.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_registration(self):
        email = "duplicate-test@test.edu"
        activity = "Soccer Club"

        response1 = client.post(
            build_activity_url(activity, "signup") + f"?email={quote(email)}"
        )
        assert response1.status_code == 200

        response2 = client.post(
            build_activity_url(activity, "signup") + f"?email={quote(email)}"
        )
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Already registered for this activity"

    def test_signup_activity_full(self):
        activity = "Art Studio"
        max_participants = original_activities[activity]["max_participants"]

        for i in range(max_participants):
            response = client.post(
                build_activity_url(activity, "signup") + f"?email=user{i}@test.edu"
            )
            assert response.status_code == 200

        overflow_response = client.post(
            build_activity_url(activity, "signup") + "?email=overflow@test.edu"
        )
        assert overflow_response.status_code == 400
        assert overflow_response.json()["detail"] == "Activity is full"


class TestUnregisterEndpoint:
    def test_unregister_success(self):
        email = "unregister-test@test.edu"
        activity = "Music Ensemble"

        signup_response = client.post(
            build_activity_url(activity, "signup") + f"?email={quote(email)}"
        )
        assert signup_response.status_code == 200

        response = client.delete(
            build_activity_url(activity, "unregister") + f"?email={quote(email)}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_activity_not_found(self):
        response = client.delete(
            build_activity_url("Nonexistent", "unregister") + "?email=student@test.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_participant_not_found(self):
        response = client.delete(
            build_activity_url("Debate Team", "unregister") + "?email=notregistered@test.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Participant not found in this activity"

    def test_unregister_then_signup_again(self):
        email = "reregister@test.edu"
        activity = "Robotics Club"

        signup_response = client.post(
            build_activity_url(activity, "signup") + f"?email={quote(email)}"
        )
        assert signup_response.status_code == 200

        unregister_response = client.delete(
            build_activity_url(activity, "unregister") + f"?email={quote(email)}"
        )
        assert unregister_response.status_code == 200

        second_signup = client.post(
            build_activity_url(activity, "signup") + f"?email={quote(email)}"
        )
        assert second_signup.status_code == 200


class TestRootRedirect:
    def test_root_redirects_to_static_index(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
