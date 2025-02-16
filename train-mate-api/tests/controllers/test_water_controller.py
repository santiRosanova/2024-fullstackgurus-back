import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

def test_add_water_intake_success(client):
    """
    POST /add => 201 on success.
    """
    mock_data = {
        "quantity_in_militers": 500,
        "public": True
    }
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.add_water_intake_service", return_value=True) as mock_add:
        
        response = client.post(
            "/api/water-intake/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 201
    resp_json = response.get_json()
    assert resp_json["message"] == "Water intake added successfully"
    # Check service call
    # quantity_in_militers=500, date=some default or from request, public=True
    mock_add.assert_called_once()
    # We won't check exact date param unless you pass a fixed date in the test_data

def test_add_water_intake_missing_qty(client):
    """
    If quantity_in_militers is not provided => 400
    """
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"):
        response = client.post(
            "/api/water-intake/add",
            data=json.dumps({}),  # no quantity_in_militers
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 400
    assert "Invalid water quantity" in response.get_json()["error"]

def test_add_water_intake_invalid_token(client):
    """
    If token is invalid => 403
    """
    mock_data = {"quantity_in_militers": 500}
    with patch("app.controllers.water_controller.verify_token_service", return_value=None):
        response = client.post(
            "/api/water-intake/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token"
            }
        )
    assert response.status_code == 403
    assert "Invalid token" in response.get_json()["error"]

def test_add_water_intake_missing_auth_header(client):
    """
    If Authorization header is missing => 403
    """
    response = client.post("/api/water-intake/add")
    assert response.status_code == 403
    assert "Authorization token missing" in response.get_json()["error"]

def test_add_water_intake_service_failure(client):
    """
    If add_water_intake_service returns False => 500
    """
    mock_data = {"quantity_in_militers": 500}
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.add_water_intake_service", return_value=False):
        
        response = client.post(
            "/api/water-intake/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 500
    assert "Failed to save water intake" in response.get_json()["error"]

def test_add_water_intake_exception(client):
    """
    If an exception is raised => 500
    """
    mock_data = {"quantity_in_militers": 500}
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.add_water_intake_service", side_effect=Exception("DB error")):
        
        response = client.post(
            "/api/water-intake/add",
            data=json.dumps(mock_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]

def test_get_daily_water_intake_success(client):
    """
    GET /get-daily-water-intake => 200 on success
    """
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.get_daily_water_intake_service", return_value=750):
        
        response = client.get(
            "/api/water-intake/get-daily-water-intake",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    # By default, controller uses current date
    assert "date" in resp_json
    assert "quantity_in_militers" in resp_json
    assert resp_json["quantity_in_militers"] == 750

def test_get_daily_water_intake_none(client):
    """
    If get_daily_water_intake_service returns None => message=No water intake..., quantity=0 => 200
    """
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.get_daily_water_intake_service", return_value=None):
        
        response = client.get(
            "/api/water-intake/get-daily-water-intake",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert resp_json["message"] == "No water intake found for today"
    assert resp_json["quantity_in_militers"] == 0

def test_get_daily_water_intake_invalid_token(client):
    with patch("app.controllers.water_controller.verify_token_service", return_value=None):
        response = client.get(
            "/api/water-intake/get-daily-water-intake",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert response.status_code == 403
    assert "Invalid token" in response.get_json()["error"]

def test_get_daily_water_intake_missing_auth(client):
    response = client.get("/api/water-intake/get-daily-water-intake")
    assert response.status_code == 403
    assert "Authorization token missing" in response.get_json()["error"]

def test_get_daily_water_intake_exception(client):
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.get_daily_water_intake_service", side_effect=Exception("DB fail")):
        
        response = client.get(
            "/api/water-intake/get-daily-water-intake",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]

def test_get_water_intake_history_success(client):
    """
    GET /get-water-intake-history => 200 on success
    """
    history_data = [
        {"date": "2023-01-01", "quantity_in_militers": 1000},
        {"date": "2023-01-02", "quantity_in_militers": 1200},
    ]
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.get_water_intake_history_service", return_value=history_data):
        
        response = client.get(
            "/api/water-intake/get-water-intake-history?start_date=2023-01-01&end_date=2023-01-02",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json["water_intake_history"]) == 2
    assert resp_json["water_intake_history"][0]["date"] == "2023-01-01"

def test_get_water_intake_history_missing_dates(client):
    """
    If start_date or end_date missing => 400
    """
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"):
        response = client.get(
            "/api/water-intake/get-water-intake-history",  # no params
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 400
    assert "Start date and end date are required" in response.get_json()["error"]

def test_get_water_intake_history_invalid_token(client):
    response = client.get(
        "/api/water-intake/get-water-intake-history?start_date=2023-01-01&end_date=2023-01-02",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 403
    assert "Invalid token" in response.get_json()["error"]

def test_get_water_intake_history_missing_auth(client):
    """
    If missing Authorization => 403
    """
    response = client.get("/api/water-intake/get-water-intake-history?start_date=2023-01-01&end_date=2023-01-02")
    assert response.status_code == 403
    assert "Authorization token missing" in response.get_json()["error"]

def test_get_water_intake_history_exception(client):
    with patch("app.controllers.water_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.water_controller.get_water_intake_history_service", side_effect=Exception("DB fail")):
        
        response = client.get(
            "/api/water-intake/get-water-intake-history?start_date=2023-01-01&end_date=2023-01-02",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]