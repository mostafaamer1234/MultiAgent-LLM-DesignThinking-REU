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

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain, LLMChain
from langchain.schema.messages import SystemMessage
import json
import os
import re

from research_llm.paths import data_outputs_dir, list_market_research_json_paths

# Add PDF reading capability
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Note: PyPDF2 not installed. PDF reading will not be available.")
    print("Install with: pip install PyPDF2")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file"""

    if not PDF_AVAILABLE:
        raise ImportError(
            "PyPDF2 is not installed. Please install it with: pip install PyPDF2")

    try:
        with open(pdf_path, 'rb') as file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)

            # Extract text from all pages
            text_content = ""
            total_pages = len(pdf_reader.pages)

            print(f"Reading PDF with {total_pages} pages...")

            for page_num, page in enumerate(pdf_reader.pages, 1):
                print(f"Processing page {page_num}/{total_pages}...")
                page_text = page.extract_text()
                text_content += page_text + "\n"

            print(
                f"Successfully extracted {len(text_content)} characters from PDF")
            return text_content.strip()

    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file '{pdf_path}' not found")
    except Exception as e:
        raise Exception(f"Error reading PDF: {e}")


def clean_pdf_text(text: str) -> str:
    """Clean and format extracted PDF text for better analysis"""

    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:  # Only keep non-empty lines
            cleaned_lines.append(line)

    # Join lines with proper spacing
    cleaned_text = ' '.join(cleaned_lines)

    # Remove excessive spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    return cleaned_text.strip()


def get_market_data_from_pdf():
    """Get market research data from a PDF file"""
    print("=== PDF MARKET RESEARCH INPUT ===\n")

    if not PDF_AVAILABLE:
        print("PDF reading is not available. Please install PyPDF2:")
        print("pip install PyPDF2")
        return None

    try:
        pdf_path = input("Enter the path to your PDF file: ").strip()

        if not pdf_path:
            print("No PDF path provided.")
            return None

        # Extract text from PDF
        print(f"\nExtracting text from PDF: {pdf_path}")
        raw_text = extract_text_from_pdf(pdf_path)

        # Clean the extracted text
        print("Cleaning extracted text...")
        cleaned_text = clean_pdf_text(raw_text)

        # Show preview of extracted text
        preview_length = 500
        preview = cleaned_text[:preview_length] + \
            "..." if len(cleaned_text) > preview_length else cleaned_text
        print(f"\nExtracted text preview ({len(cleaned_text)} characters):")
        print("-" * 60)
        print(preview)
        print("-" * 60)

        # Ask user if they want to proceed
        proceed = input(
            "\nProceed with this market research data? (y/n): ").lower().strip()

        if proceed == 'y':
            return cleaned_text
        else:
            print("Analysis cancelled.")
            return None

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None


def get_market_data_from_text_file():
    """Get market research data from a text file"""
    print("=== TEXT FILE MARKET RESEARCH INPUT ===\n")

    try:
        file_path = input("Enter the path to your text file: ").strip()

        if not file_path:
            print("No file path provided.")
            return None

        # Read text file
        print(f"\nReading text file: {file_path}")
        with open(file_path, 'r') as f:
            market_data = f.read()

        print(f"Successfully read {len(market_data)} characters from file")

        # Show preview
        preview_length = 300
        preview = market_data[:preview_length] + \
            "..." if len(market_data) > preview_length else market_data
        print(f"\nFile content preview:")
        print("-" * 50)
        print(preview)
        print("-" * 50)

        # Ask user if they want to proceed
        proceed = input(
            "\nProceed with this market research data? (y/n): ").lower().strip()

        if proceed == 'y':
            return market_data
        else:
            print("Analysis cancelled.")
            return None

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def get_market_data_from_json():
    """Get market research data from a JSON file created by market research agents"""
    print("=== JSON MARKET RESEARCH INPUT ===\n")

    try:
        json_paths = list_market_research_json_paths()

        if json_paths:
            print("Available market research JSON files:")
            for i, file in enumerate(json_paths, 1):
                print(f"{i}. {file}")

            choice = input(
                f"\nSelect a file (1-{len(json_paths)}) or enter custom path: ").strip()

            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(json_paths):
                    file_path = str(json_paths[file_index])
                else:
                    print("Invalid selection.")
                    return None
            except ValueError:
                file_path = choice
        else:
            file_path = input(
                "Enter the path to your market research JSON file: ").strip()

        if not file_path:
            print("No file path provided.")
            return None

        # Read and parse JSON file
        print(f"\nReading JSON file: {file_path}")
        with open(file_path, 'r') as f:
            market_data = json.load(f)

        # Extract relevant information from the JSON structure
        formatted_data = format_market_research_json(market_data)

        print(f"Successfully loaded market research data from {file_path}")

        # Show preview
        preview_length = 500
        preview = formatted_data[:preview_length] + "..." if len(
            formatted_data) > preview_length else formatted_data
        print(f"\nMarket research data preview:")
        print("-" * 60)
        print(preview)
        print("-" * 60)

        # Ask user if they want to proceed
        proceed = input(
            "\nProceed with this market research data? (y/n): ").lower().strip()

        if proceed == 'y':
            return formatted_data
        else:
            print("Analysis cancelled.")
            return None

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def format_market_research_json(data):
    """Format market research JSON data into readable text"""
    formatted_lines = []

    # Extract basic information
    if 'topic' in data:
        formatted_lines.append(f"Market Research Topic: {data['topic']}")

    if 'executive_summary' in data:
        formatted_lines.append(f"\nExecutive Summary:")
        formatted_lines.append(data['executive_summary'])

    if 'market_overview' in data:
        formatted_lines.append(f"\nMarket Overview:")
        formatted_lines.append(data['market_overview'])

    if 'total_market_size' in data:
        formatted_lines.append(
            f"\nTotal Market Size: {data['total_market_size']}")

    if 'market_growth_rate' in data:
        formatted_lines.append(
            f"Market Growth Rate: {data['market_growth_rate']}")

    # Extract key findings
    if 'key_findings' in data and data['key_findings']:
        formatted_lines.append(f"\nKey Findings:")
        for i, finding in enumerate(data['key_findings'], 1):
            formatted_lines.append(f"{i}. {finding}")

    # Extract market segments
    if 'market_segments' in data and data['market_segments']:
        formatted_lines.append(f"\nMarket Segments:")
        for i, segment in enumerate(data['market_segments'], 1):
            formatted_lines.append(f"\n{i}. {segment.get('name', 'Segment')}")
            formatted_lines.append(f"   Size: {segment.get('size', 'N/A')}")
            formatted_lines.append(
                f"   Growth Rate: {segment.get('growth_rate', 'N/A')}")
            formatted_lines.append(f"   Key Characteristics:")
            for char in segment.get('key_characteristics', []):
                formatted_lines.append(f"     • {char}")
            formatted_lines.append(f"   Pain Points:")
            for pain in segment.get('pain_points', []):
                formatted_lines.append(f"     • {pain}")

    # Extract competitors
    if 'competitors' in data and data['competitors']:
        formatted_lines.append(f"\nCompetitive Landscape:")
        for i, competitor in enumerate(data['competitors'], 1):
            formatted_lines.append(
                f"\n{i}. {competitor.get('name', 'Competitor')}")
            formatted_lines.append(
                f"   Market Share: {competitor.get('market_share', 'N/A')}")
            formatted_lines.append(
                f"   Value Proposition: {competitor.get('unique_value_proposition', 'N/A')}")
            formatted_lines.append(f"   Strengths:")
            for strength in competitor.get('strengths', []):
                formatted_lines.append(f"     • {strength}")
            formatted_lines.append(f"   Weaknesses:")
            for weakness in competitor.get('weaknesses', []):
                formatted_lines.append(f"     • {weakness}")

    # Extract market trends
    if 'market_trends' in data and data['market_trends']:
        formatted_lines.append(f"\nMarket Trends:")
        for i, trend in enumerate(data['market_trends'], 1):
            formatted_lines.append(
                f"\n{i}. {trend.get('trend_name', 'Trend')}")
            formatted_lines.append(f"   Impact: {trend.get('impact', 'N/A')}")
            formatted_lines.append(
                f"   Timeframe: {trend.get('timeframe', 'N/A')}")
            formatted_lines.append(
                f"   Description: {trend.get('description', 'N/A')}")

    # Extract opportunities
    if 'opportunities' in data and data['opportunities']:
        formatted_lines.append(f"\nMarket Opportunities:")
        for i, opportunity in enumerate(data['opportunities'], 1):
            formatted_lines.append(
                f"\n{i}. {opportunity.get('opportunity_name', 'Opportunity')}")
            formatted_lines.append(
                f"   Market Size: {opportunity.get('market_size', 'N/A')}")
            formatted_lines.append(
                f"   Feasibility: {opportunity.get('feasibility', 'N/A')}")
            formatted_lines.append(
                f"   Description: {opportunity.get('description', 'N/A')}")

    # Extract risks and challenges
    if 'risks_and_challenges' in data and data['risks_and_challenges']:
        formatted_lines.append(f"\nRisks and Challenges:")
        for i, risk in enumerate(data['risks_and_challenges'], 1):
            formatted_lines.append(f"{i}. {risk}")

    # Extract recommendations
    if 'recommendations' in data and data['recommendations']:
        formatted_lines.append(f"\nStrategic Recommendations:")
        for i, rec in enumerate(data['recommendations'], 1):
            formatted_lines.append(f"{i}. {rec}")

    # Add timestamp if available
    if 'timestamp' in data:
        formatted_lines.append(f"\nResearch conducted on: {data['timestamp']}")

    return "\n".join(formatted_lines)


def get_market_data_interactive():
    """Get market research data through interactive input"""
    print("=== INTERACTIVE MARKET RESEARCH INPUT ===\n")
    print("Enter your market research data below.")
    print("Type 'done' on a new line when finished.")
    print("Type 'sample' to use sample data.\n")

    market_data_lines = []

    while True:
        line = input("Market Research: ")

        if line.lower() == "done":
            break
        elif line.lower() == "sample":
            market_data_lines = [
                "Market Research Report: Sustainable Fashion Industry",
                "Target Audience: College students aged 18-24 interested in eco-friendly fashion.",
                "Key Findings:",
                "- Students frequently shop on Depop and similar second-hand platforms",
                "- Strong preference for sustainable and ethical brands",
                "- Discover new products primarily through TikTok influencers and social media",
                "- Price sensitive but willing to pay more for transparency and ethical production",
                "- Major pain points include limited budget and difficulty finding stylish sustainable options",
                "- Concerns about greenwashing in the fashion industry",
                "- Value authenticity and transparency from brands"
            ]
            break
        else:
            market_data_lines.append(line)

    if market_data_lines:
        market_data = " ".join(market_data_lines)
        return market_data
    else:
        print("No market research data provided.")
        return None


# Prompt for generating multiple personas from market data
multi_persona_prompt = PromptTemplate(
    input_variables=["market_data", "business_description", "business_vision"],
    template="""
You are a market research expert. Generate exactly 3 distinct customer personas based on the market research below, the business description, and the vision/goal of the business. Make sure they are the customers most likely to need or purchase the product, we are in the year 2007, don't use any knowledge or data you have beyond that date, only before.

Business Description: {business_description}
Business Vision/Goal: {business_vision}

Market Research:2

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


def generate_multiple_personas(market_data: str, business_description: str, business_vision: str, max_retries=3):
    """Generate 3 distinct personas from market data with retry mechanism and business context"""
    llm = ChatOpenAI(model_name="gpt-4o")
    chain = multi_persona_prompt | llm | StrOutputParser()

    for attempt in range(max_retries):
        print(f"Generating personas (attempt {attempt + 1}/{max_retries})...")
        personas_raw = chain.invoke({
            "market_data": market_data,
            "business_description": business_description,
            "business_vision": business_vision
        })
        personas = parse_personas(personas_raw)

        if len(personas) >= 3:
            print(f"Successfully generated {len(personas)} personas!")
            return personas_raw
        else:
            print(f"Generated {len(personas)} personas, need 3. Retrying...")

    # If we still don't have 3 personas after retries, try a simpler approach
    print("Using fallback method to generate 3 personas...")
    fallback_prompt = PromptTemplate(
        input_variables=["market_data",
                         "business_description", "business_vision"],
        template="""
Generate exactly 3 different customer personas for this business and vision. Make them very different from each other.

Business Description: {business_description}
Business Vision/Goal: {business_vision}

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
    return fallback_chain.invoke({
        "market_data": market_data,
        "business_description": business_description,
        "business_vision": business_vision
    })


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


def start_roleplay_conversation(persona: dict, persona_index: int, market_data: str, all_conversations: dict, business_description: str, business_vision: str):
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

Business Description: {business_description}
Business Vision/Goal: {business_vision}

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


def save_all_data(personas, all_conversations, market_data, business_description, business_vision):
    """Save all personas, business info, and conversations to files"""

    # 1. Save business info
    business_info = {
        "market_data": market_data,
        "business_description": business_description,
        "business_vision": business_vision
    }
    out = data_outputs_dir()
    with open(out / "business_info.json", "w") as f:
        json.dump(business_info, f, indent=4)

    # 2. Save personas (with business context for backward compatibility)
    personas_data = {
        "personas": personas,
        "raw_text": "\n\n".join([f"PERSONA {i+1}:\n" + "\n".join([f"{k}: {v}" for k, v in p.items()]) for i, p in enumerate(personas)]),
        "business_description": business_description,
        "business_vision": business_vision
    }
    with open(out / "persona_output.json", "w") as f:
        json.dump(personas_data, f, indent=4)

    # 3. Save all conversations
    with open(out / "conversation_history.json", "w") as f:
        json.dump(all_conversations, f, indent=4)

    print(f"\nData saved under {out}:")
    print(f"- Business info: business_info.json")
    print(f"- Personas: persona_output.json")
    print(f"- All conversations: conversation_history.json")


def main():
    """Main function to run the multi-persona system"""
    print("=== MULTI-PERSONA GENERATOR ===\n")

    valid_choices = {"1", "2", "3", "4", "5"}
    choice = None
    while True:
        print("Choose your market research input method:")
        print("1. PDF file")
        print("2. Text file")
        print("3. JSON file (from market research agents)")
        print("4. Interactive input")
        print("5. Use sample data")
        choice = input("\nChoose option (1-5): ").strip()
        if choice in valid_choices:
            break
        print("\nInvalid choice. Please enter a number from 1 to 5.\n")

    # --- Prompt for business context AFTER input method selection ---
    print("\n--- BUSINESS CONTEXT ---")
    business_description = input(
        "Enter a short description of your business: ").strip()
    business_vision = input("Enter your business vision/goal: ").strip()

    market_data = None

    if choice == "1":
        # PDF input mode
        market_data = get_market_data_from_pdf()
    elif choice == "2":
        # Text file input mode
        market_data = get_market_data_from_text_file()
    elif choice == "3":
        # JSON file input mode
        market_data = get_market_data_from_json()
    elif choice == "4":
        # Interactive input mode
        market_data = get_market_data_interactive()
    elif choice == "5":
        # Sample data mode
        market_data = (
            "College students aged 18-24, interested in eco-friendly fashion. Frequently shop on Depop, prefer sustainable brands, "
            "often discover products through TikTok influencers. Price sensitive but value transparency and ethical production."
        )

    if not market_data:
        print("No market research data available. Exiting.")
        return

    # --- Updated: Pass business context to persona generation ---
    print("\nGenerating 3 distinct personas...")
    personas_raw = generate_multiple_personas(
        market_data, business_description, business_vision)
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
                    market_data,
                    all_conversations,
                    business_description,
                    business_vision
                )

                # Ask if user wants to continue with other personas
                if len(personas) > 1:
                    print("\nReturning to persona selection menu...")
                    continue_choice = input(
                        "\nContinue with other personas? (y/n): ").lower()
                    if continue_choice != 'y':
                        break
            else:
                print(f"Invalid choice. Please enter 1-{len(personas) + 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

    # Save all data
    save_all_data(personas, all_conversations, market_data,
                  business_description, business_vision)

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
