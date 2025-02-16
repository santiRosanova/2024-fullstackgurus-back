import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.water_service import (
    add_water_intake_service,
    get_daily_water_intake_service,
    get_water_intake_history_service
)

def test_add_water_intake_service_new_day():
    """
    If the user doc does not exist or day doc does not exist, we create/update it with the quantity.
    """
    mock_db = MagicMock()

    # user_ref => doc doesn't exist initially
    user_doc_mock = MagicMock()
    user_doc_mock.exists = False

    # day doc doesn't exist
    day_doc_mock = MagicMock()
    day_doc_mock.exists = False

    # After we do .set(...), we expect success => True
    with patch("app.services.water_service.db", mock_db):
        # db.collection("water_intakes").document(uid).get() => user_doc_mock
        mock_db.collection.return_value.document.return_value.get.return_value = user_doc_mock

        # user_ref.collection("user_water_intakes").document(date).get() => day_doc_mock
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = day_doc_mock

        success = add_water_intake_service(
            uid="user123",
            quantity_in_militers=500,
            date="2025-01-01",
            public=True
        )
    
    assert success is True
    # Check calls
    mock_db.collection.assert_called_with("water_intakes")
    doc_mock = mock_db.collection.return_value.document.return_value

    # user_doc_mock doesn't exist => we do doc_mock.set({})
    doc_mock.set.assert_called_once_with({})

    # For the day doc: .set(...) with quantity_in_militers=500, date= datetime(2025,1,1,...), public=True
    day_doc_set_call = doc_mock.collection.return_value.document.return_value.set
    day_doc_set_call.assert_called_once()
    called_data = day_doc_set_call.call_args[0][0]
    assert called_data["quantity_in_militers"] == 500
    assert called_data["public"] is True
    assert isinstance(called_data["date"], datetime)  # after we do datetime.strptime(date,...)

def test_add_water_intake_service_existing_day():
    """
    If there's already water intake for that day, we add to the existing quantity.
    """
    mock_db = MagicMock()

    # user doc exists
    user_doc_mock = MagicMock()
    user_doc_mock.exists = True

    # day doc exists with quantity=300
    day_doc_mock = MagicMock()
    day_doc_mock.exists = True
    day_doc_mock.to_dict.return_value = {"quantity_in_militers": 300}

    with patch("app.services.water_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = user_doc_mock
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = day_doc_mock

        success = add_water_intake_service("user123", 200, "2025-01-02", False)
    
    assert success is True
    # We expect day doc final = 300 existing + 200 new = 500
    day_doc_set_call = mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.set
    day_doc_set_call.assert_called_once()
    new_data = day_doc_set_call.call_args[0][0]
    assert new_data["quantity_in_militers"] == 500
    assert new_data["public"] is False

def test_add_water_intake_service_exception():
    """
    If Firestore throws an error => returns False
    """
    with patch("app.services.water_service.db.collection", side_effect=Exception("DB error")):
        success = add_water_intake_service("user123", 100, "2025-01-01", True)
    assert success is False


def test_get_daily_water_intake_service_found():
    """
    If doc for the day exists => return quantity_in_militers
    """
    mock_db = MagicMock()

    day_doc_mock = MagicMock()
    day_doc_mock.exists = True
    day_doc_mock.to_dict.return_value = {"quantity_in_militers": 750}

    with patch("app.services.water_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = day_doc_mock

        qty = get_daily_water_intake_service("user123", "2025-01-01")
    assert qty == 750

def test_get_daily_water_intake_service_not_found():
    """
    If the doc does not exist => returns None
    """
    mock_db = MagicMock()
    day_doc_mock = MagicMock()
    day_doc_mock.exists = False

    with patch("app.services.water_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = day_doc_mock
        qty = get_daily_water_intake_service("user123", "2025-01-01")
    assert qty is None

def test_get_daily_water_intake_service_exception():
    """
    On exception => returns None
    """
    with patch("app.services.water_service.db.collection", side_effect=Exception("DB fail")):
        qty = get_daily_water_intake_service("user123", "2025-01-01")
    assert qty is None


def test_get_water_intake_history_service_success():
    """
    Return list of {date, quantity_in_militers} within date range
    """
    mock_db = MagicMock()

    # Suppose we have 2 docs in the date range
    doc1 = MagicMock()
    doc1.to_dict.return_value = {
        "date": datetime(2025, 1, 1),
        "quantity_in_militers": 500
    }
    doc2 = MagicMock()
    doc2.to_dict.return_value = {
        "date": datetime(2025, 1, 2),
        "quantity_in_militers": 750
    }
    mock_stream = [doc1, doc2]

    with patch("app.services.water_service.db", mock_db):
        # stream => [doc1, doc2]
        mock_db.collection.return_value.document.return_value.collection.return_value.where.return_value.where.return_value.stream.return_value = mock_stream

        history = get_water_intake_history_service("user123", "2025-01-01", "2025-01-02")
    assert len(history) == 2
    assert history[0]["date"] == "2025-01-01"
    assert history[0]["quantity_in_militers"] == 500
    assert history[1]["date"] == "2025-01-02"
    assert history[1]["quantity_in_militers"] == 750

def test_get_water_intake_history_service_exception():
    """
    On exception => returns []
    """
    with patch("app.services.water_service.db.collection", side_effect=Exception("DB fail")):
        history = get_water_intake_history_service("user123", "2025-01-01", "2025-01-05")
    assert history == []