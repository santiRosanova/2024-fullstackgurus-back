import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.goals_service import (
    get_all_goals_service,
    create_goal_service,
    get_goal_service,
    update_goal_service,
    delete_goal_service,
    complete_goal_service
)

def test_get_all_goals_service_success():
    """
    Test retrieving all goals for a user successfully.
    """
    mock_db = MagicMock()
    mock_goals = [
        MagicMock(id="goal1", to_dict=lambda: {"title": "Goal1", "completed": False}),
        MagicMock(id="goal2", to_dict=lambda: {"title": "Goal2", "completed": True}),
    ]
    with patch("app.services.goals_service.db", mock_db):
        # .document(uid).collection('user_goals').stream() => mock_goals
        mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = mock_goals
        
        goals_list = get_all_goals_service(uid="user123")
    
    assert len(goals_list) == 2
    assert goals_list[0]["id"] == "goal1"
    assert goals_list[0]["title"] == "Goal1"

def test_get_all_goals_service_exception():
    """
    If an exception occurs, returns None.
    """
    with patch("app.services.goals_service.db.collection", side_effect=Exception("Firestore error")):
        goals_list = get_all_goals_service("user123")
    assert goals_list is None

@pytest.mark.parametrize("start_date,end_date,expected_error", [
    ("2020-01-01", None, "Start date cannot be in the past."),    # start in past
    (None, "2020-01-01", "End date cannot be in the past."),      # end in past
    ("2025-11-01", "2025-10-31", "End date must be after start date."),  # end < start
])
def test_create_goal_service_date_validations(start_date, end_date, expected_error):
    """
    For invalid date scenarios, create_goal_service should return
    ({"error": "..."}, 400).
    """
    mock_data = {
        "title": "Test Goal",
        "startDate": start_date,
        "endDate": end_date
    }
    result = create_goal_service("user123", mock_data)
    assert isinstance(result, tuple)
    error_dict, status_code = result
    assert status_code == 400
    assert expected_error in error_dict["error"]

def test_create_goal_service_success():
    """
    If valid data, we expect a goal dict with assigned ID.
    """
    mock_db = MagicMock()

    mock_user_doc = MagicMock()
    mock_user_doc.exists = False
    mock_goal_ref = MagicMock()
    mock_goal_ref.id = "new_goal_id"

    with patch("app.services.goals_service.db", mock_db):
        # user_ref = db.collection('goals').document(uid)
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc
        # user_ref.collection('user_goals').document() => mock_goal_ref
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_goal_ref

        mock_data = {
            "title": "Lose Weight",
            "description": "Lose 5 lbs in 2 months",
            "startDate": "2025-05-01",  # valid future date
            "endDate": "2025-06-30"
        }
        goal = create_goal_service("user123", mock_data)
    
    # Should return a dict (not a tuple)
    assert isinstance(goal, dict)
    assert goal["id"] == "new_goal_id"
    assert goal["title"] == "Lose Weight"
    mock_db.collection.assert_called_with("goals")

def test_create_goal_service_invalid_date_format():
    """
    If startDate or endDate has an invalid format => ValueError => returns None
    (Or you may adapt this if you want a 400 tuple return.)
    """
    # You have code that raises ValueError("Invalid start date format...")
    # We'll check that this leads to returning None
    mock_data = {"title":"Goal with bad format", "startDate":"bad-format"}
    goal = create_goal_service("user123", mock_data)
    assert goal is None

def test_create_goal_service_exception():
    """
    If Firestore calls raise an exception, return None.
    """
    mock_db = MagicMock()
    with patch("app.services.goals_service.db", mock_db):
        mock_db.collection.side_effect = Exception("DB error")
        result = create_goal_service("user123", {"title": "Test"})
    assert result is None

def test_get_goal_service_success():
    """
    get_goal_service => returns dict if doc exists.
    """
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.id = "goal123"
    mock_doc.to_dict.return_value = {"title": "Goal Title", "completed": False}

    with patch("app.services.goals_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        goal = get_goal_service("user123", "goal123")

    assert goal is not None
    assert goal["id"] == "goal123"
    assert goal["title"] == "Goal Title"

def test_get_goal_service_not_found():
    """
    If doc does not exist => None
    """
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch("app.services.goals_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        goal = get_goal_service("user123", "goalXYZ")
    assert goal is None

def test_get_goal_service_exception():
    """
    On exception => None
    """
    with patch("app.services.goals_service.db.collection", side_effect=Exception("DB error")):
        result = get_goal_service("user123", "goal123")
    assert result is None

def test_update_goal_service_success():
    """
    update_goal_service => returns updated doc dict if no exception.
    """
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "title": "Updated Title",
        "description": "Updated Desc",
        "completed": False
    }

    with patch("app.services.goals_service.db", mock_db):
        # The final .get() returns mock_doc
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        updated_goal = update_goal_service("user123", "goal123", {"title":"Updated Title","description":"Updated Desc"})
    
    assert updated_goal is not None
    assert updated_goal["id"] == "goal123"
    assert updated_goal["title"] == "Updated Title"
    # Also check we called .update(...) with the provided data
    mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.update.assert_called_once_with({
        "title":"Updated Title",
        "description":"Updated Desc"
    })

def test_update_goal_service_exception():
    """
    On exception => return None
    """
    with patch("app.services.goals_service.db.collection", side_effect=Exception("DB error")):
        result = update_goal_service("user123", "goal123", {})
    assert result is None

def test_delete_goal_service_success():
    """
    If no exception, return True.
    """
    mock_db = MagicMock()
    with patch("app.services.goals_service.db", mock_db):
        success = delete_goal_service("user123", "goalXYZ")
    assert success is True
    mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete.assert_called_once()

def test_delete_goal_service_exception():
    """
    If exception => return False.
    """
    with patch("app.services.goals_service.db.collection", side_effect=Exception("DB error")):
        success = delete_goal_service("user123", "goalXYZ")
    assert success is False

def test_complete_goal_service_success():
    """
    complete_goal_service => sets 'completed' to True, returns updated goal dict
    """
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {"title": "A goal", "completed": True}

    with patch("app.services.goals_service.db", mock_db):
        # doc.get() => mock_doc
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        
        updated = complete_goal_service("user123", "goalABC")
    
    assert updated is not None
    assert updated["completed"] is True
    assert updated["id"] == "goalABC"
    mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.update.assert_called_once_with({"completed": True})

def test_complete_goal_service_exception():
    """
    On exception => returns None
    """
    with patch("app.services.goals_service.db.collection", side_effect=Exception("DB error")):
        result = complete_goal_service("user123", "goalABC")
    assert result is None