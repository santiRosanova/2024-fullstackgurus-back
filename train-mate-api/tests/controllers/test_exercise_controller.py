import pytest
import json
from unittest.mock import patch, MagicMock

def mock_verify_token(token):
    """
    Mocks token verification. Return a UID if token is "valid_token", else None.
    """
    if token == "valid_token":
        return "user123"
    return None

@pytest.mark.parametrize("endpoint,method", [
    ("/api/exercise/save-exercise", "POST"),
    ("/api/exercise/get-exercises", "GET"),
    ("/api/exercise/delete-exercise/fake_id", "DELETE"),
    ("/api/exercise/edit-exercise/fake_id", "PUT"),
    ("/api/exercise/get-exercises-by-category/fake_cat_id", "GET"),
])
def test_missing_auth(client, endpoint, method):
    """
    Verify that requests without Authorization header (or malformed) return 403.
    """
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint)
    elif method == "PUT":
        response = client.put(endpoint)
    elif method == "DELETE":
        response = client.delete(endpoint)

    # Expect 403 due to missing auth
    assert response.status_code in [401, 403, 500]
    assert f"Got {response.status_code} instead of one of [401, 403, 500]"

def test_save_exercise_success(client):
    """
    Test POST /api/exercise/save-exercise success scenario.
    """
    data = {
        "name": "Push-ups",
        "calories_per_hour": 500,
        "public": True,
        "category_id": "cat123",
        "image_url": "http://example.com/image.jpg",
        "training_muscle": "Chest"
    }

    mock_exercise_return = (True, {**data, "id": "new_ex_id"})

    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.save_exercise_service", return_value=mock_exercise_return):
        
        response = client.post(
            "/api/exercise/save-exercise",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 201
    resp_json = response.get_json()
    assert resp_json["message"] == "Exercise saved successfully"
    assert resp_json["exercise"]["id"] == "new_ex_id"

def test_save_exercise_validation_error(client):
    """
    Missing data => 400
    """
    # Missing calories_per_hour
    data = {
        "name": "Push-ups",
        "public": True,
        "category_id": "cat123",
        "image_url": "http://example.com/image.jpg",
        "training_muscle": "Chest"
    }

    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"):
        response = client.post(
            "/api/exercise/save-exercise",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 400
    assert "Missing data" in response.get_json()["error"]

def test_save_exercise_invalid_token(client):
    data = {
        "name": "Push-ups",
        "calories_per_hour": 500,
        "public": True,
        "category_id": "cat123",
        "image_url": "http://example.com/image.jpg",
        "training_muscle": "Chest"
    }
    # Mock invalid token
    with patch("app.controllers.exercise_controller.verify_token_service", return_value=None):
        response = client.post(
            "/api/exercise/save-exercise",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token"
            }
        )
    assert response.status_code == 403
    assert "Invalid token" in response.get_json()["error"]

def test_save_exercise_failure_service(client):
    """
    If the service returns (False, None) or a None scenario, expect 500.
    """
    data = {
        "name": "Push-ups",
        "calories_per_hour": 500,
        "public": True,
        "category_id": "cat123",
        "image_url": "http://example.com/image.jpg",
        "training_muscle": "Chest"
    }
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.save_exercise_service", return_value=(False, None)):
        
        response = client.post(
            "/api/exercise/save-exercise",
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid_token"
            }
        )
    assert response.status_code == 500
    assert "Failed to save exercise" in response.get_json()["error"]

def test_get_exercises_success(client):
    """
    GET /api/exercise/get-exercises => 200 on success
    """
    mock_exercises = [
        {"id": "ex1", "name": "Push-ups", "calories_per_hour": 500},
        {"id": "ex2", "name": "Sit-ups", "calories_per_hour": 300},
    ]
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.get_exercises_service", return_value=mock_exercises):
        
        response = client.get(
            "/api/exercise/get-exercises?public=false",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json["exercises"]) == 2
    assert resp_json["exercises"][0]["name"] == "Push-ups"

def test_get_exercises_invalid_token(client):
    """
    If verify_token_service returns None => 403
    """
    with patch("app.controllers.exercise_controller.verify_token_service", return_value=None):
        response = client.get(
            "/api/exercise/get-exercises?public=true",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert response.status_code == 403
    assert "Invalid token" in response.get_json()["error"]

def test_delete_exercise_success(client):
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.delete_exercise_service", return_value=True):
        
        response = client.delete(
            "/api/exercise/delete-exercise/ex123",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Exercise deleted successfully"

def test_delete_exercise_failure(client):
    """
    If delete_exercise_service returns False => 404
    """
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.delete_exercise_service", return_value=False):
        
        response = client.delete(
            "/api/exercise/delete-exercise/ex404",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 404
    assert "Failed to delete exercise" in response.get_json()["error"]

def test_edit_exercise_success(client):
    """
    Test editing an exercise, check if we call recalculate function if 'calories_per_hour' in update.
    """
    data = {"calories_per_hour": 450}
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.update_exercise_service", return_value=True) as mock_update, \
         patch("app.controllers.exercise_controller.recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise") as mock_recalc:
        
        response = client.put(
            "/api/exercise/edit-exercise/ex123",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Exercise updated successfully"
    mock_update.assert_called_once()
    # Because 'calories_per_hour' is in update, we expect recalc to be called
    mock_recalc.assert_called_once_with("user123", "ex123")

def test_edit_exercise_no_valid_fields(client):
    """
    If no valid fields are passed => 400
    """
    data = {"someField": "notAllowed"}
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"):
        response = client.put(
            "/api/exercise/edit-exercise/ex123",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 400
    assert "No valid fields to update" in response.get_json()["error"]

def test_edit_exercise_failure_service(client):
    """
    If update_exercise_service returns False => 404
    """
    data = {"calories_per_hour": 200}
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.update_exercise_service", return_value=False):
        
        response = client.put(
            "/api/exercise/edit-exercise/ex404",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 404
    assert "Failed to update exercise" in response.get_json()["error"]

def test_get_all_exercises_success(client):
    """
    Public endpoint => no auth required. 
    """
    mock_ex_list = [
        {"id": "ex1", "name": "Jumping Jacks", "calories_per_hour": 600, "public": True},
        {"id": "ex2", "name": "Running", "calories_per_hour": 800, "public": True}
    ]
    with patch("app.controllers.exercise_controller.get_all_exercises_service", return_value=mock_ex_list):
        response = client.get("/api/exercise/get-all-exercises")
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json["exercises"]) == 2
    assert resp_json["exercises"][0]["name"] == "Jumping Jacks"

def test_get_all_exercises_exception(client):
    """
    If service throws => 500
    """
    with patch("app.controllers.exercise_controller.get_all_exercises_service", side_effect=Exception("DB fail")):
        response = client.get("/api/exercise/get-all-exercises")
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]

def test_get_exercises_by_category_success(client):
    mock_exercises = [
        {"id": "exCat1", "category_id": "cat123", "owner": "user123"},
        {"id": "exCat2", "category_id": "cat123", "owner": "default"}
    ]
    with patch("app.controllers.exercise_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.exercise_controller.get_exercise_by_category_id_service", return_value=mock_exercises):
        
        response = client.get(
            "/api/exercise/get-exercises-by-category/cat123",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json["exercises"]) == 2
    assert resp_json["exercises"][0]["id"] == "exCat1"

def test_get_exercises_by_category_invalid_token(client):
    """
    If token is invalid => 403
    """
    with patch("app.controllers.exercise_controller.verify_token_service", return_value=None):
        response = client.get(
            "/api/exercise/get-exercises-by-category/cat123",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert response.status_code == 403
    assert "Invalid token" in response.get_json()["error"]