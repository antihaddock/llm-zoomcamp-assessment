import streamlit as st
import uuid
import requests

# Helper function for sending requests to the backend
def send_request(endpoint, data=None, method="GET"):
    url = f"http://backend:8000{endpoint}"  # Update this if your backend runs on a different host/port
    if method == "POST":
        response = requests.post(url, json=data)
    else:
        response = requests.get(url, params=data)
    return response.json()

def ask_question():
    """Function to handle the question asking process."""
    user_input = st.session_state.user_input  # Get user input from session state
    if user_input:  # Ensure there's input to process
        query = {
            "user_input": user_input,
            "model_choice": f"{st.session_state.model_type}/{st.session_state.model_choice}",
            "search_type": st.session_state.search_type
        }
        # Send request to backend to get answer
        with st.spinner('Processing...'):
            answer_data = send_request("/get-answer", query, method="POST")
            st.write(answer_data['answer'])

            # Save conversation to backend
            save_data = {
                "conversation_id": st.session_state.conversation_id,
                "user_input": user_input,
                "answer_data": answer_data
            }
            send_request("/save-conversation", save_data, method="POST")

def main():
    st.markdown("<h1 style='text-align: center;'>Chat Doctor Assistant</h1>", unsafe_allow_html=True)

    # Initialize session state for conversation and feedback
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if 'count' not in st.session_state:
        st.session_state.count = 0
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""

    # Create three columns for the select boxes
    col1, col2, col3 = st.columns(3)

    # Model type selection
    with col1:
        st.session_state.model_type = st.selectbox(
            "Select model type:",
            ["ollama", "openai", "AWS Bedrock"]
        )

    # Model selection based on the model type
    with col2:
        if st.session_state.model_type == "ollama":
            st.session_state.model_choice = st.selectbox(
                "Select an ollama model:",
                ["phi3", 'llama']
            )
        elif st.session_state.model_type == "openai":
            st.session_state.model_choice = st.selectbox(
                "Select an OpenAI model:",
                ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]
            )
        elif st.session_state.model_type == "AWS Bedrock":
            st.session_state.model_choice = st.selectbox(
                "Select an OpenAI model:",
                ["Claude", "Titan"]
            )


    # Search type selection as a dropdown menu
    with col3:
        st.session_state.search_type = st.selectbox(
            "Select search type:",
            ["Vector", "Text"]
        )

    # User input
    st.text_input("What is your question for the Chat Doctor?", 
                  key='user_input', 
                  on_change=ask_question)  # Trigger ask_question on Enter

    # Feedback buttons using images
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Thumbs Up", key="thumbs_up_button"):
            st.session_state.count += 1
            feedback_data = {
                "conversation_id": st.session_state.conversation_id,
                "feedback": 1
            }
            send_request("/save-feedback", feedback_data, method="POST")
        st.image("thumbs_up.png", caption="Thumbs Up", width=50)

    with col2:
        if st.button("Thumbs Down", key="thumbs_down_button"):
            st.session_state.count -= 1
            feedback_data = {
                "conversation_id": st.session_state.conversation_id,
                "feedback": -1
            }
            send_request("/save-feedback", feedback_data, method="POST")
        st.image("thumbs_down.png", caption="Thumbs Down", width=50)

    st.write(f"Current feedback count: {st.session_state.count}")

    # Display recent conversations
    st.subheader("Recent Conversations")
    relevance_filter = st.selectbox("Filter by relevance:", ["All", "RELEVANT", "PARTLY_RELEVANT", "NON_RELEVANT"])
    filter_param = None if relevance_filter == "All" else relevance_filter
    recent_conversations = send_request("/recent-conversations", {"limit": 5, "relevance": filter_param})
    for conv in recent_conversations:
        st.write(f"Q: {conv['question']}")
        st.write(f"A: {conv['answer']}")
        st.write(f"Relevance: {conv['relevance']}")
        st.write(f"Model: {conv['model_used']}")
        st.write("---")

    # Display feedback stats
    feedback_stats = send_request("/feedback-stats")
    st.subheader("Feedback Statistics")
    st.write(f"Thumbs up: {feedback_stats['thumbs_up']}")
    st.write(f"Thumbs down: {feedback_stats['thumbs_down']}")

if __name__ == "__main__":
    main()
