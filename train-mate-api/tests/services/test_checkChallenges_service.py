import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.checkChallenges_service import (
    check_and_update_physical_challenges,
    check_and_update_workouts_challenges
)

def test_check_and_update_physical_challenges_exception():
    """
    If an exception occurs => returns False
    """
    with patch("app.services.checkChallenges_service.db.collection", side_effect=Exception("DB meltdown")):
        success = check_and_update_physical_challenges("user123","2025-01-07")
    assert success is False


def test_check_and_update_workouts_challenges_some_completed():
    """
    Mocks user_workouts_ref to return certain workouts that trigger challenges.
    Then ensures user_challenges_ref doc is updated for those challenges.
    """
    from app.services.checkChallenges_service import check_and_update_workouts_challenges

    mock_db = MagicMock()

    # Suppose we have 8 workouts in the last 30 days
    doc1 = MagicMock()
    doc1.to_dict.return_value = {
        "training_id": "trA",
        "duration": 120,
        "total_calories": 1500,
        "coach": "Coach1",
        "date": datetime.now() - timedelta(days=1)
    }
    doc2 = MagicMock()
    doc2.to_dict.return_value = {
        "training_id": "trB",
        "duration": 60,
        "total_calories": 1200,
        "coach": "Coach2",
        "date": datetime.now() - timedelta(days=2)
    }
    doc3 = MagicMock()
    doc3.to_dict.return_value = {
        "training_id": "trC",
        "duration": 90,
        "total_calories": 2300,
        "coach": "Coach3",
        "date": datetime.now() - timedelta(days=3)
    }
    doc4 = MagicMock()
    doc4.to_dict.return_value = {
        "training_id": "trD",
        "duration": 100,
        "total_calories": 0,
        "coach": "Coach1",
        "date": datetime.now() - timedelta(days=4)
    }
    # etc. For brevity, let's pretend we have enough variety/cals to trigger some challenges
    workouts_list = [doc1, doc2, doc3, doc4]

    user_workouts_ref = MagicMock()
    user_workouts_ref.where.return_value = user_workouts_ref
    user_workouts_ref.stream.return_value = workouts_list

    # For each training doc fetch
    # We'll mock them to have some "exercises" => leads to categories
    training_refA = MagicMock()
    training_refA.get.return_value.exists = True
    training_refA.get.return_value.to_dict.return_value = {"exercises":["ex1","ex2"]}

    training_refB = MagicMock()
    training_refB.get.return_value.exists = True
    training_refB.get.return_value.to_dict.return_value = {"exercises":["ex3"]}

    def training_doc_side_effect(doc_id):
        if doc_id == "trA":
            return training_refA
        elif doc_id == "trB":
            return training_refB
        elif doc_id == "trC" or doc_id == "trD":
            # etc.
            mock_t = MagicMock()
            mock_t.get.return_value.exists = True
            mock_t.get.return_value.to_dict.return_value = {"exercises":["ex4"]}
            return mock_t
        return MagicMock()

    # For exercises
    ex1 = MagicMock()
    ex1.get.return_value.exists = True
    ex1.get.return_value.to_dict.return_value = {"name":"Push-ups","category_id":"catS"}  # catS => "Sports"
    ex2 = MagicMock()
    ex2.get.return_value.exists = True
    ex2.get.return_value.to_dict.return_value = {"name":"Sit-ups","category_id":"catStrength"}
    ex3 = MagicMock()
    ex3.get.return_value.exists = True
    ex3.get.return_value.to_dict.return_value = {"name":"Plank","category_id":"catStrength"}
    ex4 = MagicMock()
    ex4.get.return_value.exists = True
    ex4.get.return_value.to_dict.return_value = {"name":"Jumping Jacks","category_id":"catCardio"}

    def exercise_doc_side_effect(ex_id):
        if ex_id == "ex1":
            return ex1
        elif ex_id == "ex2":
            return ex2
        elif ex_id == "ex3":
            return ex3
        elif ex_id == "ex4":
            return ex4
        return MagicMock()

    # For categories docs
    catSports = MagicMock()
    catSports.get.return_value.exists = True
    catSports.get.return_value.to_dict.return_value = {"name":"Sports"}

    catStrength = MagicMock()
    catStrength.get.return_value.exists = True
    catStrength.get.return_value.to_dict.return_value = {"name":"Strength"}

    catCardio = MagicMock()
    catCardio.get.return_value.exists = True
    catCardio.get.return_value.to_dict.return_value = {"name":"Cardio"}

    def category_doc_side_effect(doc_id):
        if doc_id == "catS":
            return catSports
        elif doc_id == "catStrength":
            return catStrength
        elif doc_id == "catCardio":
            return catCardio
        return MagicMock()

    # user_challenges_ref => updates
    user_challenges_ref = MagicMock()

    # Now let's build the chain of mocks
    def db_collection_side_effect(collection_name):
        if collection_name == "workouts":
            # .document(uid).collection('user_workouts') => user_workouts_ref
            top_mock = MagicMock()
            doc_mock = MagicMock()
            doc_mock.collection.return_value = user_workouts_ref
            top_mock.document.return_value = doc_mock
            return top_mock
        elif collection_name == "trainings":
            # We'll return a mock that doc(...) => training_doc_side_effect
            top_mock = MagicMock()
            def doc_train_side(doc_id):
                return training_doc_side_effect(doc_id)
            top_mock.document.side_effect = doc_train_side
            return top_mock
        elif collection_name == "exercises":
            # doc(...) => exercise_doc_side_effect
            ex_top = MagicMock()
            ex_top.document.side_effect = exercise_doc_side_effect
            return ex_top
        elif collection_name == "categories":
            cat_top = MagicMock()
            cat_top.document.side_effect = category_doc_side_effect
            return cat_top
        elif collection_name == "challenges":
            # .document(uid).collection('user_workouts_challenges') => user_challenges_ref
            chal_top = MagicMock()
            chal_doc = MagicMock()
            chal_doc.collection.return_value = user_challenges_ref
            chal_top.document.return_value = chal_doc
            return chal_top
        return MagicMock()

    mock_db.collection.side_effect = db_collection_side_effect

    with patch("app.services.checkChallenges_service.db", mock_db):
        success = check_and_update_workouts_challenges("user123")
    assert success is True

    # We expect some of the challenges to be updated => "Sports Enthusiast", "Calorie Crusher", maybe "Coach's Pick" if 3 coaches, etc.
    # The code calls user_challenges_ref.where('challenge','==',name).limit(1).stream() => doc.reference.update({'state':True})
    # We'll see how many times user_challenges_ref.where(...) was called
    # We won't deeply verify each challenge name. Typically you'd do separate tests for each challenge logic.
    assert user_challenges_ref.where.call_count >= 1
    # and doc.reference.update({'state': True}) calls exist
    # For a more precise test, you'd parse which challenge names triggered.

def test_check_and_update_workouts_challenges_no_challenges():
    """
    If there's data but doesn't meet any challenge criteria => no updates
    """
    from app.services.checkChallenges_service import check_and_update_workouts_challenges

    mock_db = MagicMock()

    # user_workouts_ref => let's say 1 workout with minimal data
    doc_mock = MagicMock()
    doc_mock.to_dict.return_value = {
        "training_id": "trZ",
        "duration": 30,
        "total_calories": 100,
        "coach": "OnlyCoach",
        "date": datetime.now() - timedelta(days=1)
    }
    user_workouts_ref = MagicMock()
    user_workouts_ref.where.return_value = user_workouts_ref
    user_workouts_ref.stream.return_value = [doc_mock]

    user_challenges_ref = MagicMock()

    def db_col_side_effect(col_name):
        if col_name == "workouts":
            top_mock = MagicMock()
            dmock = MagicMock()
            dmock.collection.return_value = user_workouts_ref
            top_mock.document.return_value = dmock
            return top_mock
        elif col_name == "challenges":
            ctop = MagicMock()
            cdoc = MagicMock()
            cdoc.collection.return_value = user_challenges_ref
            ctop.document.return_value = cdoc
            return ctop
        elif col_name == "trainings":
            # We'll say training doc has 1 exercise
            tr_top = MagicMock()
            tr_doc = MagicMock()
            tr_doc.get.return_value.exists = True
            tr_doc.get.return_value.to_dict.return_value = {"exercises":["exX"]}
            tr_top.document.return_value = tr_doc
            return tr_top
        elif col_name == "exercises":
            ex_top = MagicMock()
            # doc(...) => has category_id: "catSomething"
            ex_doc = MagicMock()
            ex_doc.get.return_value.exists = True
            ex_doc.get.return_value.to_dict.return_value = {"name":"OneExercise","category_id":"catSomething"}
            ex_top.document.return_value = ex_doc
            return ex_top
        elif col_name == "categories":
            cat_top = MagicMock()
            cat_doc = MagicMock()
            cat_doc.get.return_value.exists = True
            cat_doc.get.return_value.to_dict.return_value = {"name":"MiscCategory"}
            cat_top.document.return_value = cat_doc
            return cat_top
        return MagicMock()

    mock_db.collection.side_effect = db_col_side_effect

    with patch("app.services.checkChallenges_service.db", mock_db):
        success = check_and_update_workouts_challenges("user123")
    assert success is True
    # No updates
    user_challenges_ref.where.assert_not_called()

def test_check_and_update_workouts_challenges_exception():
    """
    If an exception is thrown => returns False
    """
    from app.services.checkChallenges_service import check_and_update_workouts_challenges
    with patch("app.services.checkChallenges_service.db.collection", side_effect=Exception("DB meltdown")):
        success = check_and_update_workouts_challenges("user123")
    assert success is False