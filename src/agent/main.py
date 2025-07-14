""" A script to generate logical data using Groq's LLM capabilities. """

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from src.prompts.main import SYSTEM_PROMPT, INTENT_PROMPT
from src.schema.main import LogicalDataModel
from openai import Client
from dotenv import load_dotenv
import json
from datetime import datetime, timezone
import re

load_dotenv()

# Remove the global client initialization - it's blocking startup
# client = Client(
#     base_url="https://language-model-service.mangobeach-c18b898d.switzerlandnorth.azurecontainerapps.io/api/v2/openai/text/",
#     api_key="LMS_API_KEY"  # Uses default value as per your sample
# )

# In-memory chat histories per user (no login, user_id required in header)
chat_histories: Dict[str, List[Dict[str, Any]]] = {}

DEFAULT_USER_ID = "demo-user"

class Message(BaseModel):
    """A single message in the chat between user and assistant."""
    role: Literal["user", "assistant"] = Field(..., description="The role of the message sender: 'user' or 'assistant'.")
    content: Any = Field(..., description="The message content. For 'user', this is a string. For 'assistant', this is the logical data model as a JSON object.")
    timestamp: str = Field(..., description="The ISO 8601 UTC timestamp when the message was created.")

class QueryRequest(BaseModel):
    """Request body for the /model-chat endpoint. Only the user's query is required."""
    query: str = Field(..., description="The user's request or instruction for the data modeling assistant.")

class QueryResponse(BaseModel):
    """Response body for the /model-chat endpoint, containing the user query and the assistant's response."""
    messages: List[Message] = Field(..., description="The user query and the assistant's response (logical data model).")

class IntentResponse(BaseModel):
    response: str 


def classify_intent(messages, query):
    messages.append({
        "role": "user",
        "content": query
    })
    client = Client(
        base_url="https://language-model-service.mangobeach-c18b898d.switzerlandnorth.azurecontainerapps.io/api/v2/openai/text/",
        api_key="LMS_API_KEY"
    )
    
    # Call your in-house GPT API
    # Note: messages should contain the full conversation history
    # with previous assistant responses as JSON objects
    chat_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        response_format=IntentResponse
    )
    response = chat_completion.choices[0].message.parsed

    # Convert the LogicalDataModel to a dict for storage
    response_dict = response.model_dump()

    print("response dict from intent classification: ", response_dict)

    return response_dict['response']


def generate_logical_data(messages, query):
    messages.append({
        "role": "user",
        "content": query
    })
    # Create client only when needed (lazy initialization)
    client = Client(
        base_url="https://language-model-service.mangobeach-c18b898d.switzerlandnorth.azurecontainerapps.io/api/v2/openai/text/",
        api_key="LMS_API_KEY"
    )
    
    # Call your in-house GPT API
    # Note: messages should contain the full conversation history
    # with previous assistant responses as JSON objects
    chat_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        response_format=LogicalDataModel
    )
    response = chat_completion.choices[0].message.parsed

    # Convert the LogicalDataModel to a dict for storage
    response_dict = response.model_dump()

    messages.append(
        {
            "role": "assistant",
            "content": response_dict,
        }
    )

    return response_dict

def generate_conversational_response(messages, query):
    messages.append({
        "role": "user",
        "content": query
    })
    # Create client only when needed (lazy initialization)
    client = Client(
        base_url="https://language-model-service.mangobeach-c18b898d.switzerlandnorth.azurecontainerapps.io/api/v2/openai/text/",
        api_key="LMS_API_KEY"
    )
    
    # Call your in-house GPT API
    # Note: messages should contain the full conversation history
    # with previous assistant responses as JSON objects
    chat_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        response_format=IntentResponse
    )
    response = chat_completion.choices[0].message.parsed

    # Convert the LogicalDataModel to a dict for storage
    response_dict = response.model_dump()

    print("conversational api call: ", response_dict["response"])

    messages.append(
        {
            "role": "assistant",
            "content": response_dict["response"],
        }
    )

    return response_dict["response"]

def order_chat_history(history):
    # Group into pairs: [user, assistant]
    pairs = []
    i = 0
    while i < len(history):
        if i + 1 < len(history) and history[i]["role"] == "user" and history[i+1]["role"] == "assistant":
            pairs.append([history[i], history[i+1]])
            i += 2
        else:
            pairs.append([history[i]])
            i += 1
    # Reverse pairs if more than one user query
    if len(pairs) > 1:
        pairs = list(reversed(pairs))
    # Flatten back to a single list
    ordered = [msg for pair in pairs for msg in pair]
    return ordered

def extract_json_from_string(s):
    # Try to extract JSON from a code block
    match = re.search(r"```(?:json)?\n(.*?)```", s, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except Exception:
            pass
    # Try to parse the whole string as JSON
    try:
        return json.loads(s)
    except Exception:
        pass
    return s  # Return as-is if not JSON

GREETINGS = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]

def is_greeting(text):
    return text.strip().lower() in GREETINGS

CASUAL_QUERIES = [
    "what can you do", "who are you", "help", "what is this", "what do you do", "how can you help", "your capabilities"
]

def is_casual_query(text):
    return text.strip().lower() in CASUAL_QUERIES

def get_utc_timestamp():
    return datetime.now(timezone.utc).isoformat()

app = FastAPI(title="Logical Data Modeling Assistant API", description="Generate and iteratively refine logical data models via chat.")

# Add CORS middleware to allow all origins (for development; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/model-chat", response_model=QueryResponse, summary="Chat with the logical data modeling assistant", tags=["Model Chat"])
def model_chat(request: QueryRequest, user_id: Optional[str] = Header(DEFAULT_USER_ID, include_in_schema=False)) -> QueryResponse:
    # Use default user_id if not provided
    # Get or create chat history for this user (user+assistant messages only)
    history = chat_histories.setdefault(user_id, [])
    # Add the new user message to the history
    history.append({"role": "user", "content": request.query, "timestamp": get_utc_timestamp()})
    # Prepare messages for the LLM (system prompt + full history)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    intent_history = [{"role": "system", "content": INTENT_PROMPT}]
    for m in history:
        if m["role"] == "assistant" and isinstance(m["content"], dict):
            # Convert dict to JSON string for LLM
            messages.append({"role": m["role"], "content": json.dumps(m["content"])} )
            intent_history.append({"role": m["role"], "content": json.dumps(m["content"])} )
        else:
            messages.append({"role": m["role"], "content": m["content"]})
            intent_history.append({"role": m["role"], "content": m["content"]})

    intent = classify_intent(intent_history, request.query)

    print('intent derived: ', intent)

    if intent == 'CONVO':
        response = generate_conversational_response(messages, request.query)
        print("convo bot response: ", response)
        history.append({"role": "assistant", "content": response, "timestamp": get_utc_timestamp()})
    elif intent == 'MODEL':
        response_dict = generate_logical_data(messages, request.query)
        print("model bot response: ", response_dict)
        history.append({"role": "assistant", "content": response_dict, "timestamp": get_utc_timestamp()})

    print(history)
    # Generate assistant response (returns dict)
    #response_dict = generate_logical_data(messages, request.query)
    # Add the assistant's response to the history
    #history.append({"role": "assistant", "content": response_dict, "timestamp": get_utc_timestamp()})
    # Save updated history
    chat_histories[user_id] = history
    # Return messages in standard order (most recent user+assistant pair first)
    # Convert history to Message objects with timestamps
    return QueryResponse(messages=[Message(**msg) for msg in order_chat_history(history)])

@app.post("/model-chat/reset", summary="Reset the chat history", tags=["Model Chat"])
def reset_chat(user_id: Optional[str] = Header(DEFAULT_USER_ID, include_in_schema=False)) -> Dict[str, str]:
    chat_histories[user_id] = []
    return {"message": "Chat history has been reset."}

@app.get("/model-chat/history", response_model=QueryResponse, summary="Get the current chat history", tags=["Model Chat"])
def get_chat_history(user_id: Optional[str] = Header(DEFAULT_USER_ID, include_in_schema=False)) -> QueryResponse:
    # Convert history to Message objects with timestamps
    return QueryResponse(messages=[Message(**msg) for msg in order_chat_history(chat_histories.get(user_id, []))])