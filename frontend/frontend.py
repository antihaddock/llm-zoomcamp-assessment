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

            # Append the question and answer to conversation history
            st.session_state.conversation_history.append({
                "question": user_input,
                "answer": answer_data['answer']
            })

            # Save conversation to backend
            save_data = {
                "conversation_id": st.session_state.conversation_id,
                "user_input": user_input,
                "answer_data": answer_data
            }
            send_request("/save-conversation", save_data, method="POST")

            # Clear user input after asking the question
            st.session_state.user_input = ""

def give_feedback(feedback_value):
    """Handles feedback submission based on user action."""
    feedback_data = {
        "conversation_id": st.session_state.conversation_id,
        "feedback": feedback_value
    }
    send_request("/save-feedback", feedback_data, method="POST")

def main():
    # Add custom CSS to fix the grey sidebar and position it to the left
    st.markdown("""
        <style>
        body {
            background-color: white; /* Set the background color for the body */
        }
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 200px;
            height: 100vh;
            background-color: grey;
            padding: 20px;
            color: white;
            text-align: center;
            font-size: 20px;
        }
        .main-content {
            margin-left: 220px; /* Add a margin to push the UI to the right */
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar (fixed to the left)
    st.markdown("""
        <div class="sidebar">
            Grey Box
        </div>
    """, unsafe_allow_html=True)

    # All the existing UI goes into the main-content section
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>Chat Doctor Assistant</h1>", unsafe_allow_html=True)

    # Initialize session state for conversation and feedback
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if 'count' not in st.session_state:
        st.session_state.count = 0
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Display conversation history
    st.subheader("Conversation History")
    
    # Check if there is conversation history to display
    if len(st.session_state.conversation_history) == 0:
        st.write("No conversation history yet.")
    else:
        # Loop through the conversation history and display each entry
        for conv in st.session_state.conversation_history:
            st.write(f"**Q:** {conv['question']}")
            st.write(f"**A:** {conv['answer']}")
            st.write("---")

    # Display feedback buttons below the conversation history
    st.subheader("Feedback")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍", key="thumbs_up_button"):
            st.session_state.count += 1
            give_feedback(1)
    with col2:
        if st.button("👎", key="thumbs_down_button"):
            st.session_state.count -= 1
            give_feedback(-1)
    st.write(f"Current feedback count: {st.session_state.count}")

    # Chat question input above model selection boxes
    st.subheader("What is your question for the Chat Doctor?")
    st.text_input("", 
                key='user_input', 
                on_change=ask_question)  # Trigger ask_question on Enter

    # Create a space for the select boxes above the input area
    st.subheader("Select Model and Search Type")

    col1, col2, col3 = st.columns(3)

    # Model type selection
    with col1:
        st.session_state.model_type = st.selectbox(
            "Select model type:",
            ["openai","ollama", "AWS Bedrock"]
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
                ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
            )
        elif st.session_state.model_type == "AWS Bedrock":
            st.session_state.model_choice = st.selectbox(
                "Select a Bedrock model:",
                ["Claude", "Titan"]
            )

    # Search type selection as a dropdown menu
    with col3:
        st.session_state.search_type = st.selectbox(
            "Select search type:",
            ["Vector", "Hybrid", "Text"]
        )

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
