# WebImprovementResearch.py - Web-Based Improvement Research Agent
#
# This agent conducts web research to find information about how to improve any subject,
# system, process, or entity. It searches the web for improvement strategies, best practices,
# case studies, and expert insights to provide comprehensive improvement recommendations.

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import json
import requests
from typing import Dict, List, Any, Optional
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
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse, quote_plus
import urllib.parse
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import trafilatura
try:
    from newspaper import Article
except ImportError:
    from newspaper3k import Article
import nltk
from nltk.tokenize import sent_tokenize
import hashlib
import random

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class WebSource(BaseModel):
    """Represents a web source with extracted content"""
    url: str = Field(description="Source URL")
    title: str = Field(description="Page title")
    content: str = Field(description="Extracted content")
    source_type: str = Field(
        description="Type of source (article, case study, guide, research paper, etc.)")
    date_published: Optional[str] = Field(
        description="Publication date if available")
    relevance_score: float = Field(description="Relevance score (0-1)")
    word_count: int = Field(description="Number of words in content")


class StakeholderSegment(BaseModel):
    """Represents a stakeholder segment with their specific needs and pain points"""
    name: str = Field(description="Name of the stakeholder segment")
    description: str = Field(description="Description of this stakeholder segment")
    current_satisfaction_level: str = Field(
        description="Current satisfaction level with the subject (High/Medium/Low)")
    key_needs: List[str] = Field(
        description="Key needs and requirements of this segment")
    pain_points: List[str] = Field(
        description="Pain points and frustrations with current state")
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


class WebImprovementReport(BaseModel):
    """Complete web-based improvement research report"""
    subject_name: str = Field(description="The subject being analyzed for improvement")
    executive_summary: str = Field(
        description="Executive summary of improvement opportunities")
    current_state: str = Field(
        description="Current state and description of the subject")
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
    data_sources: List[WebSource] = Field(
        description="Web sources used for research")
    key_findings: List[str] = Field(
        description="Key findings from web research")
    timestamp: str = Field(description="When this research was conducted")


class WebImprovementAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Web Improvement Research Agent"""
        s = get_settings()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif s.openai_api_key:
            os.environ["OPENAI_API_KEY"] = s.openai_api_key

        self.llm = ChatOpenAI(
            temperature=0.3, model_name=s.openai_model_synthesis
        )
        self.parser = PydanticOutputParser(pydantic_object=WebImprovementReport)
        
        # Create the main research prompt
        self.research_prompt = PromptTemplate(
            input_variables=["subject_name", "web_sources_summary", "format_instructions"],
            template="""
You are an expert analyst and strategist with 15+ years of experience in improvement and enhancement across various domains. 
Your task is to analyze the given subject and identify comprehensive improvement opportunities based on web research.

Subject Name: {subject_name}

Web Research Sources:
{web_sources_summary}

Based on the web research data provided, please conduct thorough improvement analysis and provide a comprehensive report including:

1. Executive Summary - Key improvement opportunities and strategic direction
2. Current State - Current state and description of the subject
3. Subject Overview - Overview of current capabilities and limitations
4. Stakeholder Segments - Detailed analysis of stakeholder segments and their specific needs
5. Enhancements - Specific improvements and new capabilities
6. Advantages - Opportunities to differentiate and gain advantage
7. Gaps - Identified gaps and opportunities for improvement
8. Trends - Relevant trends and innovations that could enhance the subject
9. Implementation Roadmap - Strategic roadmap for implementing improvements
10. Success Metrics - How to measure the success of improvements
11. Risks & Considerations - Potential risks and mitigation strategies
12. Key Findings - Key findings from web research

Focus on:
- Stakeholder experience improvements
- Enhancements that solve real problems
- Differentiation opportunities
- Innovation adoption that provides real value
- Scalable and sustainable improvements
- Data-driven recommendations based on web research

Use the following format for your response:
{format_instructions}

Provide detailed, actionable insights that can guide improvement decisions. Be specific about implementation priorities, stakeholder impact, and value proposition. Base your analysis on the web research data provided.
"""
        )
    
    def generate_search_queries(self, subject_name: str) -> List[str]:
        """Generate search queries for web research"""
        queries = [
            f"how to improve {subject_name}",
            f"{subject_name} improvement strategies",
            f"{subject_name} best practices",
            f"{subject_name} optimization techniques",
            f"{subject_name} enhancement methods",
            f"{subject_name} case studies improvement",
            f"{subject_name} performance optimization",
            f"{subject_name} efficiency improvements",
            f"{subject_name} innovation opportunities",
            f"{subject_name} stakeholder satisfaction",
            f"{subject_name} problem solving",
            f"{subject_name} quality improvement",
            f"{subject_name} modernization strategies",
            f"{subject_name} digital transformation",
            f"{subject_name} user experience improvement"
        ]
        return queries
    
    def search_web(self, query: str, max_results: int = 5) -> List[str]:
        """Search the web for relevant URLs"""
        print(f"🔍 Searching for: {query}")
        
        # Try multiple search engines
        urls = []
        
        # Try DuckDuckGo first
        try:
            urls = self._search_duckduckgo(query, max_results)
            if urls:
                return urls
        except Exception as e:
            print(f"⚠️  DuckDuckGo search failed: {e}")
        
        # Try alternative methods
        urls = self._search_with_alternative_methods(query, max_results)
        
        return urls[:max_results]
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[str]:
        """Search using DuckDuckGo"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_duckduckgo_results(soup, max_results)
            
        except Exception as e:
            print(f"Error searching DuckDuckGo: {e}")
            return []
    
    def _search_with_alternative_methods(self, query: str, max_results: int = 10) -> List[str]:
        """Use alternative search methods when primary search fails"""
        urls = []
        
        # Try Bing
        try:
            urls = self._search_bing(query, max_results)
            if urls:
                return urls
        except Exception as e:
            print(f"⚠️  Bing search failed: {e}")
        
        # Try Yahoo
        try:
            urls = self._search_yahoo(query, max_results)
            if urls:
                return urls
        except Exception as e:
            print(f"⚠️  Yahoo search failed: {e}")
        
        # Use curated URLs as fallback
        urls = self._get_curated_urls(query)
        
        return urls[:max_results]
    
    def _search_bing(self, query: str, max_results: int) -> List[str]:
        """Search using Bing"""
        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_bing_results(soup, max_results)
            
        except Exception as e:
            print(f"Error searching Bing: {e}")
            return []
    
    def _search_yahoo(self, query: str, max_results: int) -> List[str]:
        """Search using Yahoo"""
        try:
            url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_yahoo_results(soup, max_results)
            
        except Exception as e:
            print(f"Error searching Yahoo: {e}")
            return []
    
    def _parse_duckduckgo_results(self, soup: BeautifulSoup, max_results: int) -> List[str]:
        """Parse DuckDuckGo search results"""
        urls = []
        
        # Look for result links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/l/?uddg='):
                # Extract the actual URL from DuckDuckGo's redirect
                try:
                    actual_url = href.split('uddg=')[1]
                    actual_url = urllib.parse.unquote(actual_url)
                    if self._is_valid_url(actual_url):
                        urls.append(actual_url)
                except:
                    continue
            elif href.startswith('http') and self._is_valid_url(href):
                urls.append(href)
        
        return urls[:max_results]
    
    def _parse_bing_results(self, soup: BeautifulSoup, max_results: int) -> List[str]:
        """Parse Bing search results"""
        urls = []
        
        # Look for result links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') and self._is_valid_url(href):
                urls.append(href)
        
        return urls[:max_results]
    
    def _parse_yahoo_results(self, soup: BeautifulSoup, max_results: int) -> List[str]:
        """Parse Yahoo search results"""
        urls = []
        
        # Look for result links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') and self._is_valid_url(href):
                urls.append(href)
        
        return urls[:max_results]
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not a search engine or social media"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Exclude search engines and social media
            excluded_domains = [
                'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com',
                'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
                'youtube.com', 'reddit.com', 'pinterest.com'
            ]
            
            for excluded in excluded_domains:
                if excluded in domain:
                    return False
            
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def _get_curated_urls(self, query: str) -> List[str]:
        """Get curated URLs based on the query topic"""
        # This is a fallback method that provides relevant URLs based on common improvement topics
        curated_urls = {
            'customer service': [
                'https://www.zendesk.com/blog/customer-service-improvement/',
                'https://www.hubspot.com/service/customer-service-improvement',
                'https://www.forbes.com/sites/forbescoachescouncil/2020/01/27/15-ways-to-improve-customer-service/'
            ],
            'process': [
                'https://www.process.st/process-improvement/',
                'https://www.lucidchart.com/blog/process-improvement-methodologies',
                'https://www.isixsigma.com/methodology/process-improvement/'
            ],
            'system': [
                'https://www.gartner.com/en/documents/3991344/system-optimization-best-practices',
                'https://www.techrepublic.com/article/how-to-optimize-your-it-systems/',
                'https://www.cio.com/article/3205971/system-optimization-strategies.html'
            ],
            'product': [
                'https://www.productplan.com/product-improvement/',
                'https://www.intercom.com/blog/product-improvement-strategies/',
                'https://www.producthunt.com/stories/product-improvement-guide'
            ],
            'service': [
                'https://www.service-design-network.org/improvement',
                'https://www.servicedesign.org/service-improvement',
                'https://www.cx-journey.com/service-improvement'
            ],
            'organization': [
                'https://www.mckinsey.com/capabilities/people-and-organizational-performance',
                'https://hbr.org/topic/organizational-improvement',
                'https://www.bain.com/insights/organizational-transformation/'
            ]
        }
        
        # Find relevant curated URLs based on query keywords
        query_lower = query.lower()
        relevant_urls = []
        
        for keyword, urls in curated_urls.items():
            if keyword in query_lower:
                relevant_urls.extend(urls)
        
        return relevant_urls[:5]  # Return up to 5 relevant URLs
    
    def extract_content_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a URL using multiple methods"""
        print(f"📄 Extracting content from: {url}")
        
        try:
            # Method 1: Try newspaper3k
            try:
                article = Article(url)
                article.download()
                article.parse()
                article.nlp()
                
                if article.text and len(article.text) > 100:
                    return {
                        'title': article.title or 'No title',
                        'content': article.text,
                        'date_published': article.publish_date.isoformat() if article.publish_date else None,
                        'method': 'newspaper3k'
                    }
            except Exception as e:
                print(f"⚠️  Newspaper3k failed: {e}")
            
            # Method 2: Try trafilatura
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                extracted_text = trafilatura.extract(response.text)
                if extracted_text and len(extracted_text) > 100:
                    return {
                        'title': 'Extracted content',
                        'content': extracted_text,
                        'date_published': None,
                        'method': 'trafilatura'
                    }
            except Exception as e:
                print(f"⚠️  Trafilatura failed: {e}")
            
            # Method 3: Try BeautifulSoup
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                if text and len(text) > 100:
                    return {
                        'title': soup.title.string if soup.title else 'No title',
                        'content': text,
                        'date_published': None,
                        'method': 'beautifulsoup'
                    }
            except Exception as e:
                print(f"⚠️  BeautifulSoup failed: {e}")
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting content from {url}: {e}")
            return None
    
    def _generate_fallback_content(self, subject_name: str) -> List[WebSource]:
        """Generate fallback content when web scraping fails"""
        print("⚠️  Using fallback content generation...")
        
        fallback_sources = []
        
        # Generate different types of improvement content
        improvement_areas = [
            "stakeholder analysis",
            "enhancement strategies", 
            "gap identification",
            "trend analysis",
            "implementation planning"
        ]
        
        for i, area in enumerate(improvement_areas):
            content = self._generate_research_content(subject_name, area, i)
            if content:
                fallback_sources.append(WebSource(
                    url=f"generated://{area.replace(' ', '_')}",
                    title=content['title'],
                    content=content['content'],
                    source_type="generated_analysis",
                    date_published=datetime.now().isoformat(),
                    relevance_score=0.8,
                    word_count=len(content['content'].split())
                ))
        
        return fallback_sources
    
    def assess_relevance(self, subject_name: str, content: str) -> float:
        """Assess the relevance of content to the improvement research"""
        try:
            # Simple keyword-based relevance scoring
            improvement_keywords = [
                'improve', 'enhance', 'optimize', 'better', 'upgrade',
                'efficiency', 'effectiveness', 'performance', 'quality',
                'best practice', 'strategy', 'solution', 'innovation',
                'transformation', 'modernization', 'optimization'
            ]
            
            content_lower = content.lower()
            score = 0.0
            
            for keyword in improvement_keywords:
                if keyword in content_lower:
                    score += 0.1
            
            # Also check for subject-specific keywords
            subject_words = subject_name.lower().split()
            for word in subject_words:
                if word in content_lower:
                    score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            print(f"Error assessing relevance: {e}")
            return 0.5
    
    def gather_web_sources(self, subject_name: str, max_sources: int = 20) -> List[WebSource]:
        """Gather web sources for improvement research"""
        print(f"🌐 Gathering web sources for: {subject_name}")
        
        all_sources = []
        queries = self.generate_search_queries(subject_name)
        
        for query in queries[:5]:  # Use first 5 queries
            try:
                urls = self.search_web(query, max_results=4)
                
                for url in urls:
                    if len(all_sources) >= max_sources:
                        break
                    
                    # Skip if we already have this URL
                    if any(source.url == url for source in all_sources):
                        continue
                    
                    content_data = self.extract_content_from_url(url)
                    if content_data:
                        relevance = self.assess_relevance(subject_name, content_data['content'])
                        
                        if relevance > 0.3:  # Only include relevant content
                            source = WebSource(
                                url=url,
                                title=content_data['title'],
                                content=content_data['content'],
                                source_type=self._classify_source_type(url, content_data['title']),
                                date_published=content_data['date_published'],
                                relevance_score=relevance,
                                word_count=len(content_data['content'].split())
                            )
                            all_sources.append(source)
                            print(f"✅ Added source: {content_data['title'][:50]}...")
                    
                    time.sleep(1)  # Be respectful to servers
                    
            except Exception as e:
                print(f"❌ Error processing query '{query}': {e}")
                continue
        
        # If we don't have enough sources, generate fallback content
        if len(all_sources) < 5:
            print("⚠️  Not enough web sources found, generating fallback content...")
            fallback_sources = self._generate_fallback_content(subject_name)
            all_sources.extend(fallback_sources)
        
        # Sort by relevance and return top sources
        all_sources.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_sources[:max_sources]
    
    def _generate_research_content(self, subject_name: str, area: str, index: int) -> Dict[str, Any]:
        """Generate research content for a specific improvement area"""
        try:
            # Create a prompt for generating improvement research content
            prompt = f"""
Generate comprehensive improvement research content for {subject_name} focusing on {area}.

Please provide:
1. A detailed analysis of current challenges and opportunities
2. Specific improvement strategies and recommendations
3. Best practices and case studies
4. Implementation considerations
5. Expected outcomes and benefits

Make the content informative, actionable, and based on improvement research principles.
"""
            
            response = self.llm.invoke(prompt)
            
            return {
                'title': f"{subject_name.title()} - {area.title()} Analysis",
                'content': response.content
            }
            
        except Exception as e:
            print(f"Error generating content for {area}: {e}")
            return None
    
    def _classify_source_type(self, url: str, title: str) -> str:
        """Classify the type of source based on URL and title"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if any(word in url_lower or word in title_lower for word in ['research', 'study', 'paper']):
            return 'research_paper'
        elif any(word in url_lower or word in title_lower for word in ['case', 'study']):
            return 'case_study'
        elif any(word in url_lower or word in title_lower for word in ['guide', 'how-to', 'tutorial']):
            return 'guide'
        elif any(word in url_lower or word in title_lower for word in ['blog', 'post', 'article']):
            return 'article'
        elif any(word in url_lower or word in title_lower for word in ['news', 'report']):
            return 'news'
        else:
            return 'web_content'
    
    def create_sources_summary(self, sources: List[WebSource]) -> str:
        """Create a summary of web sources for the research prompt"""
        if not sources:
            return "No web sources available."
        
        summary = "Web Research Sources:\n\n"
        
        for i, source in enumerate(sources, 1):
            summary += f"Source {i}: {source.title}\n"
            summary += f"URL: {source.url}\n"
            summary += f"Type: {source.source_type}\n"
            summary += f"Relevance: {source.relevance_score:.2f}\n"
            summary += f"Content Preview: {source.content[:300]}...\n\n"
        
        return summary
    
    def conduct_web_research(self, subject_name: str) -> WebImprovementReport:
        """Conduct comprehensive web-based improvement research"""
        print(f"🔍 Conducting web-based improvement research on: {subject_name}")
        print("⏳ This may take a few moments...")
        
        try:
            # Gather web sources
            sources = self.gather_web_sources(subject_name)
            print(f"📚 Found {len(sources)} relevant web sources")
            
            # Create sources summary
            sources_summary = self.create_sources_summary(sources)
            
            # Get format instructions
            format_instructions = self.parser.get_format_instructions()
            
            # Create the research prompt
            prompt = self.research_prompt.format(
                subject_name=subject_name,
                web_sources_summary=sources_summary,
                format_instructions=format_instructions
            )
            
            # Run the research
            response = self.llm.invoke(prompt)
            
            # Parse the response
            report = self.parser.parse(response.content)
            report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.data_sources = sources
            
            return report
            
        except Exception as e:
            print(f"❌ Error conducting web research: {str(e)}")
            return None
    
    def save_report(self, report: WebImprovementReport, filename: str = None) -> str:
        """Save the web improvement research report to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject_name = re.sub(r'[^a-zA-Z0-9\s]', '', report.subject_name).replace(' ', '_')
            filename = f"web_improvement_research_{safe_subject_name}_{timestamp}.json"

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
    
    def display_report(self, report: WebImprovementReport):
        """Display the web improvement research report in a formatted way"""
        print("\n" + "="*80)
        print(f"🌐 WEB IMPROVEMENT RESEARCH REPORT: {report.subject_name.upper()}")
        print("="*80)
        
        # Executive Summary
        print(f"\n📋 EXECUTIVE SUMMARY")
        print("-" * 40)
        print(report.executive_summary)
        
        # Current State
        print(f"\n📱 CURRENT STATE")
        print("-" * 40)
        print(report.current_state)
        
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
            print(f"   Current Satisfaction: {segment.current_satisfaction_level}")
            print(f"   Key Needs:")
            for need in segment.key_needs:
                print(f"     • {need}")
            print(f"   Pain Points:")
            for pain in segment.pain_points:
                print(f"     • {pain}")
            print(f"   Improvement Priorities:")
            for priority in segment.improvement_priorities:
                print(f"     • {priority}")
        
        # Enhancements
        print(f"\n⚡ ENHANCEMENTS")
        print("-" * 40)
        for i, enhancement in enumerate(report.enhancements, 1):
            print(f"\n{i}. {enhancement.enhancement_name}")
            print(f"   Description: {enhancement.description}")
            print(f"   Target Stakeholders: {', '.join(enhancement.target_stakeholder_segments)}")
            print(f"   Impact Score: {enhancement.impact_score}")
            print(f"   Implementation Complexity: {enhancement.implementation_complexity}")
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
            print(f"   Target Comparisons: {', '.join(advantage.target_comparisons)}")
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
            print(f"   Implementation Timeline: {trend.implementation_timeline}")
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
        
        # Key Findings
        print(f"\n🔍 KEY FINDINGS")
        print("-" * 40)
        for i, finding in enumerate(report.key_findings, 1):
            print(f"{i}. {finding}")
        
        # Web Sources
        print(f"\n🌐 WEB SOURCES USED")
        print("-" * 40)
        for i, source in enumerate(report.data_sources, 1):
            print(f"\n{i}. {source.title}")
            print(f"   URL: {source.url}")
            print(f"   Type: {source.source_type}")
            print(f"   Relevance: {source.relevance_score:.2f}")
            print(f"   Word Count: {source.word_count}")
        
        # Methodology
        print(f"\n📚 RESEARCH METHODOLOGY")
        print("-" * 40)
        print(report.research_methodology)
        
        print(f"\n⏰ Research conducted on: {report.timestamp}")
        print("="*80)

    def export_for_other_agents(self, report: WebImprovementReport, filename: str = None) -> str:
        """Export research data in a format suitable for other agents"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject_name = re.sub(
                r'[^a-zA-Z0-9\s]', '', report.subject_name).replace(' ', '_')
            filename = f"web_improvement_data_{safe_subject_name}_{timestamp}.json"

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
                "key_findings": report.key_findings,
                "timestamp": report.timestamp,
                "export_format": "web_improvement_research_data"
            }
            
            with open(out_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"✅ Export data saved to: {out_path}")
            return str(out_path)
        except Exception as e:
            print(f"❌ Error exporting data: {str(e)}")
            return None


def main():
    """Main function to run the web improvement research agent"""
    print("🌐 WEB IMPROVEMENT RESEARCH AGENT")
    print("="*50)
    
    # Get API key
    api_key = input("Enter your OpenAI API key (or press Enter if already set): ").strip()
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OpenAI API key is required. Please set it in your environment or provide it here.")
        return
    
    # Initialize agent
    agent = WebImprovementAgent(api_key)
    
    while True:
        print("\n" + "="*50)
        print("Choose an option:")
        print("1. Conduct web-based improvement research")
        print("2. Load and display a saved report")
        print("3. Export research data for other agents")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            subject_name = input("\nEnter the subject name (e.g., customer service process, mobile app, IT system): ").strip()
            if not subject_name:
                print("❌ Subject name is required.")
                continue
            
            print(f"\n🌐 Conducting web research for: {subject_name}")
            print("This will search the web for improvement strategies, best practices, and expert insights...")
            
            # Conduct research
            report = agent.conduct_web_research(subject_name)
            
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
                    report = WebImprovementReport(**data)
                    agent.display_report(report)
            except FileNotFoundError:
                print(f"❌ File '{filename}' not found.")
            except Exception as e:
                print(f"❌ Error loading report: {str(e)}")
        
        elif choice == "3":
            filename = input("Enter the filename of the saved report to export: ").strip()
            try:
                path = Path(filename)
                if not path.is_file():
                    alt = data_outputs_dir() / path.name
                    if alt.is_file():
                        path = alt
                with open(path, 'r') as f:
                    data = json.load(f)
                    report = WebImprovementReport(**data)
                    
                export_filename = input("Enter export filename (or press Enter for auto-generated name): ").strip()
                if not export_filename:
                    export_filename = None
                    
                agent.export_for_other_agents(report, export_filename)
            except FileNotFoundError:
                print(f"❌ File '{filename}' not found.")
            except Exception as e:
                print(f"❌ Error loading report: {str(e)}")
        
        elif choice == "4":
            print("👋 Thank you for using the Web Improvement Research Agent!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main() 