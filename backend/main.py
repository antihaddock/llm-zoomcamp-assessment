from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import save_conversation, save_feedback, get_recent_conversations, get_feedback_stats
from assistant import get_answer
import uvicorn

# Initialize the FastAPI app
app = FastAPI()

# Pydantic model for incoming requests
class ConversationRequest(BaseModel):
    conversation_id: str
    question: str

class FeedbackRequest(BaseModel):
    conversation_id: str
    feedback: int

# Endpoint to get an answer and save the conversation in the database
@app.post("/conversation")
async def conversation(request: ConversationRequest):
    try:
        # Call the assistant's get_answer function
        answer_data = get_answer(request.question)

        # Save the conversation to the database
        save_conversation(
            conversation_id=request.conversation_id,
            question=request.question,
            answer_data=answer_data
        )

        return {
            "status": "success",
            "conversation_id": request.conversation_id,
            "answer": answer_data["answer"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to save feedback for a conversation
@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    try:
        # Save the feedback in the database
        save_feedback(conversation_id=request.conversation_id, feedback=request.feedback)
        return {"status": "feedback saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to retrieve recent conversations (optionally filtered by relevance)
@app.get("/get-recent-conversations")
async def get_recent_conversations(limit: int = 5, relevance: Optional[str] = None):
    try:
        conversations = get_recent_conversations(limit=limit, relevance=relevance)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get feedback statistics
@app.get("/feedback-stats")
async def feedback_stats():
    try:
        stats = get_feedback_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)