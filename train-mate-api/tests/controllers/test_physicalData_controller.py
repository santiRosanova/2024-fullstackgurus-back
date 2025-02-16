import pytest
import json
from unittest.mock import patch, MagicMock

def mock_verify_token(token):
    """Return 'user123' if token == 'valid_token', else None."""
    if token == "valid_token":
        return "user123"
    return None

@pytest.mark.parametrize("endpoint,method", [
    ("/api/physical-data/add", "POST"),
    ("/api/physical-data/get-physical-data", "GET"),
])
def test_missing_auth(client, endpoint, method):
    """
    Check that missing or malformed Authorization header => 403.
    """
    if method == "POST":
        resp = client.post(endpoint)
    elif method == "GET":
        resp = client.get(endpoint)

    assert resp.status_code == 403
    assert "Authorization token missing" in resp.get_json()["error"]

def test_add_physical_data_success(client):
    """
    POST /api/physical-data/add => 201 on success.
    """
    mock_data = {
        "weight": 70,
        "body_fat": 15,
        "body_muscle": 40,
        # date is optional in request; if missing, server uses today's date
    }

    with patch("app.controllers.physicalData_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.physicalData_controller.add_physical_data_service", return_value=True):
        
        resp = client.post(
            "/api/physical-data/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 201
    assert resp.get_json()["message"] == "Physical data added successfully"

def test_add_physical_data_missing_params(client):
    """
    If weight, body_fat, or body_muscle are missing => 400.
    """
    # Missing body_muscle
    mock_data = {
        "weight": 70,
        "body_fat": 15
    }
    with patch("app.controllers.physicalData_controller.verify_token_service", return_value="user123"):
        resp = client.post(
            "/api/physical-data/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 400
    assert "Missing parameters" in resp.get_json()["error"]

def test_add_physical_data_invalid_token(client):
    """
    If token is invalid => 403.
    """
    mock_data = {"weight": 70, "body_fat": 15, "body_muscle": 40}
    with patch("app.controllers.physicalData_controller.verify_token_service", return_value=None):
        resp = client.post(
            "/api/physical-data/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token"
            }
        )
    assert resp.status_code == 403
    assert "Invalid token" in resp.get_json()["error"]

def test_add_physical_data_service_failure(client):
    """
    If add_physical_data_service returns False => 500.
    """
    mock_data = {"weight": 70, "body_fat": 15, "body_muscle": 40}
    with patch("app.controllers.physicalData_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.physicalData_controller.add_physical_data_service", return_value=False):
        
        resp = client.post(
            "/api/physical-data/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 500
    assert "Failed to save physical data" in resp.get_json()["error"]

def test_get_physical_data_success(client):
    """
    GET /api/physical-data/get-physical-data => 200 on success.
    """
    mock_physical_data = [
        {"date": "2025-01-01", "weight": 70, "body_fat": 15, "body_muscle": 40},
        {"date": "2025-01-08", "weight": 72, "body_fat": 14, "body_muscle": 41}
    ]
    with patch("app.controllers.physicalData_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.physicalData_controller.get_physical_data_service", return_value=mock_physical_data):
        
        resp = client.get(
            "/api/physical-data/get-physical-data",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    resp_data = resp.get_json()
    assert len(resp_data) == 2
    assert resp_data[0]["weight"] == 70

def test_get_physical_data_invalid_token(client):
    """
    If token is invalid => 403.
    """
    with patch("app.controllers.physicalData_controller.verify_token_service", return_value=None):
        resp = client.get(
            "/api/physical-data/get-physical-data",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 403
    assert "Invalid token" in resp.get_json()["error"]

def test_get_physical_data_service_failure(client):
    """
    If get_physical_data_service returns Falsey => 500.
    """
    with patch("app.controllers.physicalData_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.physicalData_controller.get_physical_data_service", return_value=None):
        
        resp = client.get(
            "/api/physical-data/get-physical-data",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Failed to get physical data" in resp.get_json()["error"]