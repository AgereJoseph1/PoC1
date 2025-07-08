""" Test Suite """
#internal 
from agent.main import generate_logical_data
from prompts.main import SYSTEM_PROMPT

def main():
    messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
]
    
    while True:
        query = input("Enter your query (or type 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        
        response = generate_logical_data(messages, query)
        print("Generated Logical Data Model:")
        print(response)
        print()
        print()


if __name__ == "__main__":
    main()
