""" A script to generate logical data using Groq's LLM capabilities. """

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from src.prompts.main import SYSTEM_PROMPT
from src.schema.main import LogicalDataModel
from openai import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    base_url="https://language-model-service.mangobeach-c18b898d.switzerlandnorth.azurecontainerapps.io/api/v2/openai/text/",
    api_key="LMS_API_KEY"  # Uses default value as per your sample
)

# In-memory chat histories per user (no login, user_id required in header)
chat_histories: Dict[str, List[Dict[str, Any]]] = {}

class Message(BaseModel):
    """A single message in the chat between user and assistant."""
    role: Literal["user", "assistant"] = Field(..., description="The role of the message sender: 'user' or 'assistant'.")
    content: Any = Field(..., description="The message content. For 'user', this is a string. For 'assistant', this is the logical data model as a JSON object.")

class QueryRequest(BaseModel):
    """Request body for the /model-chat endpoint. Only the user's query is required."""
    query: str = Field(..., description="The user's request or instruction for the data modeling assistant.")

class QueryResponse(BaseModel):
    """Response body for the /model-chat endpoint, containing the user query and the assistant's response."""
    messages: List[Message] = Field(..., description="The user query and the assistant's response (logical data model).")

def generate_logical_data(messages, query):
    # Call your in-house GPT API
    chat_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        response_format=LogicalDataModel
    )
    response = chat_completion.choices[0].message.parsed

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    return response

app = FastAPI(title="Logical Data Modeling Assistant API", description="Generate and iteratively refine logical data models via chat.")

@app.post("/model-chat", response_model=QueryResponse, summary="Chat with the logical data modeling assistant", tags=["Model Chat"])
def model_chat(request: QueryRequest, user_id: Optional[str] = Header(None)) -> QueryResponse:
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id header is required")
    # Get or create chat history for this user (user+assistant messages only)
    history = chat_histories.setdefault(user_id, [])
    # Add the new user message to the history
    history.append({"role": "user", "content": request.query})
    # Prepare messages for the LLM (system prompt + full history)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    # Generate assistant response
    response = generate_logical_data(messages, request.query)
    # Add the assistant's response to the history
    history.append({"role": "assistant", "content": response})
    # Save updated history
    chat_histories[user_id] = history
    return QueryResponse(messages=history)

@app.post("/model-chat/reset", summary="Reset the chat history", tags=["Model Chat"])
def reset_chat(user_id: Optional[str] = Header(None)) -> Dict[str, str]:
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id header is required")
    chat_histories[user_id] = []
    return {"message": "Chat history has been reset."}

@app.get("/model-chat/history", response_model=QueryResponse, summary="Get the current chat history", tags=["Model Chat"])
def get_chat_history(user_id: Optional[str] = Header(None)) -> QueryResponse:
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id header is required")
    return QueryResponse(messages=chat_histories.get(user_id, []))