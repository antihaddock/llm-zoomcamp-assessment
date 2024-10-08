from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Import your assistant, database functions here
from chat_functions import get_answer
from database import save_conversation, save_feedback, get_recent_conversations, get_feedback_stats


app = FastAPI()

# Request models for FastAPI endpoints
class QueryRequest(BaseModel):
    user_input: str
    model_choice: str
    search_type: str

class FeedbackRequest(BaseModel):
    conversation_id: str
    feedback: int

class AnswerData(BaseModel):
    answer: str
    response_time: float
    relevance: str
    relevance_explanation: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    eval_prompt_tokens: int
    eval_completion_tokens: int
    eval_total_tokens: int
    openai_cost: float

class ConversationRequest(BaseModel):
    conversation_id: str
    user_input: str
    answer_data: AnswerData

# Endpoint for getting an answer
@app.post("/get-answer")
def get_answer_endpoint(query: QueryRequest):
    answer_data = get_answer(query.user_input, query.model_choice, query.search_type)
    return answer_data

# Endpoint for saving a conversation
@app.post("/save-conversation")
def save_conversation_endpoint(request: ConversationRequest):
    save_conversation(request.conversation_id, request.user_input, request.answer_data.dict())
    return {"status": "success"}

# Endpoint for saving feedback
@app.post("/save-feedback")
def save_feedback_endpoint(feedback_request: FeedbackRequest):
    save_feedback(feedback_request.conversation_id, feedback_request.feedback)
    return {"status": "success"}

# Endpoint to get recent conversations
@app.get("/recent-conversations")
def recent_conversations(limit: int, relevance: str = None):
    return get_recent_conversations(limit, relevance)

# Endpoint to get feedback stats
@app.get("/feedback-stats")
def feedback_stats():
    return get_feedback_stats()

# Optional: A root endpoint for basic health check or welcome
@app.get("/")
def read_root():
    return {"message": "Course Assistant backend is running"}

# Main entry point
if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)