from firebase_setup import db
from datetime import datetime, timedelta

# Get all goals for a user
def get_all_goals_service(uid):
    try:
        goals_ref = db.collection('goals').document(uid).collection('user_goals')
        goals = goals_ref.stream()
        goals_list = []
        for goal in goals:
            goal_data = goal.to_dict()
            goal_data['id'] = goal.id
            goals_list.append(goal_data)
        return goals_list
    except Exception as e:
        print(f"Error getting goals: {e}")
        return None

# Create a new goal


def create_goal_service(uid, data):
    try:
        # Convert start and end dates to datetime objects with a default time of 10:00 AM
        if 'startDate' in data and isinstance(data['startDate'], str):
            try:
                start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
                start_date = start_date.replace(hour=10, minute=0)  # Set time to 10:00 AM
            except ValueError:
                raise ValueError("Invalid start date format. Use 'YYYY-MM-DD'.")
        else:
            start_date = None

        if 'endDate' in data and isinstance(data['endDate'], str):
            try:
                end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')
                end_date = end_date.replace(hour=10, minute=0)  # Set time to 10:00 AM
            except ValueError:
                raise ValueError("Invalid end date format. Use 'YYYY-MM-DD'.")
        else:
            end_date = None

        # Check if dates are valid
        yesterday = datetime.now() - timedelta(days=1)

        if start_date and start_date < yesterday:
            return {"error": "Start date cannot be in the past."}, 400
        if end_date and end_date < yesterday:
            return {"error": "End date cannot be in the past."}, 400
        if start_date and end_date and end_date < start_date:
            return {"error": "End date must be after start date."}, 400

        # Set up the goal document reference and data
        user_ref = db.collection('goals').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            user_ref.set({})

        goal_ref = user_ref.collection('user_goals').document()
        
        goal_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "start_date": start_date,
            "end_date": end_date,
            "completed": data.get("completed", False)
        }

        goal_ref.set(goal_data)
        goal_data['id'] = goal_ref.id

        return goal_data
    except Exception as e:
        print(f"Error creating goal: {e}")
        return None


# Get a specific goal
def get_goal_service(uid, goal_id):
    try:
        goal_ref = db.collection('goals').document(uid).collection('user_goals').document(goal_id)
        goal = goal_ref.get()
        if goal.exists:
            goal_data = goal.to_dict()
            goal_data['id'] = goal.id
            return goal_data
        return None
    except Exception as e:
        print(f"Error getting goal: {e}")
        return None

def complete_goal_service(uid, goal_id):
    try:
        print(uid)
        print(goal_id)
        goal_ref = db.collection('goals').document(uid).collection('user_goals').document(goal_id)
        goal_ref.update({"completed": True})
        updated_goal = goal_ref.get().to_dict()
        updated_goal['id'] = goal_id
        return updated_goal
    except Exception as e:
        print(f"Error completing goal: {e}")
        return None
