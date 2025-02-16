import pytest
import json
from unittest.mock import patch, MagicMock

def test_save_user_info_success(client):
    """
    POST /save-user-info => 201 on success.
    """
    data = {"name": "John Doe", "email": "john@example.com"}
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.save_user_info_service") as mock_save:
        
        resp = client.post(
            "/save-user-info",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 201
    resp_json = resp.get_json()
    assert resp_json["message"] == "Información guardada correctamente"
    # Check that service was called with (uid="user123", data)
    mock_save.assert_called_once_with("user123", data)

def test_save_user_info_invalid_token(client):
    """
    If verify_token_service returns None => 401
    """
    data = {"name": "John Doe", "email": "john@example.com"}
    with patch("app.controllers.user_controller.verify_token_service", return_value=None):
        resp = client.post(
            "/save-user-info",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token"
            }
        )
    assert resp.status_code == 401
    assert "Token inválido" in resp.get_json()["error"]

def test_save_user_info_exception(client):
    """
    If an exception is raised => 500
    """
    data = {"name": "John Doe"}
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.save_user_info_service", side_effect=Exception("DB error")):
        
        resp = client.post(
            "/save-user-info",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 500
    assert "Algo salió mal" in resp.get_json()["error"]

def test_get_user_info_success(client):
    """
    GET /get-user-info => 200 if user info found
    """
    mock_user_info = {"name": "Jane Doe", "email": "jane@example.com"}
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.get_user_info_service", return_value=mock_user_info):
        
        resp = client.get(
            "/get-user-info",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert resp_json["name"] == "Jane Doe"

def test_get_user_info_not_found(client):
    """
    If get_user_info_service returns None => 404
    """
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.get_user_info_service", return_value=None):
        
        resp = client.get(
            "/get-user-info",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 404
    assert "User not found" in resp.get_json()["error"]

def test_get_user_info_invalid_token(client):
    with patch("app.controllers.user_controller.verify_token_service", return_value=None):
        resp = client.get(
            "/get-user-info",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 401
    assert "Token inválido" in resp.get_json()["error"]

def test_get_user_info_exception(client):
    """
    If an exception is raised => 500
    """
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.get_user_info_service", side_effect=Exception("DB error")):
        
        resp = client.get(
            "/get-user-info",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Algo salió mal" in resp.get_json()["error"]

def test_update_user_info_success(client):
    """
    PUT /update-user-info => 200 on success
    """
    data = {"name": "Updated User", "email": "updated@example.com"}
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.update_user_info_service") as mock_update:
        
        resp = client.put(
            "/update-user-info",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert resp_json["message"] == "Información actualizada correctamente"
    mock_update.assert_called_once_with("user123", data)

def test_update_user_info_invalid_token(client):
    data = {"name": "Nope"}
    with patch("app.controllers.user_controller.verify_token_service", return_value=None):
        resp = client.put(
            "/update-user-info",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token"
            }
        )
    assert resp.status_code == 401
    assert "Token inválido" in resp.get_json()["error"]

def test_update_user_info_exception(client):
    data = {"name": "Crash"}
    with patch("app.controllers.user_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.user_controller.update_user_info_service", side_effect=Exception("DB error")):
        
        resp = client.put(
            "/update-user-info",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert resp.status_code == 500
    assert "Algo salió mal" in resp.get_json()["error"]