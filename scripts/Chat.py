# Chat.py - Simple ChatGPT Conversation Interface

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_llm.bootstrap import bootstrap
from research_llm.config.settings import apply_langsmith_env

bootstrap()
apply_langsmith_env()

from langchain.chat_models import ChatOpenAI
from langchain.schema.messages import HumanMessage, AIMessage


def chat_with_gpt():
    """Simple chat interface with ChatGPT"""

    # Initialize the chat model
    llm = ChatOpenAI(model_name="gpt-4o")

    # Store conversation history
    conversation_history = []

    print("=== ChatGPT Conversation ===")
    print("Type 'exit' to quit the conversation.")
    print("Type 'clear' to clear conversation history.")
    print("Type 'history' to see conversation history.")
    print()

    while True:
        # Get user input
        user_input = input("You: ")

        # Handle special commands
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        elif user_input.lower() == "clear":
            conversation_history = []
            print("Conversation history cleared!")
            continue
        elif user_input.lower() == "history":
            if conversation_history:
                print("\nConversation History:")
                for i, (user_msg, ai_msg) in enumerate(conversation_history, 1):
                    print(f"{i}. You: {user_msg}")
                    print(f"   ChatGPT: {ai_msg}")
                    print()
            else:
                print("No conversation history yet.")
            continue

        # Skip empty input
        if not user_input.strip():
            continue

        try:
            # Create messages for the conversation
            messages = []

            # Add conversation history
            for user_msg, ai_msg in conversation_history:
                messages.append(HumanMessage(content=user_msg))
                messages.append(AIMessage(content=ai_msg))

            # Add current user message
            messages.append(HumanMessage(content=user_input))

            # Get response from ChatGPT
            response = llm.invoke(messages)

            # Extract the response content
            ai_response = response.content

            # Display the response
            print("ChatGPT:", ai_response)
            print()

            # Store in conversation history
            conversation_history.append((user_input, ai_response))

        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    chat_with_gpt()
