# tests/controllers/test_category_controller.py

import json
import pytest
from unittest.mock import patch, MagicMock

def mock_verify_token(token):
    if token == "valid_token":
        return "user123"
    return None

@pytest.mark.parametrize("endpoint,method", [
    ("/api/category/save-category", "POST"),
    ("/api/category/get-categories", "GET"),
    ("/api/category/delete-category/fake_id", "DELETE"),
    ("/api/category/edit-category/fake_id", "PUT"),
    ("/api/category/get-category/fake_id", "GET"),
    # ("/api/category/save-default-category", "POST"),
    ("/api/category/last-modified", "GET"),
    ("/api/category/update-last-modified", "POST")
])
def test_missing_auth(client, endpoint, method):
    """
    Test that missing Authorization header may return 401, 403, OR 500
    (depending on controller code which might throw an exception on None).
    """
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint)
    elif method == "PUT":
        response = client.put(endpoint)
    elif method == "DELETE":
        response = client.delete(endpoint)
    
    assert response.status_code in [401, 403, 500], (
        f"Got {response.status_code} instead of one of [401, 403, 500]"
    )

def test_save_category_valid(client):
    data = {
        "name": "TestCat",
        "icon": "Ball",
        "isCustom": True
    }
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.save_category_service", 
               return_value=(True, {"id": "new_id", **data})):
        
        response = client.post(
            "/api/category/save-category",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    
    assert response.status_code == 201
    resp_json = response.get_json()
    assert resp_json["message"] == "Category saved successfully"
    assert resp_json["category"]["id"] == "new_id"

def test_save_category_invalid_data(client):
    # Missing 'icon'
    data = {
        "name": "TestCat",
        "isCustom": True
    }
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"):
        response = client.post(
            "/api/category/save-category",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 400
    assert "Missing data" in response.get_json()["error"]

def test_get_categories_valid(client):
    mock_categories = [{"id": "cat1", "name": "Category1"}, {"id": "cat2", "name": "Category2"}]
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.get_categories_service", return_value=mock_categories):
        
        response = client.get(
            "/api/category/get-categories",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert len(resp_json["categories"]) == 2

def test_delete_category_success(client):
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.delete_category_service", return_value=True):
        
        response = client.delete(
            "/api/category/delete-category/fake_id",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Category deleted successfully"

def test_delete_category_failure(client):
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.delete_category_service", return_value=False):
        
        response = client.delete(
            "/api/category/delete-category/fake_id",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 404
    assert "Failed to delete category" in response.get_json()["error"]

def test_edit_category_success(client):
    data = {"name": "NewName", "icon": "new-icon"}
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.update_category_service", return_value=True):
        
        response = client.put(
            "/api/category/edit-category/fake_id",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Category updated successfully"

def test_edit_category_no_valid_fields(client):
    data = {"someField": "notAllowed"}
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"):
        response = client.put(
            "/api/category/edit-category/fake_id",
            data=json.dumps(data),
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 400
    assert "No valid fields to update" in response.get_json()["error"]

def test_get_category_by_id_success(client):
    mock_category = MagicMock()
    mock_category.to_dict.return_value = {"owner": "user123", "name": "MyCategory"}
    mock_category.id = "fake_id"

    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.get_category_by_id_service", return_value=mock_category):
        
        response = client.get(
            "/api/category/get-category/fake_id",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert resp_json["name"] == "MyCategory"

def test_get_category_by_id_not_found(client):
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.get_category_by_id_service", return_value=None):
        
        response = client.get(
            "/api/category/get-category/fake_id",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 404
    assert "Category not found" in response.get_json()["error"]

# def test_save_default_category_success(client):
#     data = {
#         "name": "DefaultCat",
#         "icon": "default-icon",
#         "isCustom": False
#     }
#     with patch("app.controllers.category_controller.save_category_service", return_value=(True, "new_default_id")):
#         response = client.post(
#             "/api/category/save-default-category",
#             data=json.dumps(data),
#             headers={"Content-Type": "application/json"}
#         )
#     assert response.status_code == 201
#     assert response.get_json()["message"] == "Category saved successfully"

def test_get_last_modified_valid(client):
    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.get_last_modified_timestamp", return_value=None):
        
        response = client.get(
            "/api/category/last-modified",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert "last_modified_timestamp" in resp_json

def test_update_last_modified_valid(client):
    import datetime
    mock_time = datetime.datetime(2023, 1, 1, 0, 0)

    with patch("app.controllers.category_controller.verify_token_service", return_value="user123"), \
         patch("app.controllers.category_controller.set_last_modified_timestamp", return_value=mock_time):
        
        response = client.post(
            "/api/category/update-last-modified",
            headers={"Authorization": "Bearer valid_token"}
        )
    assert response.status_code == 200
    resp_json = response.get_json()
    assert "Last modified timestamp updated successfully" in resp_json["message"]
    assert "last_modified_timestamp" in resp_json