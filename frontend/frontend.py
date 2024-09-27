import streamlit as st
import time
import uuid
import requests

# Backend URL
BACKEND_URL = "http://backend:8000"  # Update this URL based on your Docker networking setup

def print_log(message: str) -> None:
    """
    Prints a log message to the console.

    Args:
        message (str): The message to print.
    """
    print(message, flush=True)

def get_answer_from_backend(question: str, model: str, search_type: str) -> dict:
    """
    Calls the FastAPI backend to get an answer to a question.

    Args:
        question (str): The question to ask.
        model (str): The model to use for generating the answer.
        search_type (str): The type of search to perform (e.g., 'Text' or 'Vector').

    Returns:
        dict: The response from the backend containing the answer and other relevant data.
    """
    response = requests.post(
        f"{BACKEND_URL}/get_answer",
        json={"question": question, "model": model, "search_type": search_type}
    )
    return response.json()

def save_conversation_to_backend(conversation_id: str, question: str, answer_data: dict) -> None:
    """
    Calls the FastAPI backend to save a conversation.

    Args:
        conversation_id (str): The ID of the conversation.
        question (str): The question asked in the conversation.
        answer_data (dict): The answer data from the backend.
    """
    requests.post(
        f"{BACKEND_URL}/conversation",
        json={
            "conversation_id": conversation_id,
            "question": question,
            "answer_data": answer_data
        }
    )

def save_feedback_to_backend(conversation_id: str, feedback: int) -> None:
    """
    Calls the FastAPI backend to save feedback for a conversation.

    Args:
        conversation_id (str): The ID of the conversation.
        feedback (int): The feedback score (e.g., +1 or -1).
    """
    requests.post(
        f"{BACKEND_URL}/feedback",
        json={"conversation_id": conversation_id, "feedback": feedback}
    )

def get_recent_conversations_from_backend(limit: int = 5, relevance: str = None) -> list:
    """
    Calls the FastAPI backend to get recent conversations.

    Args:
        limit (int, optional): The maximum number of recent conversations to retrieve. Defaults to 5.
        relevance (str, optional): Filter conversations by relevance (e.g., 'RELEVANT', 'PARTLY_RELEVANT', 'NON_RELEVANT').

    Returns:
        list: A list of recent conversations.
    """
    params = {"limit": limit}
    if relevance:
        params["relevance"] = relevance
    response = requests.get(f"{BACKEND_URL}/get-recent-conversations", params=params)
    return response.json()

def get_feedback_stats_from_backend() -> dict:
    """
    Calls the FastAPI backend to get feedback statistics.

    Returns:
        dict: The feedback statistics including thumbs up and thumbs down counts.
    """
    response = requests.get(f"{BACKEND_URL}/feedback-stats")
    return response.json()

def main() -> None:
    """
    Main function to run the Streamlit app.
    """
    print_log("Starting the Assistant application")
    st.title("Assistant")

    # Session state initialization
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
        print_log(f"New conversation started with ID: {st.session_state.conversation_id}")
    if 'count' not in st.session_state:
        st.session_state.count = 0
        print_log("Feedback count initialized to 0")

    # Model selection
    model_choice = st.selectbox(
        "Select a model:",
        ["ollama/phi3", "openai/gpt-3.5-turbo", "openai/gpt-4o", "openai/gpt-4o-mini"]
    )
    print_log(f"User selected model: {model_choice}")

    # Search type selection
    search_type = st.radio(
        "Select search type:",
        ["Text", "Vector"]
    )
    print_log(f"User selected search type: {search_type}")

    # User input
    user_input = st.text_input("Enter your question:")

    if st.button("Ask"):
        print_log(f"User asked: '{user_input}'")
        with st.spinner('Processing...'):
            print_log(f"Getting answer from assistant using {model_choice} model and {search_type} search")
            start_time = time.time()
            answer_data = get_answer_from_backend(user_input, model_choice, search_type)
            end_time = time.time()
            print_log(f"Answer received in {end_time - start_time:.2f} seconds")
            st.success("Completed!")
            st.write(answer_data['answer'])
            
            # Display monitoring information
            st.write(f"Response time: {answer_data['response_time']:.2f} seconds")
            st.write(f"Relevance: {answer_data['relevance']}")
            st.write(f"Model used: {answer_data['model_used']}")
            st.write(f"Total tokens: {answer_data['total_tokens']}")
            if answer_data['openai_cost'] > 0:
                st.write(f"OpenAI cost: ${answer_data['openai_cost']:.4f}")

            # Save conversation to database
            print_log("Saving conversation to database")
            save_conversation_to_backend(st.session_state.conversation_id, user_input, answer_data)
            print_log("Conversation saved successfully")

    # Feedback buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+1"):
            st.session_state.count += 1
            print_log(f"Positive feedback received. New count: {st.session_state.count}")
            save_feedback_to_backend(st.session_state.conversation_id, 1)
            print_log("Positive feedback saved to backend")
    with col2:
        if st.button("-1"):
            st.session_state.count -= 1
            print_log(f"Negative feedback received. New count: {st.session_state.count}")
            save_feedback_to_backend(st.session_state.conversation_id, -1)
            print_log("Negative feedback saved to backend")

    st.write(f"Current count: {st.session_state.count}")

    # Display recent conversations
    st.subheader("Recent Conversations")
    relevance_filter = st.selectbox("Filter by relevance:", ["All", "RELEVANT", "PARTLY_RELEVANT", "NON_RELEVANT"])
    recent_conversations = get_recent_conversations_from_backend(limit=5, relevance=relevance_filter if relevance_filter != "All" else None)
    for conv in recent_conversations:
        st.write(f"Q: {conv['question']}")
        st.write(f"A: {conv['answer']}")
        st.write(f"Relevance: {conv['relevance']}")
        st.write(f"Model: {conv['model_used']}")
        st.write("---")

    # Display feedback stats
    feedback_stats = get_feedback_stats_from_backend()
    st.subheader("Feedback Statistics")
    st.write(f"Thumbs up: {feedback_stats['thumbs_up']}")
    st.write(f"Thumbs down: {feedback_stats['thumbs_down']}")

print_log("Streamlit app loop completed")

if __name__ == "__main__":
    print_log("Assistant application started")
    main()
