# SinglePromptAgent.py - Enhanced Single-Prompt Market Research Agent
#
# This agent now emphasizes business context (description and vision/goal) as primary factors
# when creating customer personas and hypotheses. The analysis is specifically tailored to
# how the business can serve its target market and achieve its goals.

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_llm.bootstrap import bootstrap
from research_llm.config.settings import apply_langsmith_env

bootstrap()
apply_langsmith_env()

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
import json
import os

from research_llm.paths import data_outputs_dir

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
    import re
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    return cleaned_text.strip()


def get_business_context() -> tuple[str, str]:
    """Get and validate business context from user input"""

    print("\n=== BUSINESS CONTEXT ===")
    print("This information will be used to create personas and hypotheses that are specifically relevant to your business.")
    print("Please provide detailed information to get the most relevant analysis.\n")

    # Get business description
    business_description = input(
        "Enter a detailed description of your business (what you do, your products/services, target market): ").strip()

    if not business_description:
        business_description = "A business seeking market research insights"
        print("Using default business description.")

    # Get business vision/goal
    business_vision = input(
        "Enter your business vision/goal (what you want to achieve, your mission): ").strip()

    if not business_vision:
        business_vision = "To understand and serve the target market effectively"
        print("Using default business vision.")

    # Display summary for confirmation
    print(f"\nBusiness Context Summary:")
    print(f"Description: {business_description}")
    print(f"Vision/Goal: {business_vision}")

    # Ask for confirmation
    confirm = input("\nIs this correct? (y/n): ").lower().strip()
    if confirm != 'y':
        print("Let's try again...")
        return get_business_context()

    print()
    return business_description, business_vision


# Comprehensive single prompt for market research analysis
comprehensive_prompt = PromptTemplate(
    input_variables=["market_data", "business_description", "business_vision"],
    template="""
You are a market research expert and product strategist. Your task is to analyze market research data in the context of a specific business to generate actionable insights.

BUSINESS CONTEXT (Primary Factors to Consider):
Business Description: {business_description}
Business Vision/Goal: {business_vision}

MARKET RESEARCH DATA:
{market_data}

IMPORTANT: When creating personas and hypotheses, you MUST consider how they align with and support the business description and vision/goal. The personas should represent potential customers who would be interested in or benefit from this specific business. The hypotheses should be directly relevant to validating assumptions about how this business can serve its target market.

Your analysis should:

1. Generate 3 distinct customer personas that are specifically relevant to this business, and whom suffers the most from the problem we are trying to solve and who will need it the most.
2. Create 3-5 testable hypotheses about user needs/problems that this business could address
3. Recommend specific prototypes to validate each hypothesis
Please provide a comprehensive analysis in the following format:

=== CUSTOMER PERSONAS ===

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

=== HYPOTHESES ===

Based on the personas, market research, and business context, here are 3-5 testable hypotheses that are directly relevant to this business:

1. Hypothesis: [Specific, testable hypothesis about how this business can address user needs/problems]
2. Hypothesis: [Another specific hypothesis relevant to this business]
3. Hypothesis: [Another specific hypothesis relevant to this business]
4. Hypothesis: [Another specific hypothesis relevant to this business]
5. Hypothesis: [Another specific hypothesis relevant to this business]

=== PROTOTYPE RECOMMENDATIONS ===

For each hypothesis, here are specific prototype recommendations:

HYPOTHESIS 1: [Hypothesis text]
Prototype Recommendation:
• What to build/test: [Specific prototype or test]
• How to test it: [Testing methodology]
• What metrics to measure: [Key performance indicators]
• How to interpret results: [Success criteria]
• Timeline for testing: [Recommended timeline]
• Target persona segments: [Which personas to focus on]

HYPOTHESIS 2: [Hypothesis text]
Prototype Recommendation:
• What to build/test: [Specific prototype or test]
• How to test it: [Testing methodology]
• What metrics to measure: [Key performance indicators]
• How to interpret results: [Success criteria]
• Timeline for testing: [Recommended timeline]
• Target persona segments: [Which personas to focus on]

HYPOTHESIS 3: [Hypothesis text]
Prototype Recommendation:
• What to build/test: [Specific prototype or test]
• How to test it: [Testing methodology]
• What metrics to measure: [Key performance indicators]
• How to interpret results: [Success criteria]
• Timeline for testing: [Recommended timeline]
• Target persona segments: [Which personas to focus on]

HYPOTHESIS 4: [Hypothesis text]
Prototype Recommendation:
• What to build/test: [Specific prototype or test]
• How to test it: [Testing methodology]
• What metrics to measure: [Key performance indicators]
• How to interpret results: [Success criteria]
• Timeline for testing: [Recommended timeline]
• Target persona segments: [Which personas to focus on]

HYPOTHESIS 5: [Hypothesis text]
Prototype Recommendation:
• What to build/test: [Specific prototype or test]
• How to test it: [Testing methodology]
• What metrics to measure: [Key performance indicators]
• How to interpret results: [Success criteria]
• Timeline for testing: [Recommended timeline]
• Target persona segments: [Which personas to focus on]

=== SUMMARY ===

Key Insights (in relation to this business):
• [Insight 1 - how it relates to the business]
• [Insight 2 - how it relates to the business]
• [Insight 3 - how it relates to the business]

Next Steps (for this business):
• [Action item 1 - specific to this business]
• [Action item 2 - specific to this business]
• [Action item 3 - specific to this business]

Make sure each persona represents a different segment of the target market that would be interested in this specific business, with distinct characteristics, goals, and pain points that this business could address. The hypotheses should be specific and testable, directly relevant to validating how this business can serve its market, and the prototype recommendations should be actionable and focused on quick validation for this business.
"""
)


def analyze_market_research(market_data: str, business_description: str, business_vision: str):
    """Analyze market research and generate personas, hypotheses, and prototypes"""

    llm = ChatOpenAI(model_name="gpt-4o")
    chain = comprehensive_prompt | llm | StrOutputParser()

    print("=== MARKET RESEARCH ANALYSIS AGENT ===\n")
    print("Analyzing market research and generating comprehensive insights...")
    print("This may take a moment...\n")

    try:
        # Generate comprehensive analysis
        analysis = chain.invoke({
            "market_data": market_data,
            "business_description": business_description,
            "business_vision": business_vision
        })

        # Display the analysis
        print(analysis)

        # Save to file
        save_analysis(market_data, analysis,
                      business_description, business_vision)

        return analysis

    except Exception as e:
        print(f"Error during analysis: {e}")
        return None


def save_analysis(market_data: str, analysis: str, business_description: str, business_vision: str):
    """Save the analysis results to a file"""

    # Create a structured data object
    analysis_data = {
        "market_data": market_data,
        "business_description": business_description,
        "business_vision": business_vision,
        "analysis": analysis,
        "timestamp": "Generated by chat2.py"
    }

    out = data_outputs_dir() / "comprehensive_analysis.json"
    with open(out, "w") as f:
        json.dump(analysis_data, f, indent=4)

    print(f"\n=== ANALYSIS SAVED ===")
    print(f"Results saved to: {out}")


def interactive_mode(business_description: str, business_vision: str):
    """Interactive mode for custom market research input"""

    print("=== INTERACTIVE MARKET RESEARCH ANALYSIS ===\n")
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
                "College students aged 18-24, interested in eco-friendly fashion. ",
                "Frequently shop on Depop, prefer sustainable brands, ",
                "often discover products through TikTok influencers. ",
                "Price sensitive but value transparency and ethical production. ",
                "Major pain points include limited budget, difficulty finding stylish sustainable options, ",
                "and concerns about greenwashing in the fashion industry."
            ]
            break
        else:
            market_data_lines.append(line)

    if market_data_lines:
        market_data = " ".join(market_data_lines)
        print(f"\nAnalyzing market research: {market_data[:100]}...")
        analyze_market_research(
            market_data, business_description, business_vision)
    else:
        print("No market research data provided.")


def pdf_mode(business_description: str, business_vision: str):
    """Mode for analyzing market research from PDF files"""

    print("=== PDF MARKET RESEARCH ANALYSIS ===\n")

    if not PDF_AVAILABLE:
        print("PDF reading is not available. Please install PyPDF2:")
        print("pip install PyPDF2")
        return

    try:
        pdf_path = input("Enter the path to your PDF file: ").strip()

        if not pdf_path:
            print("No PDF path provided.")
            return

        # Extract text from PDF
        print(f"\nExtracting text from PDF: {pdf_path}")
        raw_text = extract_text_from_pdf(pdf_path)

        # Clean the extracted text
        print("Cleaning extracted text...")
        cleaned_text = clean_pdf_text(raw_text)

        # Show preview of extracted text
        preview_length = 300
        preview = cleaned_text[:preview_length] + \
            "..." if len(cleaned_text) > preview_length else cleaned_text
        print(f"\nExtracted text preview ({len(cleaned_text)} characters):")
        print("-" * 50)
        print(preview)
        print("-" * 50)

        # Ask user if they want to proceed
        proceed = input("\nProceed with analysis? (y/n): ").lower().strip()

        if proceed == 'y':
            print(f"\nAnalyzing market research from PDF...")
            analyze_market_research(
                cleaned_text, business_description, business_vision)
        else:
            print("Analysis cancelled.")

    except Exception as e:
        print(f"Error processing PDF: {e}")


def main():
    """Main function to run the comprehensive market research agent"""

    print("Comprehensive Market Research Agent")
    print("1. Use sample market research data")
    print("2. Enter custom market research data")
    print("3. Load market research from text file")
    if PDF_AVAILABLE:
        print("4. Load market research from PDF file")

    # Get business context
    business_description, business_vision = get_business_context()

    choice = input(
        f"\nChoose option (1-{4 if PDF_AVAILABLE else 3}): ").strip()

    if choice == "1":
        # Use sample data
        sample_market_data = (
            "College students aged 18-24, interested in eco-friendly fashion. "
            "Frequently shop on Depop, prefer sustainable brands, "
            "often discover products through TikTok influencers. "
            "Price sensitive but value transparency and ethical production. "
            "Major pain points include limited budget, difficulty finding stylish sustainable options, "
            "and concerns about greenwashing in the fashion industry."
        )
        analyze_market_research(
            sample_market_data, business_description, business_vision)

    elif choice == "2":
        # Interactive mode
        interactive_mode(business_description, business_vision)

    elif choice == "3":
        # Load from text file
        try:
            filename = input(
                "Enter filename (e.g., market_data.txt): ").strip()
            with open(filename, "r") as f:
                market_data = f.read()
            analyze_market_research(
                market_data, business_description, business_vision)
        except FileNotFoundError:
            print(f"File '{filename}' not found.")
        except Exception as e:
            print(f"Error reading file: {e}")

    elif choice == "4" and PDF_AVAILABLE:
        # Load from PDF file
        pdf_mode(business_description, business_vision)

    else:
        print("Invalid choice. Using sample data...")
        sample_market_data = (
            "College students aged 18-24, interested in eco-friendly fashion. "
            "Frequently shop on Depop, prefer sustainable brands, "
            "often discover products through TikTok influencers. "
            "Price sensitive but value transparency and ethical production."
        )
        analyze_market_research(
            sample_market_data, business_description, business_vision)


if __name__ == "__main__":
    main()
