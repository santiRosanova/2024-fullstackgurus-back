from flask import Blueprint, request, jsonify
from app.services.user_service import save_user_info_service, verify_token_service, get_user_info_service, update_user_info_service
from datetime import datetime
import pytz

user_bp = Blueprint('user_bp', __name__)

def validate_body(data):
    if 'email' not in data or 'name' not in data or 'sex' not in data or 'weight' not in data or 'height' not in data or 'birthday' not in data:
        return {"error": "Missing data"}, 400
    
    if not isinstance(data.get('email'), str) or not isinstance(data.get('name'), str) or not isinstance(data.get('weight'), (int, float)) or not isinstance(data.get('height'), (int, float)) or not isinstance(data.get('birthday'), str):
        return {"error": "Invalid data types"}, 400
    
    email = data.get('email')
    if email:
        import re
        email_regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'
        if not re.match(email_regex, email):
            return {"error": "Invalid email format"}, 400
    
    if data.get('sex') not in ['male', 'female']:
        return {"error": "Invalid sex, should be male or female"}, 400
    
    if not (25 <= data.get('weight') <= 300):
        return {"error": "Weight should be between 25 and 300"}, 400
    
    if not (120 <= data.get('height') <= 240):
        return {"error": "Height should be between 120 and 240"}, 400
    
    if len(str(data.get('weight')).split('.')[-1]) > 2:
        return {"error": "Weight should have at most two decimal places"}, 400
    
    try:
        datetime.strptime(data.get('birthday'), '%Y-%m-%d')
    except ValueError:
        return {"error": "Invalid date format, should be YYYY-MM-DD"}, 400
    
    local_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    local_time = datetime.now(local_tz)

    naive_dt = datetime.strptime(data.get('birthday'), '%Y-%m-%d')
    user_dt = local_tz.localize(naive_dt)

    if user_dt > local_time:
        return {"error": "Date should not be in the future"}, 400
    
    return None

@user_bp.route('/save-user-info', methods=['POST'])
def save_user_info():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        data = request.get_json()

        validation_error = validate_body(data)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]

        save_user_info_service(uid, data)

        return jsonify({'message': 'User data saved successfully'}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Something went wrong'}), 500
    

@user_bp.route('/get-user-info', methods=['GET'])
def get_user_info():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        user_info = get_user_info_service(uid)
        if user_info:
            return jsonify(user_info), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        print(e)
        return jsonify({'error': 'Something went wrong'}), 500


@user_bp.route('/update-user-info', methods=['PUT'])
def update_user_info():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        uid = verify_token_service(token)
        if uid is None:
            return jsonify({'error': 'Invalid token'}), 401

        data = request.get_json()
        update_user_info_service(uid, data)

        return jsonify({'message': 'Data updated successfully'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Something went wrong'}), 500