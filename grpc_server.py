from concurrent import futures
import grpc
import chat_pb2
import chat_pb2_grpc

from decision import classify_input
from greetings import generate_greeting
from recomendation import ask_ai_recomendation
from consultation import ask_ai_consultation
from general_Information import ask_ai_general

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def ChatStream(self, request, context):
        # Choose which answer function to use
        classify_result = classify_input(request.message)
        # Streaming generator
        if classify_result == "greetings":
            generator = generate_greeting(request.message, request.name, stream=True)
        elif classify_result in ["recommendation", "rekomendasi"]:
            generator = ask_ai_recomendation(
                request.name, request.bmi_category, request.weight, request.height,
                request.age, request.gender, request.message, stream=True)
        elif classify_result in ["consultation", "konsultasi"]:
            generator = ask_ai_consultation(
                request.name, request.bmi_category, request.weight, request.height,
                request.age, request.gender, request.message, stream=True)
        elif classify_result == "general":
            generator = ask_ai_general(request.message, stream=True)
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