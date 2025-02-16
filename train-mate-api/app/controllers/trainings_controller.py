from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.auth_service import verify_token_service
from app.services.trainings_service import get_popular_exercises, save_user_training, get_user_trainings, get_training_by_id
from app.services.metadata_service import get_last_modified_timestamp, set_last_modified_timestamp

trainings_bp = Blueprint('trainings_bp', __name__)

@trainings_bp.route('/save-training', methods=['POST'])
def save_training():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        data = request.get_json()

        exercises = data.get('exercises')
        calories_per_hour_sum = 0
        exercises_ids = []
        for exercise in exercises:
            calories_per_hour_sum += exercise.get('calories_per_hour')
            exercises_ids.append(exercise.get('id'))
        calories_per_hour_mean = round(calories_per_hour_sum / len(exercises))

        saved_training = save_user_training(uid, data, exercises_ids, calories_per_hour_mean)

        return jsonify({
            'message': 'Training saved successfully',
            'training': saved_training
        }), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500

@trainings_bp.route('/get-trainings', methods=['GET'])
def get_trainings():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        trainings = get_user_trainings(uid)
        return jsonify({'trainings': trainings}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500

@trainings_bp.route('/get-training/<training_id>', methods=['GET'])
def get_training_by_id(training_id):
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        training = get_training_by_id(uid, training_id)
        if not training:
            return jsonify({'error': 'Training not found'}), 404

        return jsonify(training), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500
    

@trainings_bp.route('/popular-exercises', methods=['GET'])
def get_popular_exercises_view():
    try:
        
        popular_exercises = get_popular_exercises()

        return jsonify({'popular_exercises': popular_exercises}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500
    
@trainings_bp.route('/last-modified', methods=['GET'])
def get_last_modified():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401
        
        last_modified = get_last_modified_timestamp(uid, 'trainings')

        if not last_modified:
            return jsonify({'last_modified_timestamp': None}), 200

        if isinstance(last_modified, datetime):
            timestamp_ms = int(last_modified.timestamp() * 1000)

        return jsonify({'last_modified_timestamp': timestamp_ms}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500
    
@trainings_bp.route('/update-last-modified', methods=['POST'])
def update_last_modified():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401
        
        time = set_last_modified_timestamp(uid, 'trainings')
        if not time:
            return jsonify({'error': 'Error updating last modified timestamp'}), 500
        if isinstance(time, datetime):
            timestamp_ms = int(time.timestamp() * 1000)

        return jsonify({'message': 'Last modified timestamp updated successfully', 'last_modified_timestamp': timestamp_ms}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Something went wrong'}), 500