from flask import Blueprint, request, jsonify
from app.services.auth_service import verify_token_service
from app.services.exercise_service import (
    save_exercise as save_exercise_service,
    get_exercises as get_exercises_service,
    delete_exercise as delete_exercise_service,
    update_exercise as update_exercise_service,
    get_all_exercises as get_all_exercises_service,
    get_exercise_by_category_id as get_exercise_by_category_id_service,
)
from app.services.trainings_service import recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise
from app.assets.muscular_groups_list import get_muscles

exercise_bp = Blueprint('exercise_bp', __name__)

def validate_body(data):
    name = data.get('name')
    calories_per_hour = data.get('calories_per_hour')
    public = data.get('public')
    category_id = data.get('category_id')
    training_muscle = data.get('training_muscle')
    image_url = data.get('image_url')

    if not name or calories_per_hour is None or public is None or category_id is None or training_muscle is None or image_url is None:
        return {"error": "Missing data"}, 400

    if not isinstance(name, str) or not isinstance(calories_per_hour, (int, float)) or not isinstance(public, (str, bool)) or not isinstance(category_id, str) or not isinstance(training_muscle, str) or not isinstance(image_url, str):
        return {"error": "Invalid data types"}, 400

    if calories_per_hour <= 60 or calories_per_hour >= 4000:
        return {"error": "calories_per_hour should be between 60 and 4000"}, 400
    
    muscular_groups = get_muscles()
    if training_muscle not in muscular_groups:
        return {"error": "Invalid training_muscle"}, 400
    
    if public:
        return {"error": "Invalid data for 'public', it should be False"}, 400

    return None

# Save Exercise
@exercise_bp.route('/save-exercise', methods=['POST'])
def save_exercise():
    try:
        data = request.get_json()
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403
        
        token = token.split(' ')[1]
        uid = verify_token_service(token)

        validation_error = validate_body(data)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]

        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        name = data['name']
        calories_per_hour = data['calories_per_hour']
        public = data['public']
        category_id = data['category_id']
        image_url = data['image_url']
        training_muscle = data['training_muscle']

        if isinstance(public, str):
            public = True if public.lower() == 'true' else False

        success, exercise = save_exercise_service(uid, name, calories_per_hour, public, category_id, training_muscle, image_url)
        if not success:
            return jsonify({"error": "Failed to save exercise"}), 500

        return jsonify({"message": "Exercise saved successfully", "exercise": exercise}), 201

    except Exception as e:
        print(f"Error saving exercise: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# Get Exercises
@exercise_bp.route('/get-exercises', methods=['GET'])
def get_exercises():
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403
        
        token = token.split(' ')[1]
        uid = verify_token_service(token)

        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        show_public = request.args.get('public', 'false').lower() == 'true'
        exercises = get_exercises_service(uid, show_public)
        return jsonify({"exercises": exercises}), 200

    except Exception as e:
        print(f"Error fetching exercises: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# Delete Exercise
@exercise_bp.route('/delete-exercise/<exercise_id>', methods=['DELETE'])
def delete_exercise(exercise_id):
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403
        
        token = token.split(' ')[1]
        uid = verify_token_service(token)

        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        success = delete_exercise_service(uid, exercise_id)
        if not success:
            return jsonify({"error": "Failed to delete exercise"}), 404

        return jsonify({"message": "Exercise deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting exercise: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# Edit Exercise
@exercise_bp.route('/edit-exercise/<exercise_id>', methods=['PUT'])
def edit_exercise(exercise_id):
    try:
        data = request.get_json()
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403
        
        token = token.split(' ')[1]
        uid = verify_token_service(token)

        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        # En vez de usar una validación rígida, validamos si se envió cada campo
        update_data = {}
        old_image_url = None
        
        if 'name' in data:
            name = data['name']
            if isinstance(name, str):
                update_data['name'] = name
            else:
                return jsonify({"error": "Invalid data type for 'name'"}), 400
        
        if 'calories_per_hour' in data:
            calories_per_hour = data['calories_per_hour']
            if isinstance(calories_per_hour, (int, float)) and 60 < calories_per_hour < 4000:
                update_data['calories_per_hour'] = calories_per_hour
            else:
                return jsonify({"error": "Invalid data type or value for 'calories_per_hour'"}), 400

        if 'training_muscle' in data:
            training_muscle = data['training_muscle']
            if isinstance(training_muscle, str):
                update_data['training_muscle'] = training_muscle
            elif training_muscle not in get_muscles():
                return jsonify({"error": "Invalid value for 'training_muscle'"}), 400
            else:
                return jsonify({"error": "Invalid data type for 'training_muscle'"}), 400
        
        if 'image_url' in data:
            image_url = data['image_url']
            if isinstance(image_url, str):
                update_data['image_url'] = image_url
            else:
                return jsonify({"error": "Invalid data type for 'image_url'"}), 400

        if 'public' in data:
            public = data['public']
            if isinstance(public, str):
                public = True if public.lower() == 'true' else False
            if isinstance(public, bool):
                update_data['public'] = public
            elif public:
                return jsonify({"error": "Invalid data for 'public', it should be False"}), 400
            else:
                return jsonify({"error": "Invalid data type for 'public'"}), 400
        
        if 'old_image' in data and data['old_image'] != '':
            old_image_url = data['old_image']

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        success = update_exercise_service(uid, exercise_id, update_data, old_image_url)

        # Si hubo un cambio de calories_per_hour, se debe recalcular el promedio de calories_per_hour en los trainings
        if 'calories_per_hour' in update_data and success:
            recalculate_calories_per_hour_mean_of_trainings_by_modified_excercise(uid, exercise_id)

        if not success:
            return jsonify({"error": "Failed to update exercise"}), 404

        return jsonify({"message": "Exercise updated successfully"}), 200

    except Exception as e:
        print(f"Error updating exercise: {e}")
        return jsonify({"error": "Something went wrong"}), 500


# Get All Exercises. Public endpoint
@exercise_bp.route('/get-all-exercises', methods=['GET'])
def get_all_exercises():
    try:
        exercises = get_all_exercises_service()
        return jsonify({"exercises": exercises}), 200

    except Exception as e:
        print(f"Error fetching exercises: {e}")
        return jsonify({"error": "Something went wrong"}), 500

# Get Exercises by Category ID
@exercise_bp.route('/get-exercises-by-category/<category_id>', methods=['GET'])
def get_exercises_by_category_id(category_id):
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403
        
        token = token.split(' ')[1]
        uid = verify_token_service(token)

        if not uid:
            return jsonify({"error": "Invalid token"}), 403
        
        exercises = get_exercise_by_category_id_service(category_id, uid)
        return jsonify({"exercises": exercises}), 200

    except Exception as e:
        print(f"Error fetching exercises: {e}")
        return jsonify({"error": "Something went wrong"}), 500
