# ImprovementResearch.py - General Improvement and Enhancement Research Agent
#
# This agent focuses on analyzing any topic, system, process, or entity to identify improvement opportunities,
# enhancements, and ways to elevate it to better serve its purpose and achieve better outcomes.
# It's designed to help researchers, analysts, and decision-makers make data-driven decisions about
# improvement and evolution of any subject matter.

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


class StakeholderSegment(BaseModel):
    """Represents a stakeholder segment with their specific needs and pain points"""
    name: str = Field(description="Name of the stakeholder segment")
    description: str = Field(
        description="Description of this stakeholder segment")
    current_satisfaction_level: str = Field(
        description="Current satisfaction level with the subject (High/Medium/Low)")
    key_needs: List[str] = Field(
        description="Key needs and requirements of this segment")
    pain_points: List[str] = Field(
        description="Pain points and frustrations with current state")
    usage_patterns: List[str] = Field(
        description="How this segment currently interacts with or uses the subject")
    improvement_priorities: List[str] = Field(
        description="What improvements would be most valuable to this segment")


class Enhancement(BaseModel):
    """Represents a potential enhancement or improvement"""
    enhancement_name: str = Field(description="Name of the enhancement")
    description: str = Field(
        description="Detailed description of the enhancement")
    target_stakeholder_segments: List[str] = Field(
        description="Stakeholder segments this enhancement would benefit")
    impact_score: str = Field(
        description="Expected impact score (High/Medium/Low)")
    implementation_complexity: str = Field(
        description="Implementation complexity (High/Medium/Low)")
    effort_required: str = Field(
        description="Estimated effort required (weeks/months)")
    value_proposition: str = Field(description="Expected value and benefits")
    requirements: List[str] = Field(
        description="Requirements and considerations for implementation")


class Advantage(BaseModel):
    """Represents an advantage or differentiation opportunity"""
    advantage_name: str = Field(
        description="Name of the advantage")
    description: str = Field(
        description="Description of how this creates advantage or differentiation")
    target_comparisons: List[str] = Field(
        description="What this would help differentiate from or improve upon")
    positioning: str = Field(
        description="How this positions the subject in its context")
    differentiation_factors: List[str] = Field(
        description="Key differentiation factors")
    sustainability: str = Field(
        description="How sustainable this advantage is (Long-term/Medium-term/Short-term)")


class Gap(BaseModel):
    """Represents a gap or opportunity in the current state"""
    gap_name: str = Field(description="Name of the gap or opportunity")
    description: str = Field(
        description="Description of the gap or opportunity")
    stakeholder_impact: str = Field(
        description="Impact on stakeholders (High/Medium/Low)")
    opportunity_size: str = Field(
        description="Size and potential of the opportunity")
    urgency: str = Field(
        description="Urgency to address this gap (High/Medium/Low)")
    potential_solutions: List[str] = Field(
        description="Potential solutions to address this gap")


class Trend(BaseModel):
    """Represents a trend or innovation that could enhance the subject"""
    trend_name: str = Field(description="Name of the trend or innovation")
    description: str = Field(
        description="Description of the trend and its relevance")
    applicability: str = Field(
        description="How applicable this trend is to the subject (High/Medium/Low)")
    implementation_timeline: str = Field(
        description="Recommended timeline for implementation")
    potential_benefits: List[str] = Field(
        description="Potential benefits of adopting this trend")
    risks_and_challenges: List[str] = Field(
        description="Risks and challenges of implementation")


class ImprovementReport(BaseModel):
    """Complete improvement research report"""
    subject_name: str = Field(description="Name of the subject being analyzed")
    current_state: str = Field(
        description="Current state and description of the subject")
    executive_summary: str = Field(
        description="Executive summary of improvement opportunities")
    subject_overview: str = Field(
        description="Overview of current capabilities and limitations")
    stakeholder_segments: List[StakeholderSegment] = Field(
        description="Key stakeholder segments and their needs")
    enhancements: List[Enhancement] = Field(
        description="Recommended enhancements")
    advantages: List[Advantage] = Field(
        description="Opportunities for advantage or differentiation")
    gaps: List[Gap] = Field(
        description="Identified gaps and opportunities")
    trends: List[Trend] = Field(
        description="Relevant trends and innovations for enhancement")
    implementation_roadmap: List[str] = Field(
        description="Recommended implementation roadmap")
    success_metrics: List[str] = Field(
        description="Key metrics to measure improvement success")
    risks_and_considerations: List[str] = Field(
        description="Risks and considerations for improvements")
    research_methodology: str = Field(
        description="Methodology used for this research")
    data_sources: List[str] = Field(
        description="Sources of data and information")
    timestamp: str = Field(description="When this research was conducted")


class ImprovementAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Improvement Research Agent"""
        s = get_settings()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif s.openai_api_key:
            os.environ["OPENAI_API_KEY"] = s.openai_api_key

        self.llm = ChatOpenAI(
            temperature=0.3, model_name=s.openai_model_synthesis
        )
        self.parser = PydanticOutputParser(
            pydantic_object=ImprovementReport)

        # Create the main research prompt
        self.research_prompt = PromptTemplate(
            input_variables=["subject_name", "format_instructions"],
            template="""
You are an expert analyst and strategist with 15+ years of experience in improvement and enhancement across various domains. 
Your task is to analyze the given subject and identify comprehensive improvement opportunities to elevate it to the next level.

Subject Name: {subject_name}

Based on the subject name, you should:
1. Understand what type of subject this is (product, process, system, service, organization, etc.)
2. Research and analyze the current state and common challenges in this domain
3. Identify improvement opportunities and enhancement strategies

Please conduct thorough improvement research and provide a comprehensive analysis including:

1. Executive Summary - Key improvement opportunities and strategic direction
2. Subject Overview - Current state, strengths, and limitations
3. Stakeholder Segments - Detailed analysis of stakeholder segments and their specific needs
4. Enhancements - Specific improvements and new capabilities
5. Advantages - Opportunities to differentiate and gain advantage
6. Gaps - Identified gaps and opportunities for improvement
7. Trends - Relevant trends and innovations that could enhance the subject
8. Implementation Roadmap - Strategic roadmap for implementing improvements
9. Success Metrics - How to measure the success of improvements
10. Risks & Considerations - Potential risks and mitigation strategies

Focus on:
- Stakeholder experience improvements
- Enhancements that solve real problems
- Differentiation opportunities
- Innovation adoption that provides real value
- Scalable and sustainable improvements
- Data-driven recommendations

Use the following format for your response:
{format_instructions}

Provide detailed, actionable insights that can guide improvement decisions. Be specific about implementation priorities, stakeholder impact, and value proposition. Base your analysis on the subject name and your knowledge of similar subjects in that domain.
"""
        )

    def conduct_improvement_research(self, subject_name: str) -> ImprovementReport:
        """Conduct comprehensive improvement research"""
        print(f"🔍 Conducting improvement research on: {subject_name}")
        print("⏳ This may take a few moments...")

        try:
            # Get the format instructions
            format_instructions = self.parser.get_format_instructions()

            # Create the prompt
            prompt = self.research_prompt.format(
                subject_name=subject_name,
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

    def save_report(self, report: ImprovementReport, filename: str = None) -> str:
        """Save the improvement report to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject_name = re.sub(
                r'[^a-zA-Z0-9\s]', '', report.subject_name).replace(' ', '_')
            filename = f"improvement_research_{safe_subject_name}_{timestamp}.json"

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

    def display_report(self, report: ImprovementReport):
        """Display the improvement report in a formatted way"""
        print("\n" + "="*80)
        print(f"🚀 IMPROVEMENT RESEARCH REPORT: {report.subject_name.upper()}")
        print("="*80)

        # Executive Summary
        print(f"\n📋 EXECUTIVE SUMMARY")
        print("-" * 40)
        print(report.executive_summary)

        # Subject Overview
        print(f"\n📱 SUBJECT OVERVIEW")
        print("-" * 40)
        print(report.subject_overview)

        # Stakeholder Segments
        print(f"\n👥 STAKEHOLDER SEGMENTS")
        print("-" * 40)
        for i, segment in enumerate(report.stakeholder_segments, 1):
            print(f"\n{i}. {segment.name}")
            print(f"   Description: {segment.description}")
            print(
                f"   Current Satisfaction: {segment.current_satisfaction_level}")
            print(f"   Key Needs:")
            for need in segment.key_needs:
                print(f"     • {need}")
            print(f"   Pain Points:")
            for pain in segment.pain_points:
                print(f"     • {pain}")
            print(f"   Usage Patterns:")
            for pattern in segment.usage_patterns:
                print(f"     • {pattern}")
            print(f"   Improvement Priorities:")
            for priority in segment.improvement_priorities:
                print(f"     • {priority}")

        # Enhancements
        print(f"\n⚡ ENHANCEMENTS")
        print("-" * 40)
        for i, enhancement in enumerate(report.enhancements, 1):
            print(f"\n{i}. {enhancement.enhancement_name}")
            print(f"   Description: {enhancement.description}")
            print(
                f"   Target Stakeholders: {', '.join(enhancement.target_stakeholder_segments)}")
            print(f"   Impact Score: {enhancement.impact_score}")
            print(
                f"   Implementation Complexity: {enhancement.implementation_complexity}")
            print(f"   Effort Required: {enhancement.effort_required}")
            print(f"   Value Proposition: {enhancement.value_proposition}")
            print(f"   Requirements:")
            for req in enhancement.requirements:
                print(f"     • {req}")

        # Advantages
        print(f"\n🏆 ADVANTAGES")
        print("-" * 40)
        for i, advantage in enumerate(report.advantages, 1):
            print(f"\n{i}. {advantage.advantage_name}")
            print(f"   Description: {advantage.description}")
            print(
                f"   Target Comparisons: {', '.join(advantage.target_comparisons)}")
            print(f"   Positioning: {advantage.positioning}")
            print(f"   Differentiation Factors:")
            for factor in advantage.differentiation_factors:
                print(f"     • {factor}")
            print(f"   Sustainability: {advantage.sustainability}")

        # Gaps
        print(f"\n🕳️  GAPS")
        print("-" * 40)
        for i, gap in enumerate(report.gaps, 1):
            print(f"\n{i}. {gap.gap_name}")
            print(f"   Description: {gap.description}")
            print(f"   Stakeholder Impact: {gap.stakeholder_impact}")
            print(f"   Opportunity Size: {gap.opportunity_size}")
            print(f"   Urgency: {gap.urgency}")
            print(f"   Potential Solutions:")
            for solution in gap.potential_solutions:
                print(f"     • {solution}")

        # Trends
        print(f"\n🔬 TRENDS")
        print("-" * 40)
        for i, trend in enumerate(report.trends, 1):
            print(f"\n{i}. {trend.trend_name}")
            print(f"   Description: {trend.description}")
            print(f"   Applicability: {trend.applicability}")
            print(
                f"   Implementation Timeline: {trend.implementation_timeline}")
            print(f"   Potential Benefits:")
            for benefit in trend.potential_benefits:
                print(f"     • {benefit}")
            print(f"   Risks and Challenges:")
            for risk in trend.risks_and_challenges:
                print(f"     • {risk}")

        # Implementation Roadmap
        print(f"\n🗺️  IMPLEMENTATION ROADMAP")
        print("-" * 40)
        for i, step in enumerate(report.implementation_roadmap, 1):
            print(f"{i}. {step}")

        # Success Metrics
        print(f"\n📊 SUCCESS METRICS")
        print("-" * 40)
        for i, metric in enumerate(report.success_metrics, 1):
            print(f"{i}. {metric}")

        # Risks and Considerations
        print(f"\n⚠️  RISKS & CONSIDERATIONS")
        print("-" * 40)
        for i, risk in enumerate(report.risks_and_considerations, 1):
            print(f"{i}. {risk}")

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

    def export_for_other_agents(self, report: ImprovementReport, filename: str = None) -> str:
        """Export research data in a format suitable for other agents"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject_name = re.sub(
                r'[^a-zA-Z0-9\s]', '', report.subject_name).replace(' ', '_')
            filename = f"improvement_data_{safe_subject_name}_{timestamp}.json"

        try:
            out_path = Path(filename)
            if not out_path.is_absolute():
                out_path = data_outputs_dir() / out_path.name
            # Create a simplified export format for other agents
            export_data = {
                "subject_name": report.subject_name,
                "current_state": report.current_state,
                "executive_summary": report.executive_summary,
                "stakeholder_segments": [
                    {
                        "name": segment.name,
                        "description": segment.description,
                        "pain_points": segment.pain_points,
                        "improvement_priorities": segment.improvement_priorities
                    } for segment in report.stakeholder_segments
                ],
                "enhancements": [
                    {
                        "name": enhancement.enhancement_name,
                        "description": enhancement.description,
                        "impact_score": enhancement.impact_score,
                        "value_proposition": enhancement.value_proposition
                    } for enhancement in report.enhancements
                ],
                "gaps": [
                    {
                        "name": gap.gap_name,
                        "description": gap.description,
                        "urgency": gap.urgency,
                        "potential_solutions": gap.potential_solutions
                    } for gap in report.gaps
                ],
                "implementation_roadmap": report.implementation_roadmap,
                "success_metrics": report.success_metrics,
                "timestamp": report.timestamp,
                "export_format": "improvement_research_data"
            }

            with open(out_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"✅ Export data saved to: {out_path}")
            return str(out_path)
        except Exception as e:
            print(f"❌ Error exporting data: {str(e)}")
            return None


def main():
    """Main function to run the improvement research agent"""
    print("🚀 IMPROVEMENT RESEARCH AGENT")
    print("="*50)

    # Get API key
    api_key = input(
        "Enter your OpenAI API key (or press Enter if already set): ").strip()
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("❌ OpenAI API key is required. Please set it in your environment or provide it here.")
        return

    # Initialize agent
    agent = ImprovementAgent(api_key)

    while True:
        print("\n" + "="*50)
        print("Choose an option:")
        print("1. Conduct improvement research")
        print("2. Load and display a saved report")
        print("3. Export research data for other agents")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            subject_name = input(
                "\nEnter the subject name (e.g., mobile app, customer service process, IT system, healthcare service): ").strip()
            if not subject_name:
                print("❌ Subject name is required.")
                continue

            print(f"\nAnalyzing subject: {subject_name}")
            print("The agent will automatically research and analyze improvement opportunities based on the subject name.")

            # Conduct research
            report = agent.conduct_improvement_research(subject_name)

            if report:
                # Display the report
                agent.display_report(report)

                # Ask if user wants to save
                save_choice = input(
                    "\nWould you like to save this report? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = input(
                        "Enter filename (or press Enter for auto-generated name): ").strip()
                    if not filename:
                        filename = None
                    agent.save_report(report, filename)

        elif choice == "2":
            filename = input(
                "Enter the filename of the saved report: ").strip()
            try:
                path = Path(filename)
                if not path.is_file():
                    alt = data_outputs_dir() / path.name
                    if alt.is_file():
                        path = alt
                with open(path, 'r') as f:
                    data = json.load(f)
                    report = ImprovementReport(**data)
                    agent.display_report(report)
            except FileNotFoundError:
                print(f"❌ File '{filename}' not found.")
            except Exception as e:
                print(f"❌ Error loading report: {str(e)}")

        elif choice == "3":
            filename = input(
                "Enter the filename of the saved report to export: ").strip()
            try:
                path = Path(filename)
                if not path.is_file():
                    alt = data_outputs_dir() / path.name
                    if alt.is_file():
                        path = alt
                with open(path, 'r') as f:
                    data = json.load(f)
                    report = ImprovementReport(**data)

                export_filename = input(
                    "Enter export filename (or press Enter for auto-generated name): ").strip()
                if not export_filename:
                    export_filename = None

                agent.export_for_other_agents(report, export_filename)
            except FileNotFoundError:
                print(f"❌ File '{filename}' not found.")
            except Exception as e:
                print(f"❌ Error loading report: {str(e)}")

        elif choice == "4":
            print("👋 Thank you for using the Improvement Research Agent!")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
