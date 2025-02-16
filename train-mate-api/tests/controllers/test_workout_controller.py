import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

def test_save_workout_success(client):
    data = {
        "training_id": "training123",
        "duration": 45,
        "date": "2025-01-01",
        "coach": "SomeCoach"
    }
    mock_workout = {
        "id": "workout123",
        "duration": 45,
        "date": "2025-01-01",
        "training_id": "training123",
        "coach": "SomeCoach",
        "total_calories": 300
    }
    mock_training_data = {"calories_per_hour_mean": 400}
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_training_by_id", return_value=mock_training_data), \
         patch("app.controllers.workout_controller.save_user_workout", return_value=mock_workout):
        
        resp = client.post(
            "/api/workouts/save-workout",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 201
    resp_json = resp.get_json()
    assert resp_json["message"] == "Workout saved successfully"
    assert resp_json["workout"]["id"] == "workout123"

def test_save_workout_missing_training_id(client):
    """
    If training_id is missing => 400
    """
    data = {"duration": 30}
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"):
        resp = client.post(
            "/api/workouts/save-workout",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 400
    assert "training_id is required" in resp.get_json()["error"]

def test_save_workout_invalid_duration(client):
    # e.g. duration=0 => should 400 "Invalid duration provided"
    data = {
        "training_id": "abc",
        "duration": 0,     # invalid
        "date": "2025-01-01",
        "coach": "CoachA"
    }
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"):
        resp = client.post(
            "/api/workouts/save-workout",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 400
    # The code returns `'Invalid duration provided'`
    assert "Invalid duration" in resp.get_json()["error"]

def test_save_workout_invalid_token(client):
    """
    If verify_token_service returns None => 401
    """
    data = {"training_id": "abc", "duration":30}
    with patch("app.controllers.workout_controller.verify_token_service", return_value=None):
        resp = client.post(
            "/api/workouts/save-workout",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 401
    assert "Invalid token" in resp.get_json()["error"]

def test_save_workout_exception(client):
    data = {
        "training_id": "abc",
        "duration": 30,
        "date": "2025-01-01",
        "coach": "CoachA"
    }
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_training_by_id", side_effect=Exception("DB error")):

        resp = client.post(
            "/api/workouts/save-workout",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Something went wrong" in resp.get_json()["error"]

def test_get_workouts_success(client):
    """
    GET /workouts => 200 on success, includes training+exercises expansion
    """
    # Mock workouts list
    mock_workouts = [
        {"id":"w1","training_id":"t1","date":"2023-01-01"},
        {"id":"w2","training_id":"t2","date":"2023-01-02"},
    ]
    # For each training, we might have some cph_mean, plus exercise IDs
    mock_training_data_t1 = {"calories_per_hour_mean":500, "exercises":["ex1","ex2"]}
    mock_training_data_t2 = {"calories_per_hour_mean":300, "exercises":["ex3"]}

    # Each exercise
    mock_ex1 = {"name":"Push-ups","calories_per_hour":300}
    mock_ex2 = {"name":"Sit-ups","calories_per_hour":250}
    mock_ex3 = {"name":"Squats","calories_per_hour":400}

    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_user_workouts", return_value=mock_workouts), \
         patch("app.controllers.workout_controller.get_training_by_id", side_effect=[mock_training_data_t1,mock_training_data_t2]), \
         patch("app.controllers.workout_controller.get_exercise_by_id_service", side_effect=[mock_ex1,mock_ex2,mock_ex3]):

        resp = client.get(
            "/api/workouts/workouts?startDate=2023-01-01&endDate=2023-01-31",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert len(resp_json["workouts"]) == 2
    # First workout => training => ex1,ex2
    w1 = resp_json["workouts"][0]
    assert w1["training"]["calories_per_hour_mean"] == 500
    # "exercises" replaced with mock_ex1,mock_ex2
    ex_list = w1["training"]["exercises"]
    assert ex_list[0]["name"] == "Push-ups"
    assert ex_list[1]["name"] == "Sit-ups"

def test_get_workouts_invalid_token(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value=None):
        resp = client.get(
            "/api/workouts/workouts",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 401
    assert "Token inválido" in resp.get_json()["error"]

def test_get_workouts_exception(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_user_workouts", side_effect=Exception("DB error")):
        resp = client.get(
            "/api/workouts/workouts",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Algo salió mal" in resp.get_json()["error"]

def test_get_workouts_calories_success(client):
    """
    GET /get-workouts-calories => 200
    """
    mock_calories = [300, 400]
    mock_dates = ["2023-01-01","2023-01-02"]
    mock_tids = ["t1","t2"]
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_user_calories_from_workouts", return_value=(mock_calories,mock_dates,mock_tids)):
        
        resp = client.get(
            "/api/workouts/get-workouts-calories?start_date=2023-01-01&end_date=2023-01-31",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert resp.status_code == 200
    resp_json = resp.get_json()
    wcad = resp_json["workouts_calories_and_dates"]
    assert len(wcad) == 2
    assert wcad[0]["date"] == "2023-01-01"
    assert wcad[0]["total_calories"] == 300
    assert wcad[0]["training_id"] == "t1"

def test_get_workouts_calories_invalid_token(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value=None):
        resp = client.get(
            "/api/workouts/get-workouts-calories?start_date=2023-01-01&end_date=2023-01-31",
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 401
    assert "Token inválido" in resp.get_json()["error"]

def test_get_workouts_calories_exception(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_user_calories_from_workouts", side_effect=Exception("DB error")):
        
        resp = client.get(
            "/api/workouts/get-workouts-calories?start_date=2023-01-01&end_date=2023-01-31",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Algo salió mal" in resp.get_json()["error"]

def test_cancel_workout_success(client):
    """
    DELETE /cancel-workout/<workout_id> => returns what delete_user_workout returns
    """
    mock_response = ({"message":"Workout canceled"}, 200)
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.delete_user_workout", return_value=mock_response):
        
        resp = client.delete(
            "/api/workouts/cancel-workout/w123",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Workout canceled"

def test_cancel_workout_invalid_token(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value=None):
        resp = client.delete("/api/workouts/cancel-workout/w123", headers={"Authorization":"Bearer invalid_token"})
    assert resp.status_code == 401
    assert "Invalid token" in resp.get_json()["error"]

def test_cancel_workout_exception(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.delete_user_workout", side_effect=Exception("DB crash")):
        
        resp = client.delete(
            "/api/workouts/cancel-workout/w123",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Something went wrong" in resp.get_json()["error"]

def test_get_last_modified_success(client):
    import datetime
    mock_time = datetime.datetime(2025,1,1,12,0,0)

    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_last_modified_timestamp", return_value=mock_time):
        
        resp = client.get(
            "/api/workouts/last-modified",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert "last_modified_timestamp" in resp.get_json()
    # Should be ms
    assert resp.get_json()["last_modified_timestamp"] == int(mock_time.timestamp() * 1000)

def test_get_last_modified_none(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_last_modified_timestamp", return_value=None):
        
        resp = client.get(
            "/api/workouts/last-modified",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 200
    assert resp.get_json()["last_modified_timestamp"] == None

def test_get_last_modified_invalid_token(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value=None):
        resp = client.get("/api/workouts/last-modified", headers={"Authorization":"Bearer invalid_token"})
    assert resp.status_code == 401
    assert "Invalid token" in resp.get_json()["error"]

def test_get_last_modified_exception(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.get_last_modified_timestamp", side_effect=Exception("DB err")):
        
        resp = client.get(
            "/api/workouts/last-modified",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Something went wrong" in resp.get_json()["error"]

def test_update_last_modified_success(client):
    import datetime
    mock_time = datetime.datetime(2025,1,2,10,0,0)

    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.set_last_modified_timestamp", return_value=mock_time):
        
        resp = client.post(
            "/api/workouts/update-last-modified",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert "Last modified timestamp updated successfully" in resp_json["message"]
    assert resp_json["last_modified_timestamp"] == int(mock_time.timestamp() * 1000)

def test_update_last_modified_no_time(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.set_last_modified_timestamp", return_value=None):
        
        resp = client.post(
            "/api/workouts/update-last-modified",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Error updating last modified timestamp" in resp.get_json()["error"]

def test_update_last_modified_invalid_token(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value=None):
        resp = client.post("/api/workouts/update-last-modified", headers={"Authorization":"Bearer invalid_token"})
    assert resp.status_code == 401
    assert "Invalid token" in resp.get_json()["error"]

def test_update_last_modified_exception(client):
    with patch("app.controllers.workout_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.workout_controller.set_last_modified_timestamp", side_effect=Exception("Crash")):
        
        resp = client.post(
            "/api/workouts/update-last-modified",
            headers={"Authorization":"Bearer valid_token"}
        )
    assert resp.status_code == 500
    assert "Something went wrong" in resp.get_json()["error"]