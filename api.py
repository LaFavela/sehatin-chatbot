from flask import Flask, request, jsonify
from flask_cors import CORS
from decision import classify_input
from greetings import generate_greeting
from recomendation import ask_ai_recomendation
from consultation import ask_ai_consultation
from general_Information import ask_ai_general
import bmi_classifier
import age_counter
import os
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

USER_DETAIL_SERVICE_URL = os.getenv('USER_DETAIL_SERVICE_URL')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get('message')
        user_id = request.headers.get('X-User-ID')

        if not user_input:
            return jsonify({'error': 'Message is required'}), 400

        if not user_input:
            return jsonify({'status': false, 'message': 'Message is required'}), 400

        if not user_id:
            return jsonify({'status': false, 'message': 'X-User-ID header is required'}), 400

        user_detail_response = requests.get(f"http://{USER_DETAIL_SERVICE_URL}/api/user?user_id={user_id}")
        if user_detail_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch user details'}), 500

        if not user_details_response.get('data'):
            return jsonify({'error': 'User details are missing'}), 400

        user_data = user_details_response['data']

        required_fields = ['name', 'bmi_category', 'weight', 'height', 'age', 'gender']
        missing_fields = [field for field in required_fields if field not in user_data]

        if missing_fields:
            return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400


        age = age_counter(user_data['birthday'])
        bmi_category = bmi_classifier(user_data['weight'], user_data['height'], age)

        user_name = user_data.get('name')
        weight = user_data.get('weight')
        height = user_data.get('height')
        gender = user_data.get('gender')




        classify_result = classify_input(user_input)
        
        if classify_result == "greetings":
            response = generate_greeting(user_input, user_name)
        elif classify_result in ["recommendation", "rekomendasi"]:
            response = ask_ai_recomendation(user_name, bmi_category, weight, height, age, gender, user_input)
        elif classify_result in ["consultation", "konsultasi"]:
            response = ask_ai_consultation(user_name, bmi_category, weight, height, age, gender, user_input)
        elif classify_result == "general":
            response = ask_ai_general(user_input)
        else:
            response = "Maaf, saya tidak mengerti pertanyaan Anda."

        return jsonify({
            'status': 'success',
            'response': response,
            'type': classify_result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 