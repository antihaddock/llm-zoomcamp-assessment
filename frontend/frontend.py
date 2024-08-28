import streamlit as st
import time
from backend import handle_ask_question, handle_feedback, fetch_recent_conversations, fetch_feedback_stats

def main():
    st.title("Course Assistant")

    # Session state initialization
    backend.initialize_session_state()

    # Course selection
    course = st.selectbox(
        "Select a course:",
        ["machine-learning-zoomcamp", "data-engineering-zoomcamp", "mlops-zoomcamp"]
    )

    # Model selection
    model_choice = st.selectbox(
        "Select a model:",
        ["ollama/phi3", "openai/gpt-3.5-turbo", "openai/gpt-4o", "openai/gpt-4o-mini"]
    )

    # Search type selection
    search_type = st.radio(
        "Select search type:",
        ["Text", "Vector"]
    )

    # User input
    user_input = st.text_input("Enter your question:")

    if st.button("Ask"):
        with st.spinner('Processing...'):
            answer_data = backend.handle_ask_question(user_input, course, model_choice, search_type)
            st.success("Completed!")
            st.write(answer_data['answer'])
            
            # Display monitoring information
            st.write(f"Response time: {answer_data['response_time']:.2f} seconds")
            st.write(f"Relevance: {answer_data['relevance']}")
            st.write(f"Model used: {answer_data['model_used']}")
            st.write(f"Total tokens: {answer_data['total_tokens']}")
            if answer_data['openai_cost'] > 0:
                st.write(f"OpenAI cost: ${answer_data['openai_cost']:.4f}")

    # Feedback buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+1"):
            backend.handle_feedback(1)
    with col2:
        if st.button("-1"):
            backend.handle_feedback(-1)

    st.write(f"Current count: {st.session_state.count}")

    # Display recent conversations
    st.subheader("Recent Conversations")
    relevance_filter = st.selectbox("Filter by relevance:", ["All", "RELEVANT", "PARTLY_RELEVANT", "NON_RELEVANT"])
    recent_conversations = backend.fetch_recent_conversations(relevance_filter)
    for conv in recent_conversations:
        st.write(f"Q: {conv['question']}")
        st.write(f"A: {conv['answer']}")
        st.write(f"Relevance: {conv['relevance']}")
        st.write(f"Model: {conv['model_used']}")
        st.write("---")

    # Display feedback stats
    feedback_stats = backend.fetch_feedback_stats()
    st.subheader("Feedback Statistics")
    st.write(f"Thumbs up: {feedback_stats['thumbs_up']}")
    st.write(f"Thumbs down: {feedback_stats['thumbs_down']}")

if __name__ == "__main__":
    main()
