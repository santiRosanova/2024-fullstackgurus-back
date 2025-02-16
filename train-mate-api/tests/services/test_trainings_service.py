import pytest
from unittest.mock import patch, MagicMock
from collections import Counter
from app.services.trainings_service import (
    save_user_training,
    get_user_trainings,
    get_training_by_id,
    get_popular_exercises,
    recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise
)

def test_save_user_training_success():
    """
    Checks if save_user_training creates a user doc if not exists, adds a new training,
    and returns the expected dict with 'id', 'calories_per_hour_mean', etc.
    """
    mock_db = MagicMock()

    # user_ref.get() => doc doesn't exist
    mock_user_doc = MagicMock()
    mock_user_doc.exists = False

    # user_trainings_ref.add(...) => returns (None, mock_doc_ref)
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "new_training_id"

    with patch("app.services.trainings_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc
        mock_db.collection.return_value.document.return_value.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = save_user_training(
            uid="user123",
            data={"name": "My Training"},
            exercises_ids=["ex1", "ex2"],
            calories_per_hour_mean=350
        )
    
    assert result["id"] == "new_training_id"
    assert result["calories_per_hour_mean"] == 350
    assert result["exercises"] == ["ex1", "ex2"]
    assert result["owner"] == "user123"
    # Check calls
    mock_db.collection.assert_called_with("trainings")
    mock_db.collection.return_value.document.assert_called_with("user123")

def test_save_user_training_exception():
    """
    If Firestore operations raise an exception, we can see how your code behaves.
    But note your current code does NOT catch exceptions in save_user_training.
    That means it will bubble up. We can still test it.
    """
    with patch("app.services.trainings_service.db.collection", side_effect=Exception("DB error")):
        with pytest.raises(Exception) as exc_info:
            save_user_training(
                uid="user123",
                data={"name": "Bad Training"},
                exercises_ids=["ex1"],
                calories_per_hour_mean=100
            )
    assert "DB error" in str(exc_info.value)

def test_get_user_trainings_success():
    mock_db = MagicMock()

    # Fake training docs
    mock_training1 = MagicMock()
    mock_training1.id = "t1"
    mock_training1.to_dict.return_value = {"exercises": ["ex1", "ex2"], "name": "Leg Day"}

    mock_training2 = MagicMock()
    mock_training2.id = "t2"
    mock_training2.to_dict.return_value = {"exercises": ["ex3"], "name": "Arm Day"}

    # This is what we want from .stream() when we look up 'trainings/.../user_trainings'
    mock_trainings_stream = [mock_training1, mock_training2]

    # Fake exercise docs
    mock_ex1 = MagicMock()
    mock_ex1.exists = True
    mock_ex1.to_dict.return_value = {"name": "Squats", "calories_per_hour": 400}
    
    mock_ex2 = MagicMock()
    mock_ex2.exists = True
    mock_ex2.to_dict.return_value = {"name": "Lunges", "calories_per_hour": 300}
    
    mock_ex3 = MagicMock()
    mock_ex3.exists = False  # pretend ex3 doc doesn't exist

    # We'll define a function that returns a different mock object
    # depending on which collection name is requested.
    def mock_collection_side_effect(collection_name):
        if collection_name == "trainings":
            # Return a mock that can handle .document(uid).collection('user_trainings').stream()
            trainings_top_mock = MagicMock()
            doc_mock = MagicMock()
            # doc_mock.collection("user_trainings").stream() => mock_trainings_stream
            user_trainings_mock = MagicMock()
            user_trainings_mock.stream.return_value = mock_trainings_stream
            doc_mock.collection.return_value = user_trainings_mock

            # doc_mock.get().exists => True to simulate user doc existing
            doc_get_mock = MagicMock()
            doc_get_mock.exists = True
            doc_mock.get.return_value = doc_get_mock

            # So trainings_top_mock.document(uid) => doc_mock
            trainings_top_mock.document.return_value = doc_mock
            return trainings_top_mock

        elif collection_name == "exercises":
            # Return a mock that can handle .document(ex_id).get() for ex1, ex2, ex3
            exercises_mock = MagicMock()
            
            def doc_side_effect(ex_id):
                doc_for_ex = MagicMock()
                if ex_id == "ex1":
                    doc_for_ex.get.return_value = mock_ex1
                elif ex_id == "ex2":
                    doc_for_ex.get.return_value = mock_ex2
                elif ex_id == "ex3":
                    doc_for_ex.get.return_value = mock_ex3
                else:
                    # unknown => doc.exists=False
                    doc_for_ex.get.return_value = MagicMock(exists=False)
                return doc_for_ex

            exercises_mock.document.side_effect = doc_side_effect
            return exercises_mock

        else:
            # If code calls db.collection('some_other'), just return a generic mock
            return MagicMock()

    # Now patch db so that every time .collection(...) is called, we use the side effect above
    mock_db.collection.side_effect = mock_collection_side_effect

    with patch("app.services.trainings_service.db", mock_db):
        from app.services.trainings_service import get_user_trainings
        result = get_user_trainings("user123")
    
    # We expect 2 training objects returned
    assert len(result) == 2

    # 't1' includes ex1, ex2 => ex3 is missing doc
    # first training => 'Squats', 'Lunges'
    assert result[0]["id"] == "t1"
    assert result[0]["exercises"][0]["name"] == "Squats"
    assert result[0]["exercises"][1]["name"] == "Lunges"

    # second training => ex3 doesn't exist => 0 exercises
    assert result[1]["id"] == "t2"
    assert len(result[1]["exercises"]) == 0

def test_get_user_trainings_exception():
    """
    If an exception occurs inside .stream(), code prints error and returns [].
    """
    from app.services.trainings_service import get_user_trainings
    from unittest.mock import patch, MagicMock

    # We'll patch db.collection("trainings") normally, but cause an exception
    # when user_trainings_ref.stream() is called.
    mock_db = MagicMock()

    # For db.collection("trainings").document(uid).collection("user_trainings")
    # we return a mock with .stream.side_effect = Exception("DB error")
    user_trainings_mock = MagicMock()
    user_trainings_mock.stream.side_effect = Exception("DB error")

    doc_mock = MagicMock()
    doc_mock.collection.return_value = user_trainings_mock

    trainings_mock = MagicMock()
    trainings_mock.document.return_value = doc_mock

    def collection_side_effect(collection_name):
        if collection_name == "trainings":
            return trainings_mock
        # For other collections, just return a generic mock
        return MagicMock()

    mock_db.collection.side_effect = collection_side_effect

    with patch("app.services.trainings_service.db", mock_db):
        trainings = get_user_trainings("user123")

    # The code catches the exception inside the try block and returns []
    assert trainings == []

def test_get_training_by_id_success():
    """
    If the doc exists, return its dict.
    """
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"exercises": ["ex1"], "owner": "user123"}

    with patch("app.services.trainings_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc

        training = get_training_by_id("user123", "train123")
    assert training is not None
    assert training["owner"] == "user123"

def test_get_training_by_id_not_exists():
    """
    If doc doesn't exist => return None
    """
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch("app.services.trainings_service.db", mock_db):
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        
        training = get_training_by_id("user123", "unknown")
    assert training is None

def test_get_popular_exercises_success():
    """
    get_popular_exercises => gather 'public' exercises from training docs,
    then return top 5. We'll simulate 3 docs referencing ex1, ex2, ex3 (some repeated).
    """
    mock_db = MagicMock()
    # training doc mocks from a 'collection_group' => user_trainings
    t1 = MagicMock()
    t1.to_dict.return_value = {"exercises": ["ex1", "ex2"]}
    t2 = MagicMock()
    t2.to_dict.return_value = {"exercises": ["ex2", "ex3"]}
    t3 = MagicMock()
    t3.to_dict.return_value = {"exercises": ["ex1", "ex2", "ex2"]}  # ex2 repeated
    # Stream => [t1, t2, t3]
    mock_trainings = [t1, t2, t3]

    # Mock exercises in Firestore
    mock_ex1 = MagicMock()
    mock_ex1.exists = True
    mock_ex1.to_dict.return_value = {"public": True, "name": "Push-ups"}
    mock_ex2 = MagicMock()
    mock_ex2.exists = True
    mock_ex2.to_dict.return_value = {"public": True, "name": "Squats"}
    mock_ex3 = MagicMock()
    mock_ex3.exists = True
    mock_ex3.to_dict.return_value = {"public": False, "name": "Crunches"}  # not public => won't count

    with patch("app.services.trainings_service.db", mock_db):
        mock_db.collection_group.return_value.stream.return_value = mock_trainings

        # We call db.collection('exercises').document(ex_id).get() for each ex_id
        def get_exercise_doc(ex_id):
            if ex_id == "ex1":
                return mock_ex1
            elif ex_id == "ex2":
                return mock_ex2
            elif ex_id == "ex3":
                return mock_ex3
            return MagicMock(exists=False)
        
        def mock_document_side_effect(arg):
            return MagicMock(get=lambda: get_exercise_doc(arg))
        
        mock_db.collection.return_value.document.side_effect = mock_document_side_effect

        popular = get_popular_exercises()
    
    # ex1 appears 2 times total
    # ex2 appears 5 times total (t1 =>1, t2 =>1, t3 => 2 more times? Actually 3 more times if we count duplicates strictly? or 2? 
    #   The code doesn't deduplicate, so the code increments for each reference. t1 => ex2 once, t2 => ex2 once, t3 => ex2 2 times => total 4. 
    # ex3 is not public => 0
    # So top: ex2 => 4, ex1 => 2
    # Should only include "public": True
    assert len(popular) == 2
    assert popular[0]["exercise_id"] == "ex2"
    assert popular[0]["count"] == 4
    assert popular[1]["exercise_id"] == "ex1"
    assert popular[1]["count"] == 2

def test_get_popular_exercises_exception():
    """
    On exception => return [].
    """
    with patch("app.services.trainings_service.db.collection_group", side_effect=Exception("DB error")):
        result = get_popular_exercises()
    assert result == []

def test_recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise_success():
    """
    If we find trainings that reference the exercise, we sum up all exercises' cph and update the doc.
    """
    from app.services.trainings_service import recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise
    from unittest.mock import patch, MagicMock

    # 1) Mock training docs
    t1 = MagicMock()
    t1.id = "train1"
    t1.to_dict.return_value = {"exercises": ["ex1", "ex2"]}

    t2 = MagicMock()
    t2.id = "train2"
    t2.to_dict.return_value = {"exercises": ["ex3"]}

    trainings_list = [t1, t2]

    # 2) Mock exercise docs
    mock_ex1 = MagicMock()
    mock_ex1.exists = True
    mock_ex1.to_dict.return_value = {"calories_per_hour": 300}

    mock_ex2 = MagicMock()
    mock_ex2.exists = True
    mock_ex2.to_dict.return_value = {"calories_per_hour": 200}

    mock_ex3 = MagicMock()
    mock_ex3.exists = True
    mock_ex3.to_dict.return_value = {"calories_per_hour": 999}

    # We'll need separate mocks for doc("train1") and doc("train2") to track .update(...) calls
    train1_doc_mock = MagicMock()  # for doc("train1")
    train2_doc_mock = MagicMock()  # for doc("train2")

    #
    # Side effect function for db.collection(...) calls
    #
    def collection_side_effect(collection_name):
        if collection_name == "trainings":
            #
            # Return a mock that, when .document(uid).collection("user_trainings").stream(),
            # yields [t1, t2].
            #
            trainings_top_mock = MagicMock()

            # doc(uid) => doc_mock
            doc_mock = MagicMock()

            # user_trainings_mock => for .collection("user_trainings")
            user_trainings_mock = MagicMock()
            user_trainings_mock.stream.return_value = trainings_list

            # We ALSO need .document("train1") or .document("train2") inside "user_trainings"
            def doc_train_id_side_effect(doc_id):
                if doc_id == "train1":
                    return train1_doc_mock
                elif doc_id == "train2":
                    return train2_doc_mock
                # fallback
                return MagicMock()

            user_trainings_mock.document.side_effect = doc_train_id_side_effect

            # doc_mock.collection("user_trainings") => user_trainings_mock
            doc_mock.collection.return_value = user_trainings_mock
            # Finally, trainings_top_mock.document(uid) => doc_mock
            trainings_top_mock.document.return_value = doc_mock
            return trainings_top_mock

        elif collection_name == "exercises":
            #
            # Return a mock that, when .document(ex_id).get(), returns mock_ex1, mock_ex2, or mock_ex3
            #
            exercises_mock = MagicMock()

            def doc_side_effect(ex_id):
                mock_doc = MagicMock()
                if ex_id == "ex1":
                    mock_doc.get.return_value = mock_ex1
                elif ex_id == "ex2":
                    mock_doc.get.return_value = mock_ex2
                elif ex_id == "ex3":
                    mock_doc.get.return_value = mock_ex3
                else:
                    mock_doc.get.return_value = MagicMock(exists=False)
                return mock_doc

            exercises_mock.document.side_effect = doc_side_effect
            return exercises_mock

        else:
            # For any other collection, just return a generic mock
            return MagicMock()

    # Our main db mock
    mock_db = MagicMock()
    mock_db.collection.side_effect = collection_side_effect

    with patch("app.services.trainings_service.db", mock_db):
        result = recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise("user123", "ex2")

    # The code returns None on success (False only if there's an exception)
    assert result is not False, "Expected success, got an exception"

    # Now check which doc got updated
    # Only "train1" references ex2 => it should get updated with cphMean=250
    assert train1_doc_mock.update.call_count == 1, (
        f"Expected train1_doc_mock.update(...) once, got {train1_doc_mock.update.call_count}"
    )
    update_args = train1_doc_mock.update.call_args[0][0]
    assert update_args == {"calories_per_hour_mean": 250}, f"Got update data {update_args}"

    # "train2" does NOT have ex2 => no update
    assert train2_doc_mock.update.call_count == 0, "train2_doc_mock should not be updated"

def test_recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise_exception():
    with patch("app.services.trainings_service.db.collection", side_effect=Exception("DB error")):
        result = recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise("user123", "ex1")
    # On exception => returns False
    assert result is False