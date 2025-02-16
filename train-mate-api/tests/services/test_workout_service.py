import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.workout_service import (
    save_user_workout,
    get_user_workouts,
    get_user_calories_from_workouts,
    delete_user_workout
)

def test_save_user_workout_success():
    mock_db = MagicMock()
    mock_challenges = MagicMock()

    user_doc_mock = MagicMock()
    user_doc_mock.exists = False

    doc_ref_mock = MagicMock()
    doc_ref_mock.id = "new_workout_id"

    with patch("app.services.workout_service.db", mock_db), \
         patch("app.services.workout_service.check_and_update_workouts_challenges", mock_challenges), \
         patch("app.services.workout_service.get_training_by_id", return_value={"some": "training"}):  # NEW

        mock_db.collection.return_value.document.return_value.get.return_value = user_doc_mock
        mock_db.collection.return_value.document.return_value.collection.return_value.add.return_value = (None, doc_ref_mock)

        data = {
            "training_id": "trainXYZ",
            "duration": 45,
            "date": "2025-05-01",
            "coach": "CoachBob"
        }
        result = save_user_workout("user123", data, calories_burned=300)

    # The rest remains the same...

def test_save_user_workout_invalid_date():
    mock_db = MagicMock()
    with patch("app.services.workout_service.db", mock_db), \
         patch("app.services.workout_service.get_training_by_id", return_value={"some":"training"}), \
         pytest.raises(ValueError) as exc_info:
        
        data = {
            "training_id": "tid",
            "duration": 30,
            "date": "bad-format",  # triggers ValueError
            "coach": "AnyCoach"
        }
        save_user_workout("user123", data, 150)
    assert "Invalid date format. Use 'YYYY-MM-DD'." in str(exc_info.value)

def test_save_user_workout_no_date():
    mock_db = MagicMock()
    mock_challenges = MagicMock()

    user_doc_mock = MagicMock()
    user_doc_mock.exists = True
    doc_ref_mock = MagicMock()
    doc_ref_mock.id = "workout_no_date"

    with patch("app.services.workout_service.db", mock_db), \
         patch("app.services.workout_service.check_and_update_workouts_challenges", mock_challenges), \
         patch("app.services.workout_service.get_training_by_id", return_value={"some": "training"}):

        mock_db.collection.return_value.document.return_value.get.return_value = user_doc_mock
        mock_db.collection.return_value.document.return_value.collection.return_value.add.return_value = (None, doc_ref_mock)

        data = {
            "training_id": "tid123",
            "duration": 60,
            "coach": "CoachAmy"
        }
        result = save_user_workout("user123", data, 400)

    # Now .add(...) is called once with 'date' => db.SERVER_TIMESTAMP
    add_data = mock_db.collection.return_value.document.return_value.collection.return_value.add.call_args[0][0]
    assert add_data["date"] == mock_db.SERVER_TIMESTAMP
    assert result["id"] == "workout_no_date"

def test_save_user_workout_exception():
    """
    If some other exception is raised (like Firestore fails), the code doesn't catch it => it bubbles up.
    """
    with patch("app.services.workout_service.db.collection", side_effect=Exception("DB error")):
        with pytest.raises(Exception) as exc_info:
            save_user_workout("user123", {"training_id":"abc","duration":20,"coach":"C"}, 100)
    assert "DB error" in str(exc_info.value)

def test_get_user_workouts_success():
    """
    Test normal success path: no exceptions, valid dates => doc mocks returned.
    """
    # We'll create a single mock for user_workouts_ref
    user_workouts_ref = MagicMock()
    # Each .where(...) call should return the same mock object so we can chain calls
    user_workouts_ref.where.return_value = user_workouts_ref

    # We'll pretend .stream() returns two doc mocks
    doc_mock1 = MagicMock()
    doc_mock1.id = "w1"
    doc_mock1.to_dict.return_value = {
        "training_id": "t1",
        "duration": 30,
        "total_calories": 200,
        "date": datetime(2025,1,1)
    }
    doc_mock2 = MagicMock()
    doc_mock2.id = "w2"
    doc_mock2.to_dict.return_value = {
        "training_id": "t2",
        "duration": 60,
        "total_calories": 400,
        "date": datetime(2025,1,2)
    }
    user_workouts_ref.stream.return_value = [doc_mock1, doc_mock2]

    # Now we mock the chain:
    # db.collection("workouts") -> main_collection_mock
    main_collection_mock = MagicMock()
    # main_collection_mock.document(uid) -> doc_ref_mock
    doc_ref_mock = MagicMock()
    # doc_ref_mock.collection("user_workouts") -> user_workouts_ref
    doc_ref_mock.collection.return_value = user_workouts_ref
    main_collection_mock.document.return_value = doc_ref_mock

    # Finally, db.collection("workouts") => main_collection_mock
    mock_db = MagicMock()
    mock_db.collection.return_value = main_collection_mock

    with patch("app.services.workout_service.db", mock_db):
        # Now call
        result = get_user_workouts("user123", start_date="2025-01-01", end_date="2025-01-31")

    assert len(result) == 2
    assert result[0]["id"] == "w1"
    assert result[0]["training_id"] == "t1"
    assert result[1]["id"] == "w2"
    # Also check that we called .where(...) with date >= 2025-01-01, date <= 2025-01-31
    # (If you want to confirm, you can do user_workouts_ref.where.assert_any_call('date', '>=', ...)
    # or check call_args_list.)

def test_get_user_workouts_invalid_date():
    """
    If we raise ValueError => code returns {"error": "Invalid date. Use ..."}
    """
    # We'll specifically raise ValueError inside the try block:
    # For example, patch datetime.strptime to raise ValueError
    with patch("app.services.workout_service.datetime") as mock_dt:
        mock_dt.strptime.side_effect = ValueError("bad date")

        result = get_user_workouts("user123", start_date="bad-format")
    assert isinstance(result, dict)
    assert result["error"] == "Invalid date. Use 'YYYY-MM-DD'."


def test_get_user_calories_from_workouts_success():
    """
    No exception => returns ([cals], [dates], [training_ids]).
    """
    user_workouts_ref = MagicMock()
    user_workouts_ref.where.return_value = user_workouts_ref

    doc1 = MagicMock()
    doc1.to_dict.return_value = {
        "total_calories": 200,
        "date": datetime(2025,5,1),
        "training_id": "t1"
    }
    doc2 = MagicMock()
    doc2.to_dict.return_value = {
        "total_calories": 300,
        "date": datetime(2025,5,2),
        "training_id": "t2"
    }
    user_workouts_ref.stream.return_value = [doc1, doc2]

    doc_ref_mock = MagicMock()
    doc_ref_mock.collection.return_value = user_workouts_ref

    main_collection_mock = MagicMock()
    main_collection_mock.document.return_value = doc_ref_mock

    mock_db = MagicMock()
    mock_db.collection.return_value = main_collection_mock

    with patch("app.services.workout_service.db", mock_db):
        cals, dates, tids = get_user_calories_from_workouts("user123","2025-05-01","2025-05-02")
    assert cals == [200, 300]
    assert dates == [datetime(2025,5,1), datetime(2025,5,2)]
    assert tids == ["t1","t2"]

def test_get_user_calories_from_workouts_invalid_date():
    """
    If ValueError => returns {'error':'Invalid date. Use ...'}
    """
    with patch("app.services.workout_service.datetime") as mock_dt:
        mock_dt.strptime.side_effect = ValueError("Bad date")
        result = get_user_calories_from_workouts("user123","bad-date")
    assert isinstance(result, dict)
    assert result["error"] == "Invalid date. Use 'YYYY-MM-DD'."

def test_delete_user_workout_found_future():
    """
    If doc exists with a future date => we delete => 'Workout cancelled successfully'
    """
    mock_db = MagicMock()
    doc_mock = MagicMock()
    doc_mock.exists = True
    # future date
    doc_mock.to_dict.return_value = {"date": datetime(2025,12,31)}

    with patch("app.services.workout_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = doc_mock
        response, status = delete_user_workout("user123", "workoutABC")
    assert status == 200
    assert response["message"] == "Workout cancelled successfully"

def test_delete_user_workout_not_found():
    """
    If doc not found => 404
    """
    mock_db = MagicMock()
    doc_mock = MagicMock()
    doc_mock.exists = False

    with patch("app.services.workout_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = doc_mock
        response, status = delete_user_workout("user123", "missingW")
    assert status == 404
    assert "Workout not found" in response["error"]

def test_delete_user_workout_past_date():
    """
    If date <= now => cannot cancel => 400
    """
    mock_db = MagicMock()
    doc_mock = MagicMock()
    doc_mock.exists = True
    doc_mock.to_dict.return_value = {"date": datetime(2020,1,1)}

    with patch("app.services.workout_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = doc_mock
        response, status = delete_user_workout("user123", "pastWorkout")
    assert status == 400
    assert "Cannot cancel past workouts" in response["error"]