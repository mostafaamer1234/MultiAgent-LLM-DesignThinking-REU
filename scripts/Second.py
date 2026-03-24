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
from langchain.chains import ConversationChain
import json
import os

from research_llm.paths import data_outputs_dir

# Prompt for generating a persona from market data
persona_prompt = PromptTemplate(
    input_variables=["market_research"],
    template="""
Given the following market research, generate a detailed customer persona. 
Include: name, age, gender, location, job/education, goals, pain points, values, preferred shopping methods, and brand preferences.

Market Research:
{market_research}

Persona:
"""
)

# Prompt template for role-playing as the persona
roleplay_prompt = PromptTemplate(
    input_variables=["persona", "market_research"],
    template="""
You are role-playing as the following customer persona:

{persona}

You are based on this market research:
{market_research}

You are not an AI, you are the costumer {persona}, respond the same way the human costumer would based on the {market_research} as if you are the costumer answering, you are role-playing as the costumer so you we can know more about the costumer. Don't ever mention you are an LLM. Respond conversationally to the user's questions, staying in character. Be honest about your needs, frustrations, and preferences.
"""
)


def generate_persona(market_data: str):
    llm = ChatOpenAI(model_name="gpt-4o")
    chain = persona_prompt | llm | StrOutputParser()
    persona_raw = chain.invoke({"market_research": market_data})
    return persona_raw


def start_roleplay_conversation(persona: str, market_data: str):
    llm = ChatOpenAI(model_name="gpt-4o")
    memory = ConversationBufferMemory()
    system_message = roleplay_prompt.format(
        persona=persona, market_research=market_data)
    conversation = ConversationChain(llm=llm, memory=memory, verbose=True)

    print("\n--- Start Role-Playing ---\n")
    print("Type 'exit' to quit the conversation.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        response = conversation.predict(input=user_input)
        print("Persona:", response)


if __name__ == "__main__":
    sample_market_data = (
        "College students aged 18-24, interested in eco-friendly fashion. Frequently shop on Depop, prefer sustainable brands, "
        "often discover products through TikTok influencers. Price sensitive but value transparency and ethical production."
    )
    persona = generate_persona(sample_market_data)
    print("Generated Persona:\n", persona)

    # Optional: Save to JSON
    persona_json = {
        "raw_text": persona
    }
    with open(data_outputs_dir() / "persona_output.json", "w") as f:
        json.dump(persona_json, f, indent=4)

    # Start interview with the persona
    start_roleplay_conversation(persona, sample_market_data)
