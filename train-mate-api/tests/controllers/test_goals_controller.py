import pytest
import json
from unittest.mock import patch, MagicMock

def mock_verify_token(token):
    """Mock verify_token_service to return 'user123' only if token == 'valid_token'."""
    return "user123" if token == "valid_token" else None

# Parametrize all endpoints requiring auth
@pytest.mark.parametrize("endpoint,method", [
    ("/api/goals/get-all-goals", "GET"),
    ("/api/goals/create-goal", "POST"),
    ("/api/goals/get-goal/fake_goal_id", "GET"),
    ("/api/goals/update-goal/fake_goal_id", "PUT"),
    ("/api/goals/delete-goal/fake_goal_id", "DELETE"),
    ("/api/goals/complete-goal/fake_goal_id", "PATCH"),
])
def test_missing_auth(client, endpoint, method):
    """
    When Authorization header is missing or malformed, we expect 403 or 401.
    Your code specifically returns 403 for missing token.
    """
    if method == "GET":
        resp = client.get(endpoint)
    elif method == "POST":
        resp = client.post(endpoint)
    elif method == "PUT":
        resp = client.put(endpoint)
    elif method == "DELETE":
        resp = client.delete(endpoint)
    elif method == "PATCH":
        resp = client.patch(endpoint)

    # Code raises 403 for missing token
    assert resp.status_code == 403
    assert "Authorization token missing" in resp.get_json()["error"]

def test_get_all_goals_success(client):
    """GET /get-all-goals => 200 on success with a list of goals."""
    mock_goals = [
        {"id": "g1", "title": "Goal 1"},
        {"id": "g2", "title": "Goal 2"}
    ]
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.get_all_goals_service", return_value=mock_goals):
        
        resp = client.get(
            "/api/goals/get-all-goals",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
    assert resp.get_json()[0]["id"] == "g1"

def test_get_all_goals_service_none(client):
    """If get_all_goals_service returns None => 500."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.get_all_goals_service", return_value=None):
        
        resp = client.get(
            "/api/goals/get-all-goals",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Failed to get goals" in resp.get_json()["error"]

def test_get_all_goals_invalid_token(client):
    """If token is invalid => 403."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value=None):
        resp = client.get(
            "/api/goals/get-all-goals",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 403
    assert "Invalid token" in resp.get_json()["error"]

def test_create_goal_success(client):
    """POST /create-goal => 201 if goal creation is successful."""
    mock_goal_data = {
        "id": "new_goal_id",
        "title": "New Goal",
        "description": "Test Desc",
        "completed": False
    }
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.create_goal_service", return_value=mock_goal_data):
        
        resp = client.post(
            "/api/goals/create-goal",
            data=json.dumps({"title": "New Goal", "description": "Test Desc"}),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 201
    assert resp.get_json()["id"] == "new_goal_id"

def test_create_goal_invalid_data(client):
    """If data is missing => 400. (Simulated by empty body or minimal data.)"""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"):
        resp = client.post(
            "/api/goals/create-goal",
            data=json.dumps({}),  # no data
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 400
    assert "Invalid data" in resp.get_json()["error"]

def test_create_goal_service_tuple_400(client):
    """
    If create_goal_service returns ({"error":"something"}, 400),
    the controller should pass that along.
    """
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.create_goal_service", return_value=({"error":"Some date error"}, 400)):
        
        resp = client.post(
            "/api/goals/create-goal",
            data=json.dumps({"title": "Goal with bad date", "startDate":"2020-01-01"}),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 400
    assert "Some date error" in resp.get_json()["error"]

def test_create_goal_service_none(client):
    """If create_goal_service returns None => 500."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.create_goal_service", return_value=None):
        
        resp = client.post(
            "/api/goals/create-goal",
            data=json.dumps({"title": "Goal", "description":"testdesc"}),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Failed to create goal" in resp.get_json()["error"]

def test_get_goal_success(client):
    """GET /get-goal/<goal_id> => 200 if found."""
    mock_goal = {"id": "g1", "title": "MyGoal"}
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.get_goal_service", return_value=mock_goal):
        
        resp = client.get(
            "/api/goals/get-goal/g1",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert resp.get_json()["id"] == "g1"

def test_get_goal_not_found(client):
    """If get_goal_service returns None => 404."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.get_goal_service", return_value=None):
        
        resp = client.get(
            "/api/goals/get-goal/g_notfound",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 404
    assert "Goal not found" in resp.get_json()["error"]

def test_update_goal_success(client):
    """PUT /update-goal/<goal_id> => 200 if success."""
    mock_updated_goal = {
        "id": "g123",
        "title": "Updated Title",
        "description": "Updated Desc"
    }
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.update_goal_service", return_value=mock_updated_goal):
        
        resp = client.put(
            "/api/goals/update-goal/g123",
            data=json.dumps({"title": "Updated Title", "description":"Updated Desc"}),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert resp.get_json()["id"] == "g123"

def test_update_goal_invalid_data(client):
    """If we pass no data => 400."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"):
        resp = client.put(
            "/api/goals/update-goal/g123",
            data=json.dumps({}),  # no fields
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 400
    assert "Invalid data" in resp.get_json()["error"]

def test_update_goal_service_failure(client):
    """If update_goal_service returns None => 500."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.update_goal_service", return_value=None):
        
        resp = client.put(
            "/api/goals/update-goal/g123",
            data=json.dumps({"title":"new title"}),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Failed to update goal" in resp.get_json()["error"]

def test_delete_goal_success(client):
    """DELETE /delete-goal/<goal_id> => 200 if success."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.delete_goal_service", return_value=True):
        
        resp = client.delete(
            "/api/goals/delete-goal/gABC",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Goal deleted successfully"

def test_delete_goal_service_failure(client):
    """If delete_goal_service returns False => 500."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.delete_goal_service", return_value=False):
        
        resp = client.delete(
            "/api/goals/delete-goal/g999",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Failed to delete goal" in resp.get_json()["error"]

def test_complete_goal_success(client):
    """PATCH /complete-goal/<goal_id> => 200 if success."""
    mock_completed_goal = {"id": "g123", "completed": True}
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.complete_goal_service", return_value=mock_completed_goal):
        
        resp = client.patch(
            "/api/goals/complete-goal/g123",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert resp.get_json()["completed"] is True

def test_complete_goal_service_failure(client):
    """If complete_goal_service returns None => 500."""
    with patch("app.controllers.goals_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.goals_controller.complete_goal_service", return_value=None):
        
        resp = client.patch(
            "/api/goals/complete-goal/g999",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Failed to mark goal as completed" in resp.get_json()["error"]