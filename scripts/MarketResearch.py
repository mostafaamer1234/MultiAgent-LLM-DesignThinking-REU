import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import json
from typing import Dict, List, Any
from research_llm.bootstrap import bootstrap
from research_llm.config import get_settings
from research_llm.paths import data_outputs_dir

bootstrap()
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import re


class MarketSegment(BaseModel):
    """Represents a market segment with its characteristics"""
    name: str = Field(description="Name of the market segment")
    size: str = Field(description="Estimated market size for this segment")
    growth_rate: str = Field(description="Growth rate of this segment")
    key_characteristics: List[str] = Field(description="Key characteristics of this segment")
    pain_points: List[str] = Field(description="Main pain points of this segment")

class Competitor(BaseModel):
    """Represents a competitor in the market"""
    name: str = Field(description="Name of the competitor")
    market_share: str = Field(description="Estimated market share")
    strengths: List[str] = Field(description="Key strengths of the competitor")
    weaknesses: List[str] = Field(description="Key weaknesses of the competitor")
    unique_value_proposition: str = Field(description="Competitor's unique value proposition")

class MarketTrend(BaseModel):
    """Represents a market trend"""
    trend_name: str = Field(description="Name of the trend")
    description: str = Field(description="Description of the trend")
    impact: str = Field(description="Impact on the market (High/Medium/Low)")
    timeframe: str = Field(description="Expected timeframe for this trend")

class MarketOpportunity(BaseModel):
    """Represents a market opportunity"""
    opportunity_name: str = Field(description="Name of the opportunity")
    description: str = Field(description="Description of the opportunity")
    market_size: str = Field(description="Estimated market size for this opportunity")
    feasibility: str = Field(description="Feasibility assessment (High/Medium/Low)")
    time_to_market: str = Field(description="Estimated time to market")

class MarketResearchReport(BaseModel):
    """Complete market research report"""
    topic: str = Field(description="The market research topic")
    executive_summary: str = Field(description="Executive summary of the market research")
    market_overview: str = Field(description="Overall market overview")
    total_market_size: str = Field(description="Total addressable market size")
    market_growth_rate: str = Field(description="Overall market growth rate")
    market_segments: List[MarketSegment] = Field(description="Key market segments")
    competitors: List[Competitor] = Field(description="Key competitors in the market")
    market_trends: List[MarketTrend] = Field(description="Key market trends")
    opportunities: List[MarketOpportunity] = Field(description="Market opportunities")
    risks_and_challenges: List[str] = Field(description="Key risks and challenges")
    recommendations: List[str] = Field(description="Strategic recommendations")
    research_methodology: str = Field(description="Methodology used for this research")
    data_sources: List[str] = Field(description="Sources of data and information")
    timestamp: str = Field(description="When this research was conducted")

class MarketResearchAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Market Research Agent"""
        s = get_settings()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif s.openai_api_key:
            os.environ["OPENAI_API_KEY"] = s.openai_api_key

        self.llm = ChatOpenAI(
            temperature=0.3, model_name=s.openai_model_synthesis
        )
        self.parser = PydanticOutputParser(pydantic_object=MarketResearchReport)
        
        # Create the main research prompt
        self.research_prompt = PromptTemplate(
            input_variables=["topic", "format_instructions"],
            template="""
You are an expert market research analyst with 15+ years of experience in analyzing markets across various industries. 
Your task is to conduct comprehensive market research on the given topic and provide detailed insights.

Topic: {topic}

Please conduct thorough market research and provide a comprehensive report including:

1. Executive Summary - Key findings and insights
2. Market Overview - Current state and dynamics
3. Market Size - Total addressable market and growth rates
4. Market Segments - Key customer segments with characteristics
5. Competitive Analysis - Major competitors and their positioning
6. Market Trends - Current and emerging trends
7. Opportunities - Potential market opportunities
8. Risks & Challenges - Key risks and barriers
9. Recommendations - Strategic recommendations
10. Methodology - How this research was conducted

Use the following format for your response:
{format_instructions}

Provide detailed, actionable insights based on current market data and trends. Be specific with numbers, percentages, and concrete examples where possible.
"""
        )
    
    def conduct_research(self, topic: str) -> MarketResearchReport:
        """Conduct comprehensive market research on the given topic"""
        print(f"🔍 Conducting market research on: {topic}")
        print("⏳ This may take a few moments...")
        
        try:
            # Get the format instructions
            format_instructions = self.parser.get_format_instructions()
            
            # Create the prompt
            prompt = self.research_prompt.format(
                topic=topic,
                format_instructions=format_instructions
            )
            
            # Run the research
            response = self.llm.invoke(prompt)
            
            # Parse the response
            report = self.parser.parse(response.content)
            report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return report
            
        except Exception as e:
            print(f"❌ Error conducting research: {str(e)}")
            return None
    
    def save_report(self, report: MarketResearchReport, filename: str = None) -> str:
        """Save the market research report to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = re.sub(r'[^a-zA-Z0-9\s]', '', report.topic).replace(' ', '_')
            filename = f"market_research_{safe_topic}_{timestamp}.json"

        try:
            out_path = Path(filename)
            if not out_path.is_absolute():
                out_path = data_outputs_dir() / out_path.name
            with open(out_path, 'w') as f:
                json.dump(report.dict(), f, indent=2)
            print(f"✅ Report saved to: {out_path}")
            return str(out_path)
        except Exception as e:
            print(f"❌ Error saving report: {str(e)}")
            return None
    
    def display_report(self, report: MarketResearchReport):
        """Display the market research report in a formatted way"""
        print("\n" + "="*80)
        print(f"📊 MARKET RESEARCH REPORT: {report.topic.upper()}")
        print("="*80)
        
        # Executive Summary
        print(f"\n📋 EXECUTIVE SUMMARY")
        print("-" * 40)
        print(report.executive_summary)
        
        # Market Overview
        print(f"\n🌍 MARKET OVERVIEW")
        print("-" * 40)
        print(f"Total Market Size: {report.total_market_size}")
        print(f"Growth Rate: {report.market_growth_rate}")
        print(f"\n{report.market_overview}")
        
        # Market Segments
        print(f"\n👥 MARKET SEGMENTS")
        print("-" * 40)
        for i, segment in enumerate(report.market_segments, 1):
            print(f"\n{i}. {segment.name}")
            print(f"   Size: {segment.size}")
            print(f"   Growth Rate: {segment.growth_rate}")
            print(f"   Key Characteristics:")
            for char in segment.key_characteristics:
                print(f"     • {char}")
            print(f"   Pain Points:")
            for pain in segment.pain_points:
                print(f"     • {pain}")
        
        # Competitors
        print(f"\n🏢 COMPETITIVE LANDSCAPE")
        print("-" * 40)
        for i, competitor in enumerate(report.competitors, 1):
            print(f"\n{i}. {competitor.name}")
            print(f"   Market Share: {competitor.market_share}")
            print(f"   Value Proposition: {competitor.unique_value_proposition}")
            print(f"   Strengths:")
            for strength in competitor.strengths:
                print(f"     • {strength}")
            print(f"   Weaknesses:")
            for weakness in competitor.weaknesses:
                print(f"     • {weakness}")
        
        # Market Trends
        print(f"\n📈 MARKET TRENDS")
        print("-" * 40)
        for i, trend in enumerate(report.market_trends, 1):
            print(f"\n{i}. {trend.trend_name}")
            print(f"   Impact: {trend.impact}")
            print(f"   Timeframe: {trend.timeframe}")
            print(f"   Description: {trend.description}")
        
        # Opportunities
        print(f"\n💡 MARKET OPPORTUNITIES")
        print("-" * 40)
        for i, opportunity in enumerate(report.opportunities, 1):
            print(f"\n{i}. {opportunity.opportunity_name}")
            print(f"   Market Size: {opportunity.market_size}")
            print(f"   Feasibility: {opportunity.feasibility}")
            print(f"   Time to Market: {opportunity.time_to_market}")
            print(f"   Description: {opportunity.description}")
        
        # Risks and Challenges
        print(f"\n⚠️  RISKS & CHALLENGES")
        print("-" * 40)
        for i, risk in enumerate(report.risks_and_challenges, 1):
            print(f"{i}. {risk}")
        
        # Recommendations
        print(f"\n🎯 STRATEGIC RECOMMENDATIONS")
        print("-" * 40)
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")
        
        # Methodology and Sources
        print(f"\n📚 RESEARCH METHODOLOGY")
        print("-" * 40)
        print(report.research_methodology)
        
        print(f"\n📖 DATA SOURCES")
        print("-" * 40)
        for i, source in enumerate(report.data_sources, 1):
            print(f"{i}. {source}")
        
        print(f"\n⏰ Research conducted on: {report.timestamp}")
        print("="*80)

def main():
    """Main function to run the market research agent"""
    print("🔬 MARKET RESEARCH AGENT")
    print("="*50)
    
    # Get API key
    api_key = input("Enter your OpenAI API key (or press Enter if already set): ").strip()
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OpenAI API key is required. Please set it in your environment or provide it here.")
        return
    
    # Initialize agent
    agent = MarketResearchAgent(api_key)
    
    while True:
        print("\n" + "="*50)
        print("Choose an option:")
        print("1. Conduct market research on a topic")
        print("2. Load and display a saved report")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            topic = input("\nEnter the market research topic: ").strip()
            if topic:
                # Conduct research
                report = agent.conduct_research(topic)
                
                if report:
                    # Display the report
                    agent.display_report(report)
                    
                    # Ask if user wants to save
                    save_choice = input("\nWould you like to save this report? (y/n): ").strip().lower()
                    if save_choice in ['y', 'yes']:
                        filename = input("Enter filename (or press Enter for auto-generated name): ").strip()
                        if not filename:
                            filename = None
                        agent.save_report(report, filename)
        
        elif choice == "2":
            filename = input("Enter the filename of the saved report: ").strip()
            try:
                path = Path(filename)
                if not path.is_file():
                    alt = data_outputs_dir() / path.name
                    if alt.is_file():
                        path = alt
                with open(path, 'r') as f:
                    data = json.load(f)
                    report = MarketResearchReport(**data)
                    agent.display_report(report)
            except FileNotFoundError:
                print(f"❌ File '{filename}' not found.")
            except Exception as e:
                print(f"❌ Error loading report: {str(e)}")
        
        elif choice == "3":
            print("👋 Thank you for using the Market Research Agent!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
