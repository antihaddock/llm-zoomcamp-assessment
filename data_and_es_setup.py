"""
data_and_es_setup.py

This module sets up an Elasticsearch index for storing question-answer pairs and their vector representations.
It fetches documents from an external source, generates vector embeddings using a pre-trained model, and 
indexes the documents into Elasticsearch for future retrieval and similarity-based search. It also initializes 
a local database.

The following steps are carried out by this script:
1. Fetch documents from a specified URL.
2. Load a sentence transformer model for embedding generation.
3. Set up an Elasticsearch index with mappings for text and vector fields.
4. Generate vector embeddings for each document's question and the combined question-answer.
5. Index the documents and embeddings into Elasticsearch.
6. Initialize the local database after indexing.

Dependencies:
    - os
    - requests
    - sentence_transformers
    - elasticsearch
    - tqdm
    - dotenv
    - db (custom module for database initialization)

Environment Variables:
    - ELASTIC_URL: The Elasticsearch URL.
    - MODEL_NAME: The name of the sentence transformer model to be used.
    - INDEX_NAME: The name of the Elasticsearch index.
"""


import os
import requests
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from tqdm.auto import tqdm
from dotenv import load_dotenv

from db import init_db

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
INDEX_NAME = os.getenv("INDEX_NAME")

DOCS_URL = "https://raw.githubusercontent.com/Kent0n-Li/ChatDoctor/main/chatdoctor5k.json"


def fetch_documents():
    """
    Fetches the documents from the specified URL.

    This function makes a GET request to the URL defined by DOCS_URL to fetch a list of
    question-answer documents in JSON format.

    Returns:
        list: A list of dictionaries, each containing 'id', 'question', and 'answer'.
    """
    
    print("Fetching documents...")
    docs_response = requests.get(DOCS_URL)
    documents = docs_response.json()
    print(f"Fetched {len(documents)} documents")
    return documents


def load_model():
    print(f"Loading model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def setup_elasticsearch():
    """
    Set up an Elasticsearch index for storing question-answer pairs along with vector representations of:
    1. The question alone (question_vector).
    2. The concatenation of question and answer (question_answer_vector).

    The function initializes an Elasticsearch index with specific settings and mappings. It supports
    storing question and answer text fields, along with two vector representations to be used for 
    similarity search (e.g., cosine similarity):
    - One vector for the question.
    - Another vector for the concatenation of the question and answer.

    The function deletes the existing index (if any) with the same name before creating the new one.

    Returns:
        Elasticsearch: The client instance connected to the Elasticsearch cluster.

    Raises:
        ElasticsearchException: If there is an error creating or interacting with the index.
    """
    print("Setting up Elasticsearch...")
    es_client = Elasticsearch(ELASTIC_URL)

    index_settings = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "question_vector": {
                    "type": "dense_vector",
                    "dims": 384,  # Assuming you're using a vector of size 384
                    "index": True,
                    "similarity": "cosine",
                },
                "question_answer_vector": {
                    "type": "dense_vector",
                    "dims": 384,  # Assuming the same vector size for concatenated embeddings
                    "index": True,
                    "similarity": "cosine",
                },
            }
        },
    }

    # Delete the existing index if it exists
    es_client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
    
    # Create a new index with the provided settings
    es_client.indices.create(index=INDEX_NAME, body=index_settings)
    
    print(f"Elasticsearch index '{INDEX_NAME}' created")
    return es_client



def index_documents(es_client, documents, model):
    """
    Index a list of documents into the Elasticsearch database.

    Each document should contain an 'id', 'question', and 'answer' field.
    The function computes two vector embeddings for each document using the provided model:
    1. One for the question alone.
    2. One for the concatenation of question and answer.

    Args:
        es_client (Elasticsearch): The Elasticsearch client instance.
        documents (list of dict): The list of documents to be indexed, each containing 'id', 'question', and 'answer'.
        model (SentenceTransformer): The model to use for generating vector embeddings.

    Returns:
        None
    """
    print("Indexing documents...")
    for doc in tqdm(documents):
        question = doc["question"]
        answer = doc["answer"]

        # Generate vector embeddings
        doc["question_vector"] = model.encode(question).tolist()  # Embedding for the question alone
        doc["question_answer_vector"] = model.encode(question + " " + answer).tolist()  # Embedding for both question and answer

        # Index the document into Elasticsearch
        es_client.index(index=INDEX_NAME, document=doc)

    print(f"Indexed {len(documents)} documents")


def main():
    """
        Main function to coordinate the document indexing process.

        This function orchestrates the following:
        1. Fetches the documents from an external source.
        2. Loads the pre-trained model for embedding generation.
        3. Sets up the Elasticsearch index.
        4. Indexes the fetched documents into Elasticsearch.
        5. Initializes the local database.

        Returns:
            None
    """
    
    print("Starting the indexing process...")

    documents = fetch_documents()
    model = load_model()
    es_client = setup_elasticsearch()
    index_documents(es_client, documents, model)


    print("Initializing database...")
    init_db()

    print("Indexing process completed successfully!")


if __name__ == "__main__":
    main()
