import pytest
from unittest.mock import patch, MagicMock
from app.services.user_service import (
    verify_token_service,
    save_user_info_service,
    get_user_info_service,
    update_user_info_service
)


def test_verify_token_service_success():
    """
    If auth.verify_id_token(token) succeeds, we return decoded_token['uid'].
    """
    mock_auth = MagicMock()
    mock_auth.verify_id_token.return_value = {"uid": "user123"}

    with patch("app.services.user_service.auth", mock_auth):
        uid = verify_token_service("valid_token")
    assert uid == "user123"
    mock_auth.verify_id_token.assert_called_once_with("valid_token")

def test_verify_token_service_failure():
    """
    If auth.verify_id_token(token) raises an exception, return None.
    """
    mock_auth = MagicMock()
    mock_auth.verify_id_token.side_effect = Exception("Token invalid")

    with patch("app.services.user_service.auth", mock_auth):
        uid = verify_token_service("bad_token")
    assert uid is None
    mock_auth.verify_id_token.assert_called_once_with("bad_token")


def test_save_user_info_service_with_data():
    """
    If there's valid data, we set the user doc and call create_challenges_service.
    """
    mock_db = MagicMock()
    mock_create_challenges = MagicMock()

    # Suppose data includes some fields
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "weight": 70
    }

    with patch("app.services.user_service.db", mock_db), \
         patch("app.services.user_service.create_challenges_service", mock_create_challenges):

        save_user_info_service("user123", user_data)
    
    # We expect db.collection('users').document('user123').set(...) with the final dict
    # The final dict includes 'email', 'fullName'='Test User', 'weight'=70
    expected_dict = {
        "email": "test@example.com",
        "fullName": "Test User",
        "weight": 70
    }
    mock_db.collection.assert_called_with("users")
    doc_mock = mock_db.collection.return_value.document.return_value
    doc_mock.set.assert_called_once_with(expected_dict)

    # create_challenges_service called once with uid="user123"
    mock_create_challenges.assert_called_once_with("user123")

def test_save_user_info_service_no_data():
    """
    If no valid fields in data, we do not set() or call create_challenges_service.
    """
    mock_db = MagicMock()
    mock_create_challenges = MagicMock()

    # This data has only None or missing fields
    user_data = {
        "email": None,
        "name": None,
        "sex": None
    }

    with patch("app.services.user_service.db", mock_db), \
         patch("app.services.user_service.create_challenges_service", mock_create_challenges):
        
        save_user_info_service("user123", user_data)
    
    # No set calls
    doc_mock = mock_db.collection.return_value.document.return_value
    doc_mock.set.assert_not_called()
    # No challenges created
    mock_create_challenges.assert_not_called()


def test_get_user_info_service_existing_doc():
    """
    If user doc exists => return doc.to_dict().
    """
    mock_db = MagicMock()
    mock_auth = MagicMock()

    doc_mock = MagicMock()
    doc_mock.exists = True
    doc_mock.to_dict.return_value = {"email": "existing@example.com"}

    with patch("app.services.user_service.db", mock_db), \
         patch("app.services.user_service.auth", mock_auth):
        
        # user_ref.get() => doc_mock
        mock_db.collection.return_value.document.return_value.get.return_value = doc_mock

        user_info = get_user_info_service("user123")
    
    assert user_info == {"email": "existing@example.com"}
    mock_db.collection.assert_called_with("users")
    mock_db.collection.return_value.document.assert_called_with("user123")
    # auth.get_user not called because doc exists
    mock_auth.get_user.assert_not_called()

def test_get_user_info_service_doc_not_exist():
    """
    If doc doesn't exist, we fetch user from auth.get_user(uid) => user.email => save_user_info_service => return new doc
    """
    mock_db = MagicMock()
    mock_auth = MagicMock()
    mock_create_challenges = MagicMock()

    # user doc doesn't exist initially
    doc_mock = MagicMock()
    doc_mock.exists = False

    user_record = MagicMock()
    user_record.email = "fresh@example.com"

    # After we save info, presumably the doc now returns something
    new_doc_mock = MagicMock()
    new_doc_mock.exists = True
    new_doc_mock.to_dict.return_value = {
        "email": "fresh@example.com"
    }

    with patch("app.services.user_service.db", mock_db), \
         patch("app.services.user_service.auth", mock_auth), \
         patch("app.services.user_service.create_challenges_service", mock_create_challenges), \
         patch("app.services.user_service.save_user_info_service") as mock_save_info:
        
        # doc_mock on first get
        mock_db.collection.return_value.document.return_value.get.return_value = doc_mock
        mock_auth.get_user.return_value = user_record

        # After calling save_user_info_service, we do doc again => new_doc_mock
        mock_db.collection.return_value.document.return_value.get.side_effect = [doc_mock, new_doc_mock]

        user_info = get_user_info_service("user123")

    # We expect user_info = {"email":"fresh@example.com"}
    assert user_info == {"email": "fresh@example.com"}

    # verify we called auth.get_user("user123") because doc didn't exist
    mock_auth.get_user.assert_called_once_with("user123")
    # verify we called save_user_info_service with the email from user_record
    mock_save_info.assert_called_once_with("user123", {"email": "fresh@example.com"})


def test_update_user_info_service_doc_exists():
    """
    If doc exists, we do user_ref.update(...) with updated fields
    """
    from app.services.user_service import update_user_info_service
    from unittest.mock import patch, MagicMock

    # We'll create two separate mocks:
    # doc_snapshot_mock => the snapshot from .get()
    # doc_ref_mock => the DocumentReference that .update(...) is actually called on.
    doc_snapshot_mock = MagicMock()
    doc_snapshot_mock.exists = True  # doc found

    doc_ref_mock = MagicMock()  # This is the object that has .update(...)
    doc_ref_mock.get.return_value = doc_snapshot_mock

    # Our Firestore mock:
    mock_db = MagicMock()
    # For db.collection("users").document("user123"), we return doc_ref_mock
    mock_db.collection.return_value.document.return_value = doc_ref_mock

    data = {
        "full_name": "Updated Name",
        "gender": "M",
        "height": 180,
        "weight": 75,
        "birthday": "2000-01-01"
    }

    expected_update = {
        "fullName": "Updated Name",
        "gender": "M",
        "height": 180,
        "weight": 75,
        "birthday": "2000-01-01"
    }

    with patch("app.services.user_service.db", mock_db):
        update_user_info_service("user123", data)

    # We confirm user_ref.update(...) was called on doc_ref_mock, once, with expected_update
    doc_ref_mock.update.assert_called_once_with(expected_update)

def test_update_user_info_service_doc_not_exists():
    """
    If doc does not exist, we call save_user_info_service(uid, data).
    """
    mock_db = MagicMock()
    doc_mock = MagicMock()
    doc_mock.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = doc_mock

    mock_save_user = MagicMock()

    data = {"full_name":"No doc yet","gender":"F"}

    with patch("app.services.user_service.db", mock_db), \
         patch("app.services.user_service.save_user_info_service", mock_save_user):
        
        update_user_info_service("user123", data)

    # doc doesn't exist => we call save_user_info_service
    mock_save_user.assert_called_once_with("user123", data)
    # doc_mock.update not called
    doc_mock.update.assert_not_called()