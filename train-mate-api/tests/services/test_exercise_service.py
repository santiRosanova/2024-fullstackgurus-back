import pytest
from unittest.mock import patch, MagicMock
from app.services.exercise_service import (
    save_exercise,
    get_exercises,
    delete_exercise,
    update_exercise,
    get_all_exercises,
    get_exercise_by_category_id,
    get_exercise_by_id_service
)
from urllib.parse import quote

import pytest
from unittest.mock import patch, MagicMock
from app.services.exercise_service import save_exercise

def test_save_exercise_valid_category():
    """
    If get_category_by_id returns a valid category dict, we create a doc in 'exercises' => (True, exercise_data).
    """
    # 1) Mock get_category_by_id => return a dict indicating the category is valid
    mock_category_data = {"owner": "user123", "name": "SomeCategory"}
    
    # 2) Mock the db to handle exercises
    mock_db = MagicMock()
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "new_exercise_id"  # The Firestore-generated doc ID
    # .document() => mock_doc_ref
    mock_db.collection.return_value.document.return_value = mock_doc_ref

    with patch("app.services.exercise_service.get_category_by_id", return_value=mock_category_data), \
         patch("app.services.exercise_service.db", mock_db):
        
        success, exercise_data = save_exercise(
            uid="user123",
            name="Push-ups",
            calories_per_hour=300,
            public=False,
            category_id="cat123",
            training_muscle="Chest",
            image_url="http://example.com/image.jpg"
        )
    
    assert success is True
    assert exercise_data["id"] == "new_exercise_id"
    assert exercise_data["name"] == "Push-ups"
    # Check we wrote to 'exercises' collection
    mock_db.collection.assert_called_with("exercises")
    # Check doc creation
    mock_db.collection.return_value.document.assert_called_once()
    # Check the final data we set
    mock_doc_ref.set.assert_called_once_with({
        "name": "Push-ups",
        "calories_per_hour": 300,
        "public": False,
        "owner": "user123",
        "category_id": "cat123",
        "image_url": "http://example.com/image.jpg",
        "training_muscle": "Chest"
    })

def test_save_exercise_invalid_category():
    """
    If get_category_by_id returns None => (False, None)
    """
    with patch("app.services.exercise_service.get_category_by_id", return_value=None):
        success, exercise_data = save_exercise(
            uid="user123",
            name="Push-ups",
            calories_per_hour=300,
            public=False,
            category_id="cat123",
            training_muscle="Chest",
            image_url="http://example.com/image.jpg"
        )
    assert success is False
    assert exercise_data is None

def test_save_exercise_exception():
    """
    If something in the try block raises an exception => returns None
    """
    # e.g. we raise an exception when calling db.collection('exercises')
    mock_db = MagicMock()
    mock_db.collection.side_effect = Exception("DB meltdown")

    with patch("app.services.exercise_service.get_category_by_id", return_value={"owner":"user123"}), \
         patch("app.services.exercise_service.db", mock_db):
        
        result = save_exercise(
            uid="user123",
            name="Push-ups",
            calories_per_hour=300,
            public=False,
            category_id="cat123",
            training_muscle="Chest",
            image_url="http://example.com/image.jpg"
        )
    # The function in the except block does "return None"
    assert result is None

@pytest.mark.parametrize("show_public", [True, False])
def test_get_exercises_success(show_public):
    """
    Test retrieving exercises either public or user-specific.
    """
    mock_db = MagicMock()
    # Mock docs from Firestore
    doc1 = MagicMock()
    doc1.id = "ex1"
    doc1.to_dict.return_value = {"name": "Push-ups", "owner": "user123"}
    doc2 = MagicMock()
    doc2.id = "ex2"
    doc2.to_dict.return_value = {"name": "Sit-ups", "owner": "user123"}

    with patch("app.services.exercise_service.db", mock_db):
        # .where(...).stream() returns [doc1, doc2]
        mock_db.collection.return_value.where.return_value.stream.return_value = [doc1, doc2]

        exercises = get_exercises("user123", show_public=show_public)
    
    # Basic checks
    assert len(exercises) == 2
    assert exercises[0]["id"] == "ex1"
    if show_public:
        # We call: exercises_ref.where('public', '==', True)
        mock_db.collection.return_value.where.assert_called_with("public", "==", True)
    else:
        # We call: exercises_ref.where('owner', '==', uid)
        mock_db.collection.return_value.where.assert_called_with("owner", "==", "user123")

def test_get_exercises_exception():
    """
    If an exception is raised, returns [].
    """
    with patch("app.services.exercise_service.db.collection", side_effect=Exception("Firestore error")):
        exercises = get_exercises("user123", show_public=False)
    assert exercises == []

def test_delete_exercise_success():
    """
    If exercise exists and belongs to user => delete from Firestore and remove image if present.
    """
    mock_db = MagicMock()
    mock_storage = MagicMock()

    mock_doc_snap = MagicMock()
    mock_doc_snap.exists = True
    mock_doc_snap.to_dict.return_value = {
        "owner": "user123",
        "image_url": "http://storage/path/to%2Fimage.jpg"
    }

    with patch("app.services.exercise_service.db", mock_db), \
         patch("app.services.exercise_service.storage_client", mock_storage):
        
        # doc get => doc exists
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc_snap
        
        success = delete_exercise("user123", "ex123")
    
    assert success is True
    # Check we deleted from Firestore
    mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    # Check we deleted from storage
    # The raw path might be "path/to%2Fimage.jpg", so ensure we unquote it
    mock_storage.bucket.return_value.blob.assert_called_once()
    mock_storage.bucket.return_value.blob.return_value.delete.assert_called_once()

def test_delete_exercise_not_found_or_wrong_owner():
    """
    If doc doesn't exist or doc.owner != uid => return False
    """
    mock_db = MagicMock()
    mock_doc_snap = MagicMock()
    mock_doc_snap.exists = False

    with patch("app.services.exercise_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc_snap
        success = delete_exercise("user123", "ex123")
    assert success is False

def test_delete_exercise_exception():
    """
    On exception => return False
    """
    with patch("app.services.exercise_service.db.collection", side_effect=Exception("Firestore error")):
        success = delete_exercise("user123", "ex123")
    assert success is False

def test_update_exercise_success():
    """
    If exercise exists and belongs to user => update fields, optionally delete old image.
    """
    mock_db = MagicMock()
    mock_storage = MagicMock()

    mock_doc_snap = MagicMock()
    mock_doc_snap.exists = True
    mock_doc_snap.to_dict.return_value = {"owner": "user123"}

    with patch("app.services.exercise_service.db", mock_db), \
         patch("app.services.exercise_service.storage_client", mock_storage):
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc_snap

        update_data = {"name": "NewName", "calories_per_hour": 350}
        success = update_exercise("user123", "ex123", update_data, old_image_url="http://storage/old_image.jpg")
    
    assert success is True
    # Check Firestore update called
    mock_db.collection.return_value.document.return_value.update.assert_called_once_with(update_data)
    # Check old image deleted
    mock_storage.bucket.return_value.blob.return_value.delete.assert_called_once()

def test_update_exercise_wrong_owner():
    """
    If doc.owner != uid => return False
    """
    mock_db = MagicMock()
    mock_doc_snap = MagicMock()
    mock_doc_snap.exists = True
    mock_doc_snap.to_dict.return_value = {"owner": "another_user"}

    with patch("app.services.exercise_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc_snap

        success = update_exercise("user123", "ex123", {"calories_per_hour": 400}, old_image_url=None)
    assert success is False

def test_update_exercise_not_found():
    """
    If doc doesn't exist => return False
    """
    mock_db = MagicMock()
    mock_doc_snap = MagicMock()
    mock_doc_snap.exists = False

    with patch("app.services.exercise_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc_snap
        success = update_exercise("user123", "ex123", {"calories_per_hour": 400}, old_image_url=None)
    assert success is False

def test_update_exercise_exception():
    with patch("app.services.exercise_service.db.collection", side_effect=Exception("Firestore error")):
        success = update_exercise("user123", "ex123", {"name": "NewName"}, old_image_url=None)
    assert success is False

def test_get_all_exercises_exception():
    with patch("app.services.exercise_service.db.collection", side_effect=Exception("Firestore error")):
        result = get_all_exercises()
    assert result == []

def test_get_exercise_by_category_id_success():
    mock_db = MagicMock()
    doc1 = MagicMock()
    doc1.id = "exCat1"
    doc1.to_dict.return_value = {"owner": "user123", "category_id": "cat123"}
    doc2 = MagicMock()
    doc2.id = "exCat2"
    doc2.to_dict.return_value = {"owner": "default", "category_id": "cat123"}

    with patch("app.services.exercise_service.db", mock_db):
        # Chain .where(...).where(...).stream() => [doc1, doc2]
        mock_db.collection.return_value.where.return_value.where.return_value.stream.return_value = [doc1, doc2]
        exercises = get_exercise_by_category_id("cat123", "user123")

    assert len(exercises) == 2
    assert exercises[0]["id"] == "exCat1"
    assert exercises[1]["owner"] == "default"

def test_get_exercise_by_category_id_exception():
    with patch("app.services.exercise_service.db.collection", side_effect=Exception("Firestore error")):
        result = get_exercise_by_category_id("cat123", "user123")
    assert result == []

def test_get_exercise_by_id_service_success():
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"name": "Bicep Curls", "owner": "user123"}

    with patch("app.services.exercise_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        exercise = get_exercise_by_id_service("ex_id_456")
    assert exercise is not None
    assert exercise["name"] == "Bicep Curls"

def test_get_exercise_by_id_service_not_found():
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch("app.services.exercise_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        exercise = get_exercise_by_id_service("ex_id_999")
    assert exercise is None

def test_get_exercise_by_id_service_exception():
    with patch("app.services.exercise_service.db.collection", side_effect=Exception("Firestore error")):
        exercise = get_exercise_by_id_service("ex_id_err")
    assert exercise is None