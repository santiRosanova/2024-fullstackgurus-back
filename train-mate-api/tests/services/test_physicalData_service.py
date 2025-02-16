import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.physicalData_service import (
    add_physical_data_service,
    get_physical_data_service
)

def test_add_physical_data_service_success():
    """
    If Firestore calls succeed and check_and_update_physical_challenges is called,
    the function should return True.
    """
    mock_db = MagicMock()
    mock_user_doc = MagicMock()
    mock_user_doc.exists = False  # pretend user doc doesn't exist
    mock_doc_ref = MagicMock()
    
    with patch("app.services.physicalData_service.db", mock_db), \
         patch("app.services.physicalData_service.check_and_update_physical_challenges") as mock_challenges:
        
        # user_ref.get() => mock_user_doc
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc
        # user_ref.collection('user_physical_data').document(date) => mock_doc_ref
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc_ref

        success = add_physical_data_service(
            uid="user123",
            body_fat=15,
            body_muscle=40,
            weight=70,
            date="2025-05-01"
        )
    
    assert success is True
    # The set(...) call should happen on the doc_ref
    mock_doc_ref.set.assert_called_once()
    # check_and_update_physical_challenges should be called once
    mock_challenges.assert_called_once_with("user123", "2025-05-01")

def test_add_physical_data_service_exception():
    """
    If an exception is raised, the function returns False.
    """
    with patch("app.services.physicalData_service.db.collection", side_effect=Exception("DB error")), \
         patch("app.services.physicalData_service.check_and_update_physical_challenges"):
        
        success = add_physical_data_service(
            uid="user123",
            body_fat=15,
            body_muscle=40,
            weight=70,
            date="2025-05-01"
        )
    assert success is False

def test_get_physical_data_service_success():
    """
    If user doc exists, return a list of data from the .stream() results.
    """
    mock_db = MagicMock()
    mock_user_doc = MagicMock()
    mock_user_doc.exists = True

    mock_data1 = MagicMock()
    mock_data1.to_dict.return_value = {
        "weight": 70,
        "date": datetime(2025, 5, 1, 10, 0),
        "body_fat": 15,
        "body_muscle": 40
    }
    mock_data2 = MagicMock()
    mock_data2.to_dict.return_value = {
        "weight": 72,
        "date": datetime(2025, 5, 8, 10, 0),
        "body_fat": 14,
        "body_muscle": 41
    }

    with patch("app.services.physicalData_service.db", mock_db):
        # user_ref.get() => mock_user_doc
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc
        # user_ref.collection('user_physical_data').stream() => [mock_data1, mock_data2]
        mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = [
            mock_data1, mock_data2
        ]

        result = get_physical_data_service("user123")
    
    assert len(result) == 2
    assert result[0]["weight"] == 70
    assert result[1]["body_fat"] == 14

def test_get_physical_data_service_doc_not_exist():
    """
    If user_doc doesn't exist, return an empty list.
    """
    mock_db = MagicMock()
    mock_user_doc = MagicMock()
    mock_user_doc.exists = False

    with patch("app.services.physicalData_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc

        result = get_physical_data_service("user123")
    assert result == []  # empty list

def test_get_physical_data_service_exception():
    """
    On exception, return False (as per your code).
    """
    with patch("app.services.physicalData_service.db.collection", side_effect=Exception("DB error")):
        result = get_physical_data_service("user123")
    assert result is False