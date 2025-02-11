# tests/controllers/test_challenges_controller.py

import json
import pytest
from unittest.mock import patch, MagicMock

def mock_verify_token(token):
    if token == "valid_token":
        return "user123"
    return None

@pytest.mark.parametrize("endpoint,method", [
    ("/api/challenges/get-challenges-list/physical", "GET"),
    ("/api/challenges/get-challenges-list/workouts", "GET")
])
def test_missing_auth(client, endpoint, method):
    """
    Check missing Authorization => 403 (or 401).
    """
    if method == "GET":
        response = client.get(endpoint)
    # If you had POST endpoints you'd do elif method == "POST": etc.

    assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

def test_invalid_token(client):
    """
    If token is invalid, we expect 403 (or 401).
    """
    with patch("app.controllers.challenges_controller.verify_token_service", return_value=None):
        response = client.get(
            "/api/challenges/get-challenges-list/physical",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert "Invalid token" in response.get_json()["error"]

def test_get_challenges_list_success(client):
    mock_challenges = [
        {"challenge": "Challenge1", "state": False, "id": "doc1"},
        {"challenge": "Challenge2", "state": True, "id": "doc2"}
    ]
    with patch("app.controllers.challenges_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.challenges_controller.get_challenges_list_service", return_value=mock_challenges):
        response = client.get(
            "/api/challenges/get-challenges-list/physical",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json) == 2
    assert resp_json[0]["challenge"] == "Challenge1"

def test_get_challenges_list_failure_service_none(client):
    """
    If the service returns None, we expect 500 (as in the code).
    """
    with patch("app.controllers.challenges_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.challenges_controller.get_challenges_list_service", return_value=None):
        response = client.get(
            "/api/challenges/get-challenges-list/workouts",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 500
    assert "Failed to get challenges" in response.get_json()["error"]

def test_get_challenges_list_exception(client):
    """
    If the controller hits an exception, returns 500.
    """
    with patch("app.controllers.challenges_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.challenges_controller.get_challenges_list_service", side_effect=Exception("Boom!")):
        response = client.get(
            "/api/challenges/get-challenges-list/physical",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]