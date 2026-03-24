# ai_cofounder_agent/agents/persona_generator.py

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
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain, LLMChain
from langchain.schema.messages import SystemMessage
import json
import os

from research_llm.paths import data_outputs_dir

# Prompt for generating multiple personas from market data
multi_persona_prompt = PromptTemplate(
    input_variables=["market_data"],
    template="""
You are a market research expert. Generate exactly 3 distinct customer personas based on the market research below, make sure they are the costumer most likely to need or purchase the product.

Market Research:
{market_data}

IMPORTANT: You MUST generate exactly 3 personas. Each persona should be completely different from the others. Go further in-depth in each point (goals, pain points, values, etc...), by explaining them in more detail.

Format each persona exactly like this:

PERSONA 1:
Name: [Full Name]
Age: [Age]
Gender: [Gender]
Location: [City, State, Urban/Suburban/Rural]
Job/Education: [Job title and education]
Goals:
• [Goal 1]
• [Goal 2]
• [Goal 3]
• [Goal 4]
Pain Points:
• [Pain point 1]
• [Pain point 2]
• [Pain point 3]
• [Pain point 4]
Values:
• [Value 1]
• [Value 2]
• [Value 3]
• [Value 4]
Preferred Shopping Methods:
• [Method 1]
• [Method 2]
• [Method 3]
• [Method 4]
Brand Preferences:
• [Preference 1]
• [Preference 2]
• [Preference 3]
• [Preference 4]
Lifestyle & Habits:
• [Habit 1]
• [Habit 2]
• [Habit 3]
• [Habit 4]
Communication Style:
• [Style 1]
• [Style 2]
• [Style 3]
• [Style 4]

PERSONA 2:
Name: [Full Name]
Age: [Age]
Gender: [Gender]
Location: [City, State, Urban/Suburban/Rural]
Job/Education: [Job title and education]
Goals:
• [Goal 1]
• [Goal 2]
• [Goal 3]
• [Goal 4]
Pain Points:
• [Pain point 1]
• [Pain point 2]
• [Pain point 3]
• [Pain point 4]
Values:
• [Value 1]
• [Value 2]
• [Value 3]
• [Value 4]
Preferred Shopping Methods:
• [Method 1]
• [Method 2]
• [Method 3]
• [Method 4]
Brand Preferences:
• [Preference 1]
• [Preference 2]
• [Preference 3]
• [Preference 4]
Lifestyle & Habits:
• [Habit 1]
• [Habit 2]
• [Habit 3]
• [Habit 4]
Communication Style:
• [Style 1]
• [Style 2]
• [Style 3]
• [Style 4]

PERSONA 3:
Name: [Full Name]
Age: [Age]
Gender: [Gender]
Location: [City, State, Urban/Suburban/Rural]
Job/Education: [Job title and education]
Goals:
• [Goal 1]
• [Goal 2]
• [Goal 3]
• [Goal 4]
Pain Points:
• [Pain point 1]
• [Pain point 2]
• [Pain point 3]
• [Pain point 4]
Values:
• [Value 1]
• [Value 2]
• [Value 3]
• [Value 4]
Preferred Shopping Methods:
• [Method 1]
• [Method 2]
• [Method 3]
• [Method 4]
Brand Preferences:
• [Preference 1]
• [Preference 2]
• [Preference 3]
• [Preference 4]
Lifestyle & Habits:
• [Habit 1]
• [Habit 2]
• [Habit 3]
• [Habit 4]
Communication Style:
• [Style 1]
• [Style 2]
• [Style 3]
• [Style 4]

Make sure each persona represents a different segment of the target market with distinct characteristics, goals, and pain points.
"""
)


def generate_multiple_personas(market_data: str, max_retries=3):
    """Generate 3 distinct personas from market data with retry mechanism"""
    llm = ChatOpenAI(model_name="gpt-4o")
    chain = multi_persona_prompt | llm | StrOutputParser()

    for attempt in range(max_retries):
        print(f"Generating personas (attempt {attempt + 1}/{max_retries})...")
        personas_raw = chain.invoke({"market_data": market_data})
        personas = parse_personas(personas_raw)

        if len(personas) >= 3:
            print(f"Successfully generated {len(personas)} personas!")
            return personas_raw
        else:
            print(f"Generated {len(personas)} personas, need 3. Retrying...")

    # If we still don't have 3 personas after retries, try a simpler approach
    print("Using fallback method to generate 3 personas...")
    fallback_prompt = PromptTemplate(
        input_variables=["market_data"],
        template="""
Generate exactly 3 different customer personas for eco-friendly fashion. Make them very different from each other.

Market Research: {market_data}

Format:
PERSONA 1:
Name: [Name]
Age: [Age]
Job: [Job]
Goals: [Goals]
Pain Points: [Pain Points]

PERSONA 2:
Name: [Name]
Age: [Age]
Job: [Job]
Goals: [Goals]
Pain Points: [Pain Points]

PERSONA 3:
Name: [Name]
Age: [Age]
Job: [Job]
Goals: [Goals]
Pain Points: [Pain Points]
"""
    )

    fallback_chain = fallback_prompt | llm | StrOutputParser()
    return fallback_chain.invoke({"market_data": market_data})


def parse_personas(personas_text: str):
    """Parse the generated personas text into a list of persona dictionaries"""
    personas = []
    current_persona = {}
    current_section = ""

    lines = personas_text.split('\n')

    for line in lines:
        line = line.strip()

        # Check for new persona section
        if line.startswith('PERSONA') and ('1:' in line or '2:' in line or '3:' in line):
            # Only add if persona has meaningful content
            if current_persona and len(current_persona) > 2:
                personas.append(current_persona)
            current_persona = {}
            current_section = ""
            continue

        # Skip empty lines, section dividers, and lines with just asterisks
        if not line or line.startswith('---') or line.startswith('===') or line == '**' or line == '*':
            continue

        # Handle bullet points (lines starting with •)
        if line.startswith('•'):
            # Skip empty bullet points or bullet points with just asterisks
            bullet_content = line[1:].strip()
            if bullet_content and bullet_content != '**' and bullet_content != '*':
                if current_section and current_section in current_persona:
                    if isinstance(current_persona[current_section], list):
                        current_persona[current_section].append(bullet_content)
                    else:
                        current_persona[current_section] = [
                            current_persona[current_section], bullet_content]
            continue

        # Handle key-value pairs
        if ':' in line and not line.startswith('PERSONA'):
            # Split on first colon only
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()

                # Clean up key (remove asterisks and extra spaces)
                key = key.replace('*', '').strip()

                # Skip if key is empty or just asterisks
                if not key or key == '' or key == '**':
                    continue

                current_section = key

                # Clean up value (remove asterisks)
                value = value.replace('*', '').strip()

                # If value is not empty and not just asterisks, store it
                if value and value != '' and value != '**':
                    current_persona[key] = value
                else:
                    # Initialize empty list for bullet points
                    current_persona[key] = []

    # Add the last persona if it has meaningful content
    if current_persona and len(current_persona) > 2:
        personas.append(current_persona)

    # Clean up personas - remove any empty lists and ensure proper formatting
    cleaned_personas = []
    for persona in personas:
        cleaned_persona = {}
        for key, value in persona.items():
            if isinstance(value, list):
                # Only keep non-empty lists
                if value:
                    cleaned_persona[key] = value
            elif value and value.strip():  # Only keep non-empty strings
                cleaned_persona[key] = value.strip()

        # Only add personas with meaningful content
        if len(cleaned_persona) >= 3:  # At least name, age, and one other field
            cleaned_personas.append(cleaned_persona)

    return cleaned_personas


def display_personas(personas):
    """Display the generated personas in a nice format"""
    print("\n=== GENERATED PERSONAS ===\n")

    if not personas:
        print("No valid personas were generated. Please try again.")
        return

    for i, persona in enumerate(personas, 1):
        print(f"PERSONA {i}:")
        print("-" * 40)

        for key, value in persona.items():
            if isinstance(value, list):
                print(f"{key}:")
                for item in value:
                    if item and item.strip():  # Only show non-empty items
                        print(f"  • {item}")
            else:
                print(f"{key}: {value}")
        print()


def start_roleplay_conversation(persona: dict, persona_index: int, market_data: str, all_conversations: dict):
    """Start a roleplay conversation with a specific persona"""
    llm = ChatOpenAI(model_name="gpt-4o")

    # Create persona description for the prompt
    persona_desc = ""
    for key, value in persona.items():
        if isinstance(value, list):
            persona_desc += f"{key}:\n"
            for item in value:
                persona_desc += f"• {item}\n"
        else:
            persona_desc += f"{key}: {value}\n"

    persona_name = persona.get('Name', 'this person')

    print(
        f"\n--- Chatting with {persona.get('Name', f'Persona {persona_index}')} ---\n")
    print("Type 'exit' to quit the conversation.")
    print("Type 'switch' to switch to another persona.")
    print("Type 'memory' to see current conversation history.\n")

    # Store conversation history for this persona
    conversation_history = []

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:  # Handle empty input
                continue

            if user_input.lower() == "exit":
                print("Exiting conversation...")
                break
            elif user_input.lower() == "switch":
                print("Switching to persona selection...")
                # Save current conversation before switching
                if conversation_history:
                    all_conversations[f"persona_{persona_index}"] = {
                        "persona": persona,
                        "conversations": conversation_history
                    }
                return all_conversations
            elif user_input.lower() == "memory":
                print("Current conversation history:")
                for conv in conversation_history:
                    print(f"You: {conv['user']}")
                    print(
                        f"{persona.get('Name', f'Persona {persona_index}')}: {conv['persona']}")
                continue

            # Build conversation history for context
            history_text = ""
            if conversation_history:
                history_text = "\n".join([
                    f"You: {conv['user']}\n{persona.get('Name', f'Persona {persona_index}')}: {conv['persona']}"
                    # Keep last 5 exchanges for context
                    for conv in conversation_history[-5:]
                ])

            # Create the full prompt dynamically - NO TEMPLATE VARIABLES
            full_prompt = f"""You are role-playing as the following customer persona:

{persona_desc}

You are based on this market research:
{market_data}

You are not an AI, you are the customer {persona_name}, respond the same way the human customer would based on the above context as if you are the customer answering, you are role-playing as the customer so we can know more about the customer. Don't ever mention you are an LLM. Respond conversationally to the user's questions, staying in character. Be honest about your needs, frustrations, and preferences.

Conversation history:
{history_text}

User: {user_input}
Persona:"""

            # Generate response directly from LLM - NO CHAIN
            response = llm.invoke(full_prompt)
            print(f"{persona.get('Name', f'Persona {persona_index}')}:",
                  response.content)

            # Save conversation to history
            conversation_history.append({
                "user": user_input,
                "persona": response.content
            })

        except KeyboardInterrupt:
            print("\nConversation interrupted. Exiting...")
            break
        except Exception as e:
            print(f"Error in conversation: {e}")
            print("Please try again or type 'exit' to quit.")
            continue

    # Save conversation history for this persona
    if conversation_history:
        all_conversations[f"persona_{persona_index}"] = {
            "persona": persona,
            "conversations": conversation_history
        }

    return all_conversations


def save_all_data(personas, all_conversations, market_data):
    """Save all personas and conversations to files"""

    # Save personas
    personas_data = {
        "market_data": market_data,
        "personas": personas,
        "raw_text": "\n\n".join([f"PERSONA {i+1}:\n" + "\n".join([f"{k}: {v}" for k, v in p.items()]) for i, p in enumerate(personas)])
    }

    out = data_outputs_dir()
    with open(out / "persona_output.json", "w") as f:
        json.dump(personas_data, f, indent=4)

    # Save all conversations
    with open(out / "conversation_history.json", "w") as f:
        json.dump(all_conversations, f, indent=4)

    print(f"\nData saved under {out}:")
    print(f"- Personas: persona_output.json")
    print(f"- All conversations: conversation_history.json")


def main():
    """Main function to run the multi-persona system"""
    sample_market_data = (
        "College students aged 18-24, interested in eco-friendly fashion. Frequently shop on Depop, prefer sustainable brands, "
        "often discover products through TikTok influencers. Price sensitive but value transparency and ethical production."
    )

    print("=== MULTI-PERSONA GENERATOR ===\n")

    # Generate personas
    print("Generating 3 distinct personas...")
    personas_raw = generate_multiple_personas(sample_market_data)
    personas = parse_personas(personas_raw)

    # Display personas
    display_personas(personas)

    # Check if we have valid personas
    if not personas:
        print("Failed to generate valid personas. Please try running the script again.")
        return

    print(f"Successfully generated {len(personas)} persona(s)")

    # Store all conversations
    all_conversations = {}

    while True:
        print("\nChoose a persona to chat with:")
        for i, persona in enumerate(personas, 1):
            name = persona.get('Name', f'Persona {i}')
            age = persona.get('Age', '')
            job = persona.get('Job/Education', '')
            print(f"{i}. {name} - {age} {job}")

        print(f"{len(personas) + 1}. Exit")

        try:
            choice = int(
                input(f"\nEnter your choice (1-{len(personas) + 1}): "))

            if choice == len(personas) + 1:
                break
            elif 1 <= choice <= len(personas):
                # Start conversation with selected persona
                all_conversations = start_roleplay_conversation(
                    personas[choice-1],
                    choice,
                    sample_market_data,
                    all_conversations
                )

                # Ask if user wants to continue with other personas
                if len(personas) > 1:
                    continue_choice = input(
                        "\nContinue with other personas? (y/n): ").lower()
                    if continue_choice != 'y':
                        break
            else:
                print(f"Invalid choice. Please enter 1-{len(personas) + 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Save all data
    save_all_data(personas, all_conversations, sample_market_data)

    print(f"\n=== SESSION COMPLETE ===")
    print(f"Generated {len(personas)} persona(s)")
    print(f"Total conversations: {len(all_conversations)}")

    # Show summary of conversations
    for persona_key, data in all_conversations.items():
        persona_name = data['persona'].get('Name', persona_key)
        conv_count = len(data['conversations'])
        print(f"- {persona_name}: {conv_count} exchanges")


if __name__ == "__main__":
    main()
