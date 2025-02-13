# tests/services/test_challenges_service.py

import pytest
from unittest.mock import patch, MagicMock
from app.services.challenges_service import (
    get_challenges_list_service,
    create_challenges_service
)

@pytest.mark.parametrize("challenge_type, mock_doc_exists", [
    ("physical", True),
    ("workouts", True),
    ("physical", False),  # doc doesn't exist
    ("workouts", False),  # doc doesn't exist
])
def test_get_challenges_list_service_success(challenge_type, mock_doc_exists):
    """
    Test successful retrieval of physical or workouts challenges.
    If doc doesn't exist, we create it. 
    """
    # Mock the Firestore 'db' calls
    mock_db = MagicMock()

    # user_ref = db.collection('challenges').document(uid)
    user_ref_mock = MagicMock()
    # user_doc = user_ref.get()
    user_doc_mock = MagicMock()
    user_doc_mock.exists = mock_doc_exists

    # Suppose each collection returns some docs
    challenge1 = MagicMock()
    challenge1.id = "challenge1_id"
    challenge1.to_dict.return_value = {"challenge": "Challenge1", "state": False}

    challenge2 = MagicMock()
    challenge2.id = "challenge2_id"
    challenge2.to_dict.return_value = {"challenge": "Challenge2", "state": True}

    # So we have a list of doc mocks to stream
    doc_stream = [challenge1, challenge2]

    user_ref_mock.get.return_value = user_doc_mock
    if challenge_type == "physical":
        # user_ref.collection('user_physical_challenges').stream()
        user_ref_mock.collection.return_value.stream.return_value = doc_stream
    else:
        # user_ref.collection('user_workouts_challenges').stream()
        user_ref_mock.collection.return_value.stream.return_value = doc_stream
    
    # Patch where the db is imported in the service
    with patch("app.services.challenges_service.db", mock_db):
        mock_db.collection.return_value.document.return_value = user_ref_mock
        result = get_challenges_list_service(uid="test_uid", type=challenge_type)
    
    # Check we got a list of challenges
    assert len(result) == 2
    assert result[0]["challenge"] == "Challenge1"
    assert result[1]["id"] == "challenge2_id"

def test_get_challenges_list_service_invalid_type():
    """
    Test that invalid challenge type returns None.
    """
    with patch("app.services.challenges_service.db", MagicMock()):
        result = get_challenges_list_service(uid="test_uid", type="invalid_type")
    assert result is None

def test_get_challenges_list_service_firestore_error():
    """
    Test that an exception in Firestore calls returns None.
    """
    mock_db = MagicMock()
    mock_db.collection.side_effect = Exception("Firestore error")
    with patch("app.services.challenges_service.db", mock_db):
        result = get_challenges_list_service(uid="test_uid", type="physical")
    assert result is None

def test_create_challenges_service_success():
    """
    Test the creation of challenges (both physical and workouts).
    """
    mock_db = MagicMock()

    user_ref_mock = MagicMock()
    user_doc_mock = MagicMock()
    user_doc_mock.exists = False  # assume doc doesn't exist initially
    user_ref_mock.get.return_value = user_doc_mock

    # Patch where the db is imported in the service
    with patch("app.services.challenges_service.db", mock_db):
        mock_db.collection.return_value.document.return_value = user_ref_mock
        result = create_challenges_service(uid="test_uid")

    assert result is True
    # We can do more asserts to check if set(...) is called,
    # but usually verifying True is enough if there's no exception.

def test_create_challenges_service_failure():
    """
    If Firestore raises an exception, returns False.
    """
    mock_db = MagicMock()
    mock_db.collection.side_effect = Exception("Firestore error")

    with patch("app.services.challenges_service.db", mock_db):
        result = create_challenges_service(uid="test_uid")

    assert result is False