import pytest
from unittest.mock import patch, MagicMock
from app.services.category_service import (
    save_category,
    get_public_categories,
    get_personalized_categories,
    get_categories,
    get_category_by_id,
    delete_category,
    update_category
)

@pytest.mark.parametrize("name, icon, isCustom, owner", [
    ("Food", "food-icon", True, "user123"),
    ("Groceries", "groceries-icon", False, None)
])
def test_save_category_success(name, icon, isCustom, owner):
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "fake_doc_id"

    # Mock db.collection().document() -> returns mock_doc_ref
    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value = mock_doc_ref
        
        success, category_data = save_category(name, icon, isCustom, owner)
    
    assert success is True
    assert category_data["name"] == name
    assert category_data["icon"] == icon
    assert category_data["isCustom"] == isCustom
    assert category_data["owner"] == owner
    assert category_data["id"] == mock_doc_ref.id

def test_save_category_failure():
    # Force an exception to simulate Firestore error
    with patch("app.services.category_service.db.collection", side_effect=Exception("DB Error")):
        success, category_data = save_category("Fail", "fail-icon", True, "user123")
    
    assert success is False
    assert category_data is None

def test_get_public_categories_success():
    mock_docs = [MagicMock(), MagicMock()]
    with patch("app.services.category_service.db.collection") as mock_collection:
        # Simulate .where(...).stream() returning list of docs
        mock_collection.return_value.where.return_value.stream.return_value = mock_docs
        
        result = get_public_categories()
    
    assert len(list(result)) == 2  # or convert to list to iterate

def test_get_public_categories_failure():
    # Force an exception
    with patch("app.services.category_service.db.collection", side_effect=Exception("DB Error")):
        result = get_public_categories()
    # Should return an empty list on exception
    assert result == []

def test_get_personalized_categories_success():
    mock_docs = [MagicMock(), MagicMock(), MagicMock()]
    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.where.return_value.stream.return_value = mock_docs
        
        result = get_personalized_categories("user123")
    
    assert len(list(result)) == 3

def test_get_personalized_categories_failure():
    with patch("app.services.category_service.db.collection", side_effect=Exception("DB Error")):
        result = get_personalized_categories("user123")
    assert result == []

def test_get_categories_success():
    personalized_docs = [MagicMock(), MagicMock()]
    public_docs = [MagicMock()]

    # Each doc mock needs to have .to_dict() and .id
    for i, doc in enumerate(personalized_docs):
        doc.to_dict.return_value = {"owner": "user123", "name": f"Personalized{i}"}
        doc.id = f"personalized_id_{i}"
    for i, doc in enumerate(public_docs):
        doc.to_dict.return_value = {"owner": "default", "name": f"Public{i}"}
        doc.id = f"public_id_{i}"

    with patch("app.services.category_service.get_personalized_categories", return_value=personalized_docs), \
         patch("app.services.category_service.get_public_categories", return_value=public_docs):
        result = get_categories("user123")
    
    assert len(result) == 3
    assert result[0]["name"] == "Personalized0"
    assert result[1]["name"] == "Personalized1"
    assert result[2]["name"] == "Public0"

def test_get_categories_failure():
    with patch("app.services.category_service.get_personalized_categories", side_effect=Exception("Boom!")), \
         patch("app.services.category_service.get_public_categories", return_value=[]):
        result = get_categories("user123")
    assert result == []

def test_get_category_by_id_success():
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"owner": "user123", "name": "TestCategory"}

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        
        category = get_category_by_id("user123", "fake_id")

    assert category is not None
    assert category["name"] == "TestCategory"

def test_get_category_by_id_not_exists():
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        
        category = get_category_by_id("user123", "fake_id")
    assert category is None

def test_get_category_by_id_wrong_owner():
    mock_doc = MagicMock()
    mock_doc.exists = True
    # This category belongs to a different user
    mock_doc.to_dict.return_value = {"owner": "someone_else", "name": "TestCategory"}

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        
        category = get_category_by_id("user123", "fake_id")
    assert category is None

def test_delete_category_success():
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"owner": "user123"}

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        
        success = delete_category("user123", "fake_id")

    assert success is True
    mock_collection.return_value.document.return_value.delete.assert_called_once()

def test_delete_category_not_found():
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        
        success = delete_category("user123", "fake_id")
    assert success is False

def test_delete_category_wrong_owner():
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"owner": "someone_else"}

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        
        success = delete_category("user123", "fake_id")
    assert success is False

def test_delete_category_failure():
    # Force exception
    with patch("app.services.category_service.db.collection", side_effect=Exception("DB Error")):
        success = delete_category("user123", "fake_id")
    assert success is False

def test_update_category_success():
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"owner": "user123"}

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        success = update_category("user123", "fake_id", {"name": "New Name"})
    
    assert success is True
    mock_collection.return_value.document.return_value.update.assert_called_once_with({"name": "New Name"})

def test_update_category_not_found():
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        success = update_category("user123", "fake_id", {"name": "New Name"})
    
    assert success is False

def test_update_category_wrong_owner():
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"owner": "someone_else"}

    with patch("app.services.category_service.db.collection") as mock_collection:
        mock_collection.return_value.document.return_value.get.return_value = mock_doc
        success = update_category("user123", "fake_id", {"name": "New Name"})
    
    assert success is False

def test_update_category_failure():
    with patch("app.services.category_service.db.collection", side_effect=Exception("DB Error")):
        success = update_category("user123", "fake_id", {"name": "New Name"})
    assert success is False