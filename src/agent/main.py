""" A script to generate logical data using Groq's LLM capabilities. """

#internal 
from src.schema.main import Response
import instructor


#external 
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = instructor.from_groq(Groq())


def generate_logical_data(messages, query):
    messages.append(
            {
                "role": "user",
                "content": query,
            }
        )
    chat_completion = client.chat.completions.create(
        messages=messages,
        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",
        response_model=Response
    )
    # Print the completion returned by the LLM.
    response = chat_completion

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    return response