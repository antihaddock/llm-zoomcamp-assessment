"""
backend.py

This module contains the backend logic for the Course Assistant application.
It includes functions to handle user interactions, process questions, manage feedback, and fetch data.

Functions:
- start_conversation: Initializes a new conversation with a unique ID.
- initialize_session_state: Sets up initial session state variables for conversation ID and feedback count.
- handle_ask_question: Processes user input to retrieve an answer from the assistant and saves the conversation.
- handle_feedback: Saves user feedback to the database and updates the feedback count.
- fetch_recent_conversations: Retrieves recent conversations with an optional relevance filter.
- fetch_feedback_stats: Retrieves feedback statistics.

Dependencies:
- `uuid`: For generating unique conversation IDs.
- `time`: For measuring response times.
- `assistant.get_answer`: Function to get answers from the assistant.
- `db.save_conversation`: Function to save conversations to the database.
- `db.save_feedback`: Function to save feedback to the database.
- `db.get_recent_conversations`: Function to get recent conversations from the database.
- `db.get_feedback_stats`: Function to get feedback statistics from the database.
"""


import uuid
import time
from assistant import get_answer
from db import save_conversation, save_feedback, get_recent_conversations, get_feedback_stats

def start_conversation():
    """
    Initializes a new conversation with a unique ID.
    """
    return str(uuid.uuid4())

def initialize_session_state():
    """
    Initializes session state variables for conversation ID and feedback count.
    """
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = start_conversation()
    if 'count' not in st.session_state:
        st.session_state.count = 0

def handle_ask_question(user_input: str, course: str, model_choice: str, search_type: str):
    """
    Processes the user input to get an answer from the assistant and saves the conversation.

    Args:
        user_input (str): The question entered by the user.
        course (str): The selected course.
        model_choice (str): The selected model.
        search_type (str): The type of search to perform.

    Returns:
        Dict: Contains answer data and other relevant information.
    """
    start_time = time.time()
    answer_data = get_answer(user_input, course, model_choice, search_type)
    end_time = time.time()

    answer_data['response_time'] = end_time - start_time

    # Save conversation to database
    save_conversation(st.session_state.conversation_id, user_input, answer_data, course)

    return answer_data

def handle_feedback(feedback: int):
    """
    Saves the user feedback to the database and updates the feedback count.

    Args:
        feedback (int): The feedback value (+1 or -1).
    """
    st.session_state.count += feedback
    save_feedback(st.session_state.conversation_id, feedback)
    
def fetch_recent_conversations(relevance_filter: str):
    """
    Retrieves recent conversations with an optional relevance filter.

    Args:
        relevance_filter (str): Filter for relevance of conversations.

    Returns:
        List[Dict]: A list of recent conversations.
    """
    return get_recent_conversations(limit=5, relevance=relevance_filter if relevance_filter != "All" else None)

def fetch_feedback_stats():
    """
    Retrieves feedback statistics.

    Returns:
        Dict: Contains thumbs up and thumbs down counts.
    """
    return get_feedback_stats()
