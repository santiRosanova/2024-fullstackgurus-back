from flask import Blueprint, request, jsonify
from app.services.auth_service import verify_token_service
from app.services.physicalData_service import (
    add_physical_data_service,
    get_physical_data_service
)
from datetime import datetime
import pytz

physicalData_bp = Blueprint('physicalData_bp', __name__)

def validate_body(data):
    weight = data.get('weight')
    body_fat = data.get('body_fat')
    body_muscle = data.get('body_muscle')
    date = data.get('date')

    if not weight or not body_fat or not body_muscle or not date:
        return {"error": "Missing data"}, 400

    if not isinstance(weight, (int, float)) or not isinstance(body_fat, (int, float)) or not isinstance(body_muscle, (int, float)) or not isinstance(date, str):
        return {"error": "Invalid data types"}, 400
    
    if not (25 <= weight <= 300):
        return {"error": "Weight should be between 25 and 300"}, 400
    
    if not (1 <= body_fat <= 150):
        return {"error": "Body fat should be between 1 and 150"}, 400
    
    if not (1 <= body_muscle <= 150):
        return {"error": "Body muscle should be between 1 and 150"}, 400
    
    if (body_fat + body_muscle) > weight:
        return {"error": "Body fat and muscle should not be greater than weight"}, 400

    if len(str(weight).split('.')[-1]) > 2:
        return {"error": "Weight should have at most two decimal places"}, 400
    
    if len(str(body_fat).split('.')[-1]) > 2:
        return {"error": "Body fat should have at most two decimal places"}, 400
    
    if len(str(body_muscle).split('.')[-1]) > 2:
        return {"error": "Body muscle should have at most two decimal places"}, 400

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return {"error": "Invalid date format, should be YYYY-MM-DD"}, 400
    
    local_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    local_time = datetime.now(local_tz)

    naive_dt = datetime.strptime(date, '%Y-%m-%d')
    user_dt = local_tz.localize(naive_dt)

    if user_dt > local_time:
        return {"error": "Date should not be in the future"}, 400

    return None


@physicalData_bp.route('/add', methods=['POST'])
def add_physical_data():
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403

        token = token.split(' ')[1]
        uid = verify_token_service(token)
        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        data = request.get_json()
        weight = data.get('weight')
        body_fat = data.get('body_fat')
        body_muscle = data.get('body_muscle')
        date = data.get('date')

        validation_error = validate_body(data)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]

        if not weight or not body_fat or not body_muscle:
            return jsonify({"error": "Missing parameters"}), 400

        success = add_physical_data_service(uid, body_fat, body_muscle, weight, date)
        if not success:
            return jsonify({"error": "Failed to save physical data"}), 500

        return jsonify({"message": "Physical data added successfully"}), 201

    except Exception as e:
        print(f"Error adding physical data: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@physicalData_bp.route('/get-physical-data', methods=['GET'])
def get_physical_data():
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403

        token = token.split(' ')[1]
        uid = verify_token_service(token)
        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        physical_data = get_physical_data_service(uid)
        if not physical_data:
            return jsonify({"error": "Failed to get physical data"}), 500

        return jsonify(physical_data), 200

    except Exception as e:
        print(f"Error getting physical data: {e}")
        return jsonify({"error": "Something went wrong"}), 500
