"""
Test suite for the FastAPI application

Tests for all API endpoints including:
- GET /activities - retrieve all activities
- POST /activities/{activity_name}/signup - sign up for an activity
- DELETE /activities/{activity_name}/participants - unregister from an activity
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Fixture for creating a test client"""
    return TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_list(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            for field in required_fields:
                assert field in activity_data

    def test_get_activities_contains_expected_activities(self, client):
        """Test that the API returns expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club"
        ]
        
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_participants_are_lists(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_data in data.values():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_valid_activity(self, client):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newemail@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newemail@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        email = "testuser@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Programming Class"]["participants"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with the same email twice fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_returns_correct_message_format(self, client):
        """Test that signup returns properly formatted message"""
        email = "messagetest@mergington.edu"
        activity_name = "Tennis Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity_name in data["message"]


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        email = "unregister@mergington.edu"
        activity_name = "Science Club"
        
        # First sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "removetest@mergington.edu"
        activity_name = "Robotics Club"
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Unregister
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_participant(self, client):
        """Test that unregistering non-existent participant returns 404"""
        response = client.delete(
            "/activities/Music Ensemble/participants",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake Activity/participants",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_activity_name_case_sensitive(self, client):
        """Test that activity names are case sensitive"""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "casetest@mergington.edu"}
        )
        # Should fail because "chess club" != "Chess Club"
        assert response.status_code == 404

    def test_multiple_signups_same_activity(self, client):
        """Test that multiple different users can sign up for the same activity"""
        activity_name = "Basketball Team"
        emails = [
            "user1@mergington.edu",
            "user2@mergington.edu",
            "user3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        response = client.get("/activities")
        activities = response.json()
        for email in emails:
            assert email in activities[activity_name]["participants"]

    def test_email_with_special_characters(self, client):
        """Test signup with special email formats"""
        email = "test.user+special@mergington.edu"
        response = client.post(
            "/activities/Gym Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
