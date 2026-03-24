# SecondAgent.py - Hypothesis Generator and Prototype Recommender

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
from langchain.chains import LLMChain
from langchain.schema.messages import SystemMessage
import json
import os

from research_llm.paths import data_outputs_dir, list_market_research_json_paths

# New: Load business info, personas, and conversations from three files


def load_business_info(file_path=None):
    if file_path is None:
        file_path = str(data_outputs_dir() / "business_info.json")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please run Agent1EX.py first.")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def load_personas(file_path=None):
    if file_path is None:
        file_path = str(data_outputs_dir() / "persona_output.json")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data.get("personas", [])
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please run Agent1EX.py first.")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def load_market_research_json(file_path=None):
    """Load market research data from a JSON file created by market research agents"""
    if not file_path:
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
        return None

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Format the market research data
        return format_market_research_json(data)
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


def load_conversation_history(file_path=None):
    """Load conversation history if it exists"""
    if file_path is None:
        file_path = str(data_outputs_dir() / "conversation_history.json")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def format_all_conversations(all_conversations):
    """Format all conversations from multiple personas into a readable string"""
    formatted_text = ""

    for persona_key, data in all_conversations.items():
        persona = data.get('persona', {})
        conversations = data.get('conversations', [])

        if persona:
            formatted_text += f"\n=== CONVERSATION WITH {persona.get('Name', persona_key)} ===\n"
            formatted_text += f"Persona Details:\n"
            for key, value in persona.items():
                formatted_text += f"{key}: {value}\n"
            formatted_text += "\nConversation:\n"

            for conv in conversations:
                formatted_text += f"User: {conv.get('user', '')}\n"
                formatted_text += f"{persona.get('Name', 'Persona')}: {conv.get('persona', '')}\n\n"

    return formatted_text


# Prompt for generating hypotheses from multiple persona conversations
hypothesis_prompt = PromptTemplate(
    input_variables=["personas_data", "all_conversations",
                     "market_data", "business_description", "business_vision"],
    template="""
Based on the following multiple customer personas and their conversations, the market research (market_data), the business description of what it is (business_description), and the vision/goals of what the business wants to achieve or where it wants to be (business_vision), generate 3-5 specific hypotheses about what problems the users might have or what they could want. 

Business Description: {business_description}
Business Vision/Goal: {business_vision}

Customer Personas:
{personas_data}

All Conversations:
{all_conversations}

Market Research Context:
{market_data}

Generate hypotheses in this format:
1. Hypothesis: [Specific, testable hypothesis about user behavior/needs]
2. Hypothesis: [Another specific hypothesis]
3. Hypothesis: [Another specific hypothesis]

Focus on:
- Common pain points across personas
- Unmet needs that appear in multiple conversations
- Behavioral patterns that emerge
- Preferences that could be leveraged
- Problems that could be solved for multiple user types
- Differences between persona segments
- Gaps in the related market that need to be satisfied
- Problems the user might not be aware of
- Possible hidden opportunities
- Doing something new that could help people
- Be really creative

Hypotheses:
"""
)

# Prompt for generating prototype recommendations
prototype_prompt = PromptTemplate(
    input_variables=["hypothesis", "personas_data",
                     "market_data", "business_description", "business_vision"],
    template="""
Given this specific hypothesis, recommend a concrete prototype or test to validate it.

Business Description: {business_description}
Business Vision/Goal: {business_vision}

Hypothesis: {hypothesis}

Customer Personas:
{personas_data}

Market Research Context:
{market_data}

Provide a detailed prototype recommendation including:
1. What to build/test
2. How to test it
3. What metrics to measure
4. How to interpret results
5. Timeline for testing
6. Which persona segments to focus on

Make it specific and actionable. Focus on quick, low-cost ways to validate the hypothesis.

Prototype Recommendation:
"""
)


def generate_hypotheses(personas_data, all_conversations, market_data, business_description, business_vision):
    """Generate hypotheses from multiple persona conversations"""
    llm = ChatOpenAI(model_name="gpt-4o")
    chain = hypothesis_prompt | llm | StrOutputParser()

    # Format personas data
    personas_text = ""
    if 'personas' in personas_data:
        for i, persona in enumerate(personas_data['personas'], 1):
            personas_text += f"\nPERSONA {i}:\n"
            for key, value in persona.items():
                personas_text += f"{key}: {value}\n"

    # Format all conversations
    conversations_text = format_all_conversations(all_conversations)

    hypotheses = chain.invoke({
        "personas_data": personas_text,
        "all_conversations": conversations_text,
        "market_data": market_data,
        "business_description": business_description,
        "business_vision": business_vision
    })

    return hypotheses


def generate_prototype_recommendation(hypothesis, personas_data, market_data, business_description, business_vision):
    """Generate prototype recommendation for a specific hypothesis"""
    llm = ChatOpenAI(model_name="gpt-4o")
    chain = prototype_prompt | llm | StrOutputParser()

    # Format personas data
    personas_text = ""
    if 'personas' in personas_data:
        for i, persona in enumerate(personas_data['personas'], 1):
            personas_text += f"\nPERSONA {i}:\n"
            for key, value in persona.items():
                personas_text += f"{key}: {value}\n"

    recommendation = chain.invoke({
        "hypothesis": hypothesis,
        "personas_data": personas_text,
        "market_data": market_data,
        "business_description": business_description,
        "business_vision": business_vision
    })

    return recommendation


def analyze_and_recommend():
    """Main function to analyze conversation data and generate hypotheses with prototypes"""

    # Load all context from three files
    business_info = load_business_info()
    personas = load_personas()
    all_conversations = load_conversation_history()

    if not business_info or not personas or not all_conversations:
        print("Missing required context files. Please run Agent1EX.py first and complete at least one conversation.")
        return

    market_data = business_info.get("market_data")
    business_description = business_info.get("business_description")
    business_vision = business_info.get("business_vision")

    if not market_data or not business_description or not business_vision or not personas:
        print("business_info.json or persona_output.json is missing required fields. Please re-run Agent1EX.py.")
        return

    personas_data = {"personas": personas}

    print("=== HYPOTHESIS GENERATOR AGENT ===\n")
    print(f"Loaded {len(personas)} personas and {len(all_conversations)} conversation sessions from Agent1EX.py output.")

    print("\nGenerating hypotheses from conversation data...\n")

    # Generate hypotheses
    hypotheses = generate_hypotheses(
        personas_data, all_conversations, market_data, business_description, business_vision)
    print("GENERATED HYPOTHESES:")
    print("=" * 50)
    print(hypotheses)
    print("\n" + "=" * 50)

    # Parse hypotheses and generate prototypes for each
    hypothesis_lines = [line.strip() for line in hypotheses.split(
        '\n') if line.strip().startswith(('1.', '2.', '3.', '4.', '5.'))]

    all_recommendations = []

    for i, hypothesis_line in enumerate(hypothesis_lines, 1):
        print(f"\n--- HYPOTHESIS {i} ---")
        print(hypothesis_line)

        # Extract just the hypothesis text (remove numbering)
        hypothesis_text = hypothesis_line.split(
            ':', 1)[1].strip() if ':' in hypothesis_line else hypothesis_line

        print(f"\nGenerating prototype recommendation for Hypothesis {i}...")
        recommendation = generate_prototype_recommendation(
            hypothesis_text, personas_data, market_data, business_description, business_vision)

        print(f"\nPROTOTYPE RECOMMENDATION {i}:")
        print("-" * 30)
        print(recommendation)
        print("-" * 30)

        all_recommendations.append({
            "hypothesis": hypothesis_text,
            "recommendation": recommendation
        })

    # Save results to file
    results = {
        "personas_data": personas_data,
        "market_data": market_data,
        "all_conversations": all_conversations,
        "hypotheses": hypotheses,
        "recommendations": all_recommendations
    }

    with open(data_outputs_dir() / "hypothesis_analysis.json", "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n=== ANALYSIS COMPLETE ===")
    print(
        f"Generated {len(hypothesis_lines)} hypotheses with prototype recommendations")
    print(f"Results saved to: hypothesis_analysis.json")


def interactive_hypothesis_explorer():
    """Interactive mode to explore specific hypotheses"""
    print("=== INTERACTIVE HYPOTHESIS EXPLORER ===\n")

    business_info = load_business_info()
    personas = load_personas()
    if not business_info or not personas:
        print("No persona or business info data found. Please run Agent1EX.py first.")
        return
    market_data = business_info.get("market_data")
    business_description = business_info.get("business_description")
    business_vision = business_info.get("business_vision")
    if not business_description or not business_vision or not market_data or not personas:
        print("business_info.json or persona_output.json is missing required fields. Please re-run Agent1EX.py.")
        return
    personas_data = {"personas": personas}

    print("Enter your own hypothesis to get a prototype recommendation:")
    print("Type 'exit' to quit\n")

    while True:
        user_hypothesis = input("Your Hypothesis: ")
        if user_hypothesis.lower() == "exit":
            break

        print("\nGenerating prototype recommendation...")
        recommendation = generate_prototype_recommendation(
            user_hypothesis, personas_data, market_data, business_description, business_vision)

        print("\nPROTOTYPE RECOMMENDATION:")
        print("=" * 40)
        print(recommendation)
        print("=" * 40)
        print()


def show_conversation_summary():
    """Show a summary of all conversations"""
    personas = load_personas()
    all_conversations = load_conversation_history()

    if not personas or not all_conversations:
        print("No data found. Please run Agent1EX.py first.")
        return

    print("=== CONVERSATION SUMMARY ===\n")

    print(f"Total Personas: {len(personas)}")
    print(f"Total Conversation Sessions: {len(all_conversations)}\n")

    for persona_key, data in all_conversations.items():
        persona = data.get('persona', {})
        conversations = data.get('conversations', [])

        print(f"Persona: {persona.get('Name', persona_key)}")
        print(f"Age: {persona.get('Age', 'N/A')}")
        print(f"Job/Education: {persona.get('Job/Education', 'N/A')}")
        print(f"Conversation Exchanges: {len(conversations)}")
        print("-" * 40)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--analyze", "--pipeline"):
        analyze_and_recommend()
    else:
        print("Second Agent - Hypothesis Generator and Prototype Recommender")
        print("1. Run full analysis (generate hypotheses + prototypes)")
        print("2. Interactive hypothesis explorer")
        print("3. Show conversation summary")
        print("\n(Hint: python Agent2Hypothesis.py --analyze  skips this menu)")

        choice = input("\nChoose option (1, 2, or 3): ").strip()

        if choice == "1":
            analyze_and_recommend()
        elif choice == "2":
            interactive_hypothesis_explorer()
        elif choice == "3":
            show_conversation_summary()
        else:
            print("Invalid choice. Running full analysis...")
            analyze_and_recommend()
