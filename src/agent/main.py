""" A script to generate logical data using Groq's LLM capabilities. """

#internal 
from prompts.main import SYSTEM_PROMPT
from schema.main import Response
import instructor


#external 
from groq import Groq

client = instructor.from_groq(Groq())


def generate_logical_data(messages, query):
    chat_completion = client.chat.completions.create(
        messages.append(
            {
                "role": "user",
                "content": query,
            }
        ),
        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",
        response_model=Response
    )
    # Print the completion returned by the LLM.
    response = chat_completion.choices[0].message.content

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    return response