"""
backend_flask.py

This module provides the backend logic for the Course Assistant application using Flask. 
It handles user interactions via API endpoints, processes questions, manages feedback, 
and retrieves data from the database.

API Endpoints:
- POST /ask: Processes user input to get an answer from the assistant and saves the conversation.
- POST /feedback: Saves user feedback to the database and updates the feedback count.
- GET /recent-conversations: Retrieves recent conversations with an optional relevance filter.
- GET /feedback-stats: Retrieves feedback statistics.

Functions:
- start_conversation: Initializes a new conversation with a unique ID.
- initialize_session_state: Sets up initial session state variables for conversation ID and feedback count.
- handle_ask_question: Processes user input to retrieve an answer from the assistant and saves the conversation.
- handle_feedback: Saves user feedback to the database and updates the feedback count.
- fetch_recent_conversations: Retrieves recent conversations with an optional relevance filter.
- fetch_feedback_stats: Retrieves feedback statistics.

Dependencies:
- Flask: For creating the web server and handling API requests.
- uuid: For generating unique conversation IDs.
- time: For measuring response times.
- assistant.get_answer: Function to get answers from the assistant.
- db.save_conversation: Function to save conversations to the database.
- db.save_feedback: Function to save feedback to the database.
- db.get_recent_conversations: Function to get recent conversations from the database.
- db.get_feedback_stats: Function to get feedback statistics from the database.
"""


from flask import Flask, request, jsonify
import uuid
import time
from assistant import get_answer
from db import save_conversation, save_feedback, get_recent_conversations, get_feedback_stats

app = Flask(__name__)

def start_conversation() -> str:
    """
    Initializes a new conversation with a unique ID.

    Returns:
        str: The unique conversation ID.
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

@app.route('/ask', methods=['POST'])
def handle_ask_question():
    """
    Processes the user input to get an answer from the assistant and saves the conversation.

    Returns:
        jsonify: Contains answer data and other relevant information.
    """
    data = request.json
    user_input = data.get('question')
    course = data.get('course')
    model_choice = data.get('model_choice')
    search_type = data.get('search_type')

    if not all([user_input, course, model_choice, search_type]):
        return jsonify({"error": "Missing required parameters"}), 400

    start_time = time.time()
    answer_data = get_answer(user_input, course, model_choice, search_type)
    end_time = time.time()

    answer_data['response_time'] = end_time - start_time

    # Save conversation to database
    save_conversation(st.session_state.conversation_id, user_input, answer_data, course)

    return jsonify(answer_data)

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """
    Saves the user feedback to the database and updates the feedback count.

    Returns:
        jsonify: Confirmation message of feedback saving.
    """
    data = request.json
    feedback = data.get('feedback')
    
    if feedback is None:
        return jsonify({"error": "Missing feedback parameter"}), 400

    st.session_state.count += feedback
    save_feedback(st.session_state.conversation_id, feedback)
    
    return jsonify({"message": "Feedback saved"})

@app.route('/recent-conversations', methods=['GET'])
def fetch_recent_conversations():
    """
    Retrieves recent conversations with an optional relevance filter.

    Returns:
        jsonify: A list of recent conversations.
    """
    relevance_filter = request.args.get('relevance', 'All')
    recent_convs = get_recent_conversations(limit=5, relevance=relevance_filter if relevance_filter != "All" else None)
    return jsonify(recent_convs)

@app.route('/feedback-stats', methods=['GET'])
def fetch_feedback_stats():
    """
    Retrieves feedback statistics.

    Returns:
        jsonify: Contains thumbs up and thumbs down counts.
    """
    stats = get_feedback_stats()
    return jsonify(stats)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
