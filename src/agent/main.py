""" A script to generate logical data using Groq's LLM capabilities. """

#internal 
from src.prompts.main import SYSTEM_PROMPT
from src.schema.main import LogicalDataModel
import instructor
from dotenv import load_dotenv

load_dotenv()


#external 
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = instructor.from_groq(Groq())


def generate_logical_data(messages, query):
    # Do NOT append the user message here; it is already added in the API
    # Call the LLM with all keyword arguments
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        response_model=LogicalDataModel
    )
    # The response is already the structured object
    response = chat_completion

    # Append the assistant's response as a message (as JSON)
    messages.append(
        {
            "role": "assistant",
            "content": response.model_dump(),
        }
    )

    return response.model_dump()