from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from retriever import general_retriever
from dotenv import load_dotenv
import os

load_dotenv()

model = OllamaLLM(
    model="llama3.2:3b",
    base_url=os.getenv("OLLAMA_URL")
)

template = """
Anda adalah seorang ahli kesehatan yang bertugas untuk memberikan informasi tentang kesehatan dan gizi berdasarkan informasi yang tersedia pada database.

Pertanyaan: "{question}"
informasi: "{information}"

sesuaikan jawaban berdasarkan pertanyaan dari user
cukup berikan jawaban yang singkat dan padat
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

def ask_ai_general(question, stream=False):
    information = general_retriever.invoke(question)
    prompt_value = prompt.format_messages(
        question=question,
        information=information
    )

    if stream:
        for chunk in model.stream(prompt_value):
            yield chunk
    else:
        response = ""
        for chunk in model.stream(prompt_value):
            response += chunk
        return response

# while True:
#     question = input("Masukkan pertanyaan: ")
#     if question == "q":
#         break
#     ask_ai_general(question)