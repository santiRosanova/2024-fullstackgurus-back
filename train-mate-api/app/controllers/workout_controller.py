from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.user_service import verify_token_service
from app.services.workout_service import save_user_workout, get_user_workouts, get_user_calories_from_workouts
from app.services.exercise_service import get_exercise_by_id_service
from app.services.trainings_service import get_training_by_id
from app.services.workout_service import delete_user_workout
from app.services.metadata_service import get_last_modified_timestamp, set_last_modified_timestamp

workout_bp = Blueprint('workout_bp', __name__)

@workout_bp.route('/save-workout', methods=['POST'])
def record_workout():
    try:
        # Extract and validate the token
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        # Get request data
        data = request.get_json()

        # Validate if training_id is provided
        training_id = data.get('training_id')
        if not training_id:
            return jsonify({'error': 'training_id is required'}), 400
        
        if not isinstance(training_id, str) or not isinstance(data.get('duration'), int) or not isinstance(data.get('date'), str) or not isinstance(data.get('coach'), str):
            return jsonify({'error': 'Invalid data provided'}), 400
        
        if not (1 <= data["duration"] <= 1000):
            return jsonify({"error":"Invalid duration provided"}), 400
        
        try:
            datetime.strptime(data.get('date'), '%Y-%m-%d')
        except ValueError:
            return {"error": "Invalid date format, should be YYYY-MM-DD"}, 400

        calories_per_hour_mean = get_training_by_id(uid, training_id).get('calories_per_hour_mean')

        # Calculate calories burned based on duration and calories_per_hour
        duration = data.get('duration')

        # Calculate calories burned
        calories_burned = round((calories_per_hour_mean / 60) * duration)

        # Save the workout using the service and pass the necessary details
        saved_workout = save_user_workout(uid, data, calories_burned)

        return jsonify({
            'message': 'Workout saved successfully',
            'workout': saved_workout  # Include the saved workout in the response
        }), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500
    

@workout_bp.route('/workouts', methods=['GET'])
def get_workouts():
    try:
        # Extract and validate the token
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Token inválido'}), 401

        # Obtener las fechas de los parámetros de la URL
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        # Get all workouts for the user with optional date filtering
        workouts = get_user_workouts(uid, start_date, end_date)
        for workout in workouts:
            exercises = []
            training_data = get_training_by_id(uid, workout['training_id'])
            workout['training'] = training_data
            for exercise_id in training_data['exercises']:
                exercise_data = get_exercise_by_id_service(exercise_id)
                exercise_data['id'] = exercise_id
                exercises.append(exercise_data)
            workout['training']['exercises'] = exercises


        # Return the list of workouts
        return jsonify({
            'workouts': workouts
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Algo salió mal'}), 500


# Va a quedar deprecado, ya el endpoint de workouts tiene toda la data que necesito
@workout_bp.route('/get-workouts-calories', methods=['GET'])
def get_workouts_calories():
    try:
        # Extract and validate the token
        token = request.headers.get('Authorization').split(' ')[1]

        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Token inválido'}), 401
        
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')


        # Get all workouts for the user
        workouts_calories, workouts_dates, workouts_training_id = get_user_calories_from_workouts(uid, start_date, end_date)

        # Combinar las fechas y calorías en una lista de objetos
        workouts_calories_and_dates = [
            {"date": date, "total_calories": calories, "training_id": training_id}
            for date, calories, training_id in zip(workouts_dates, workouts_calories, workouts_training_id)
        ]

        # Return the combined list of workouts
        return jsonify({
            'workouts_calories_and_dates': workouts_calories_and_dates
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Algo salió mal'}), 500
    

@workout_bp.route('/cancel-workout/<workout_id>', methods=['DELETE'])
def cancel_workout(workout_id):
    try:
        # Extract and validate the token
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        # Attempt to delete the workout
        response, status_code = delete_user_workout(uid, workout_id)
        return jsonify(response), status_code

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500
    
@workout_bp.route('/last-modified', methods=['GET'])
def get_last_modified():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401
        
        last_modified = get_last_modified_timestamp(uid, 'workouts')

        if not last_modified:
            return jsonify({'last_modified_timestamp': None}), 200

        if isinstance(last_modified, datetime):
            timestamp_ms = int(last_modified.timestamp() * 1000)

        return jsonify({'last_modified_timestamp': timestamp_ms}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500
    
@workout_bp.route('/update-last-modified', methods=['POST'])
def update_last_modified():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401
        
        time = set_last_modified_timestamp(uid, 'workouts')
        if not time:
            return jsonify({'error': 'Error updating last modified timestamp'}), 500
        if isinstance(time, datetime):
            timestamp_ms = int(time.timestamp() * 1000)

        return jsonify({'message': 'Last modified timestamp updated successfully', 'last_modified_timestamp': timestamp_ms}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500