"""
assistant.py

This module provides functions for interacting with language models and evaluating responses.
It includes functionalities for searching, generating prompts, evaluating answers, and calculating costs.

Functions:
- elastic_search_text: Searches for text matches in an Elasticsearch index.
- build_prompt: Constructs a prompt for a language model based on a query and search results.
- llm: Sends a prompt to a language model and retrieves the response, token usage, and response time.
- evaluate_relevance: Evaluates the relevance of a generated answer to a given question.
- calculate_openai_cost: Calculates the cost of using OpenAI's API based on model choice and token usage.
- get_answer: Retrieves an answer to a query by performing a search and evaluating the response.

Dependencies:
- `elastic_search_knn`: Function for vector-based search in Elasticsearch.
- `elastic_search_text`: Function for text-based search in Elasticsearch.
- `build_prompt`: Function for constructing prompts for language models.
- `llm`: Function for generating model responses and retrieving usage metrics.
- `evaluate_relevance`: Function for evaluating the relevance of answers.
- `calculate_openai_cost`: Function for computing API costs based on token usage.

Note:
Ensure that the necessary dependencies and API clients are correctly configured and available for the functions to work as intended.
"""

import os
import time
import json
from dotenv import load_dotenv

from openai import OpenAI
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Any


load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/v1/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
INDEX_NAME = os.getenv("INDEX_NAME")


es_client = Elasticsearch(ELASTIC_URL)
ollama_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

model = SentenceTransformer(MODEL_NAME)


def elastic_search_text(query: str, index_name: str = INDEX_NAME) -> List[Dict[str, Any]]:
    """
    Searches for text in the specified Elasticsearch index based on the query.

    Args:
        query (str): The search query string.
        index_name (str): The name of the Elasticsearch index to search. Defaults to the global INDEX_NAME.

    Returns:
        List[Dict[str, Any]]: A list of search results, where each result is a dictionary containing the source data.
    """   
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "answer"],
                        "type": "best_fields",
                    }
                }
            }
        },
    }

    response = es_client.search(index=index_name, body=search_query)
    return [hit["_source"] for hit in response["hits"]["hits"]]

def elastic_search_knn(field: str, vector: List[float], index_name: str = INDEX_NAME) -> List[Dict[str, Any]]:
    """
    Perform a k-nearest neighbor (k-NN) search in the specified Elasticsearch index based on a query vector.

    Args:
        field (str): The field name in the index where the vector is stored.
        vector (List[float]): The query vector for which to find the nearest neighbors.
        index_name (str): The name of the Elasticsearch index to search. Defaults to the global INDEX_NAME.

    Returns:
        List[Dict[str, Any]]: A list of search results, where each result is a dictionary containing the source data.
    """
    knn_query = {
        "field": field,
        "query_vector": vector,
        "k": 5,  # Number of nearest neighbors to retrieve
        "num_candidates": 10000  # Number of candidates to consider for finding the nearest neighbors
    }

    search_query = {
        "knn": knn_query,  # Move knn to top-level of the body
        "_source": ["question", "answer", "id"],
        "size": 5  # Number of results to return
    }

    es_results = es_client.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in es_results["hits"]["hits"]]


def elastic_search_hybrid(
    field: str, 
    query: str, 
    vector: List[float], 
    index_name: str = INDEX_NAME
) -> List[Dict[str, Any]]:
    """
    Perform a hybrid search on Elasticsearch combining k-NN vector search and keyword matching.

    Args:
        field (str): The field to use for the k-NN search.
        query (str): The keyword query string.
        vector (List[float]): The query vector for k-NN search.
        index_name (str): The Elasticsearch index to search. Defaults to the global INDEX_NAME.

    Returns:
        List[Dict[str, Any]]: A list of search result documents from Elasticsearch.
    """
    # k-NN query
    knn_query = {
        "field": field,
        "query_vector": vector,
        "k": 5,
        "num_candidates": 10000,
        "boost": 0.5
    }

    # Keyword search query
    keyword_query = {
        "bool": {
            "must": {
                "multi_match": {
                    "query": query,
                    "fields": ["question^3", "answer"],
                    "type": "best_fields",
                    "boost": 0.5,
                }
            }
        }
    }

    # Hybrid search combining k-NN and keyword search
    search_query = {
        "knn": knn_query,
        "query": keyword_query,
        "size": 5,
        "_source": ["question", "answer","id"]
    }

    es_results = es_client.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in es_results["hits"]["hits"]]




def build_prompt(query: str, search_results: List[Dict[str, str]]) -> str:
    """
    Builds a prompt for a course teaching assistant based on the provided query and search results.

    The prompt is structured to guide the assistant to answer the question using only the provided context.

    Args:
        query (str): The question to be answered by the teaching assistant.
        search_results (List[Dict[str, str]]): A list of search result documents, where each document is a dictionary
                                              containing 'id', 'question', and 'answer' keys.

    Returns:
        str: A formatted prompt combining the question and context from the search results.
    """
    prompt_template = """
                        You're a doctor assistant chat bot. Answer the QUESTION based on the CONTEXT from the FAQ database.
                        Use only the facts from the CONTEXT when answering the QUESTION. Do not make any answers up if you do not
                        have enough context. If you do not know, state 'sorry I don't have an answer to that question'.

                        QUESTION: {question}

                        CONTEXT: 
                        {context}
                      """.strip()

    context = "\n\n".join(
        [
            f"id: {doc['id']}\nquestion: {doc['question']}\nanswer: {doc['answer']}"
            for doc in search_results
        ]
    )
    return prompt_template.format(question=query, context=context).strip()

def llm(prompt: str, model_choice: str) -> Tuple[str, Dict[str, int], float]:
    """
    Sends a prompt to a specified language model and retrieves the response, token usage, and response time.

    Supports models from 'ollama/' and 'openai/' prefixes. Raises a ValueError for unknown model choices.

    Args:
        prompt (str): The input prompt to send to the language model.
        model_choice (str): The identifier for the model to use. Should start with 'ollama/' or 'openai/'.

    Returns:
        Tuple[str, Dict[str, int], float]: A tuple containing:
            - The response content from the model (str).
            - A dictionary with token usage metrics:
                - 'prompt_tokens' (int): Number of tokens in the prompt.
                - 'completion_tokens' (int): Number of tokens in the completion.
                - 'total_tokens' (int): Total number of tokens used.
            - The response time in seconds (float).
    """
    start_time = time.time()
    
    if model_choice.startswith('ollama/'):
        response = ollama_client.chat.completions.create(
            model=model_choice.split('/')[-1],
            messages=[{"role": "user", "content": prompt}]
        )
    elif model_choice.startswith('openai/'):
        response = openai_client.chat.completions.create(
            model=model_choice.split('/')[-1],
            messages=[{"role": "user", "content": prompt}]
        )
        
    elif model_choice.startswith('aws_bedrock/'):
        response = openai_client.chat.completions.create(
            model=model_choice.split('/')[-1],
            messages=[{"role": "user", "content": prompt}]
        )
    else:
        raise ValueError(f"Unknown model choice: {model_choice}")
    
    answer = response.choices[0].message.content
    tokens = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens
    }
    
    end_time = time.time()
    response_time = end_time - start_time
    
    return answer, tokens, response_time


def evaluate_relevance(question: str, answer: str) -> Tuple[str, str, Dict[str, int]]:
    """
    Evaluates the relevance of a generated answer to a given question using a language model.

    The function constructs a prompt for an evaluator model to classify the relevance of the answer as
    "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT". It returns the relevance classification, 
    an explanation, and token usage metrics.

    Args:
        question (str): The question to which the answer was generated.
        answer (str): The generated answer to evaluate.

    Returns:
        Tuple[str, str, Dict[str, int]]:
            - Relevance classification ("NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT").
            - A brief explanation for the evaluation.
            - A dictionary with token usage metrics:
                - 'prompt_tokens' (int): Number of tokens in the prompt.
                - 'completion_tokens' (int): Number of tokens in the completion.
                - 'total_tokens' (int): Total number of tokens used.
    """
    prompt_template = """
    You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
      "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
      "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, 'openai/gpt-4o-mini')
    
    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation'], tokens
    except json.JSONDecodeError:
        return "UNKNOWN", "Failed to parse evaluation", tokens


def calculate_openai_cost(model_choice: str, tokens: Dict[str, int]) -> float:
    """
    Calculates the cost of using OpenAI's API based on the model choice and token usage.

    The cost is calculated differently depending on the model used. This function supports:
    - 'openai/gpt-3.5-turbo'
    - 'openai/gpt-4o'
    - 'openai/gpt-4o-mini'

    Args:
        model_choice (str): The identifier for the OpenAI model used.
        tokens (Dict[str, int]): A dictionary containing token usage metrics:
            - 'prompt_tokens' (int): Number of tokens in the prompt.
            - 'completion_tokens' (int): Number of tokens in the completion.

    Returns:
        float: The calculated cost based on the model choice and token usage.
    """
    if model_choice == 'openai/gpt-3.5-turbo':
        openai_cost = (tokens['prompt_tokens'] * 0.0015 + tokens['completion_tokens'] * 0.002) / 1000
    elif model_choice in ['openai/gpt-4o', 'openai/gpt-4o-mini']:
        openai_cost = (tokens['prompt_tokens'] * 0.03 + tokens['completion_tokens'] * 0.06) / 1000
    else:
        raise ValueError(f"Unknown model choice: {model_choice}")

    return openai_cost

def improve_query(user_query: str, model: str = 'openai/gpt-4o-mini') -> str:
    """
    Enhances a user's query by correcting spelling, fixing grammar, and improving clarity, while maintaining the original 
    context and similar length. Can use either OpenAI API or an Ollama server.

    Args:
        user_query (str): The original query from the user.
        model (str): The name of the LLM model to use for processing the query (default is 'text-davinci-003' for OpenAI).
        service (str): The service to use, either 'openai' or 'ollama' (default is 'openai').

    Returns:
        str: The improved query with better spelling, grammar, and clarity.
    """

    prompt = f"""
    The following is a user's query: "{user_query}"

    Please rewrite the query to improve clarity, fix any spelling or grammar mistakes, and maintain the same context.
    Ensure the rewritten query is not much longer or shorter than the original query.

    Rewritten query:
    """
    improved_query, _, _ = llm(prompt, model)
    
    return improved_query



def get_answer(
    query: str, 
    model_choice: str, 
    search_type: str
) -> Dict[str, Any]:
    """
    Retrieves an answer to a query by performing a search and evaluating the response.

    Depending on the `search_type`, the function either uses vector-based search or text-based search.
    It then generates a prompt for the language model, retrieves the answer, evaluates its relevance,
    and calculates the associated costs and token usage.

    Args:
        query (str): The query for which an answer is sought.
        model_choice (str): The identifier for the model used to generate the answer.
        search_type (str): The type of search to perform ('Vector' or 'Text').

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'answer' (str): The generated answer from the model.
            - 'response_time' (float): The time taken to generate the response.
            - 'relevance' (str): The relevance classification of the answer.
            - 'relevance_explanation' (str): Explanation for the relevance classification.
            - 'model_used' (str): The model used to generate the answer.
            - 'prompt_tokens' (int): Number of tokens in the prompt.
            - 'completion_tokens' (int): Number of tokens in the completion.
            - 'total_tokens' (int): Total number of tokens used.
            - 'eval_prompt_tokens' (int): Number of tokens used in the evaluation prompt.
            - 'eval_completion_tokens' (int): Number of tokens in the evaluation completion.
            - 'eval_total_tokens' (int): Total number of tokens used in the evaluation.
            - 'openai_cost' (float): Cost of the API usage based on the model choice and token usage.
    """
    # first clean the query to improve spelling and grammar and clarity
    query = improve_query(query)
    
    # Search for the best matching knowledge base 
    if search_type == 'Vector':
        vector = model.encode(query)
        search_results = elastic_search_knn('question_vector', vector)
    if search_type == 'Hybrid':
        vector = model.encode(query)
        search_results = elastic_search_hybrid('question_vector', query, vector)
    else:
        search_results = elastic_search_text(query)

    #build a prompt pass context to the LLM and get an answer
    prompt = build_prompt(query, search_results)
    answer, tokens, response_time = llm(prompt, model_choice)
    
    # Evaluate the relevance of the answer
    relevance, explanation, eval_tokens = evaluate_relevance(query, answer)

    # Calculate cost
    openai_cost = calculate_openai_cost(model_choice, tokens)
 
    return {
        'answer': answer,
        'response_time': response_time,
        'relevance': relevance,
        'relevance_explanation': explanation,
        'model_used': model_choice,
        'prompt_tokens': tokens['prompt_tokens'],
        'completion_tokens': tokens['completion_tokens'],
        'total_tokens': tokens['total_tokens'],
        'eval_prompt_tokens': eval_tokens['prompt_tokens'],
        'eval_completion_tokens': eval_tokens['completion_tokens'],
        'eval_total_tokens': eval_tokens['total_tokens'],
        'openai_cost': openai_cost
    }