from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

embeddings = OllamaEmbeddings(model="nomic-embed-text",
                              base_url=os.getenv("OLLAMA_URL"))

food_db_location = "./chroma_langchain_db"
general_db_location = "./general_data_db"

food_vector_store = Chroma(
    collection_name="food_data",
    persist_directory=food_db_location,
    embedding_function=embeddings
)

general_vector_store = Chroma(
    collection_name="general_data",
    persist_directory=general_db_location,
    embedding_function=embeddings
)

food_retriever = food_vector_store.as_retriever(
    search_type="mmr",
        search_kwargs={'k': 6, 'lambda_mult': 0.25}
)

general_retriever = general_vector_store.as_retriever(
    search_kwargs = {"k" : 5}
)


# print("\n=== Mencoba Retriever ===")
# query = "Tumis bandeng, masakan"
# results = food_retriever.invoke(query)

# print(f"\nHasil pencarian untuk query: '{query}'")
# for doc in results:
#     print(f"\nKonten: {doc.page_content}")
#     print(f"Metadata: {doc.metadata}")
