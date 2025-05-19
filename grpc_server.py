from concurrent import futures
import grpc
import chat_pb2
import chat_pb2_grpc
import requests
import os

from decision import classify_input
from greetings import generate_greeting
from recomendation import ask_ai_recomendation
from consultation import ask_ai_consultation
from general_Information import ask_ai_general
import bmi_classifier
import age_counter

USER_DETAIL_SERVICE_URL = os.getenv('USER_DETAIL_SERVICE_URL')  # e.g. "user-detail-service.default.svc.cluster.local:8000"

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def ChatStream(self, request, context):
        user_input = request.message

        user_id = None
        for key, value in context.invocation_metadata():
            if key.lower() == "x-user-id":
                user_id = value
                break

        if not user_id:
            yield chat_pb2.ChatReply(response_chunk="X-User-ID is required", type="error")
            return

        if not user_input:
            yield chat_pb2.ChatReply(response_chunk="Message is required", type="error")
            return

        if not user_id:
            yield chat_pb2.ChatReply(response_chunk="X-User-ID is required", type="error")
            return

        # Fetch user details from user detail service
        try:
            resp = requests.get(
                f"http://{USER_DETAIL_SERVICE_URL}/api/user",
                params={"user_id": user_id},
                timeout=3
            )
            if resp.status_code != 200:
                yield chat_pb2.ChatReply(response_chunk="Failed to fetch user details", type="error")
                return

            user_details_response = resp.json()
            user_data = user_details_response.get('data')
            if not user_data:
                yield chat_pb2.ChatReply(response_chunk="User details are missing", type="error")
                return

            required_fields = ['name', 'weight', 'height', 'age', 'birthday', 'gender']
            missing_fields = [field for field in required_fields if field not in user_data]
            if missing_fields:
                yield chat_pb2.ChatReply(response_chunk=f"Missing fields: {', '.join(missing_fields)}", type="error")
                return

            age = age_counter(user_data['birthday'])
            bmi_category = bmi_classifier(user_data['weight'], user_data['height'], age)

            user_name = user_data.get('name')
            weight = user_data.get('weight')
            height = user_data.get('height')
            gender = user_data.get('gender')

        except Exception as e:
            yield chat_pb2.ChatReply(response_chunk=f"Exception: {str(e)}", type="error")
            return

        classify_result = classify_input(user_input)
        # Streaming generator
        if classify_result == "greetings":
            generator = generate_greeting(user_input, user_name, stream=True)
        elif classify_result in ["recommendation", "rekomendasi"]:
            generator = ask_ai_recomendation(
                user_name, bmi_category, weight, height, age, gender, user_input, stream=True)
        elif classify_result in ["consultation", "konsultasi"]:
            generator = ask_ai_consultation(
                user_name, bmi_category, weight, height, age, gender, user_input, stream=True)
        elif classify_result == "general":
            generator = ask_ai_general(user_input, stream=True)
        else:
            yield chat_pb2.ChatReply(response_chunk="Maaf, saya tidak mengerti pertanyaan Anda.", type=classify_result)
            return

        for chunk in generator:
            yield chat_pb2.ChatReply(response_chunk=chunk, type=classify_result)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server running at 0.0.0.0:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()