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
from research_llm.search.tavily import tavily_search
from langchain_openai import ChatOpenAI

bootstrap()
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
from newspaper import Article
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
        description="Type of source (news, report, article, etc.)")
    date_published: Optional[str] = Field(
        description="Publication date if available")
    relevance_score: float = Field(description="Relevance score (0-1)")
    word_count: int = Field(description="Number of words in content")


class MarketSegment(BaseModel):
    """Represents a market segment with its characteristics"""
    name: str = Field(description="Name of the market segment")
    size: str = Field(description="Estimated market size for this segment")
    growth_rate: str = Field(description="Growth rate of this segment")
    key_characteristics: List[str] = Field(
        description="Key characteristics of this segment")
    pain_points: List[str] = Field(
        description="Main pain points of this segment")


class Competitor(BaseModel):
    """Represents a competitor in the market"""
    name: str = Field(description="Name of the competitor")
    market_share: str = Field(description="Estimated market share")
    strengths: List[str] = Field(description="Key strengths of the competitor")
    weaknesses: List[str] = Field(
        description="Key weaknesses of the competitor")
    unique_value_proposition: str = Field(
        description="Competitor's unique value proposition")


class MarketTrend(BaseModel):
    """Represents a market trend"""
    trend_name: str = Field(description="Name of the trend")
    description: str = Field(description="Description of the trend")
    impact: str = Field(description="Impact on the market (High/Medium/Low)")
    timeframe: str = Field(description="Expected timeframe for this trend")
    supporting_evidence: List[str] = Field(
        description="Evidence supporting this trend")


class MarketOpportunity(BaseModel):
    """Represents a market opportunity"""
    opportunity_name: str = Field(description="Name of the opportunity")
    description: str = Field(description="Description of the opportunity")
    market_size: str = Field(
        description="Estimated market size for this opportunity")
    feasibility: str = Field(
        description="Feasibility assessment (High/Medium/Low)")
    time_to_market: str = Field(description="Estimated time to market")
    supporting_data: List[str] = Field(
        description="Supporting data for this opportunity")


class WebMarketResearchReport(BaseModel):
    """Complete web-based market research report"""
    topic: str = Field(description="The market research topic")
    executive_summary: str = Field(
        description="Executive summary of the market research")
    market_overview: str = Field(description="Overall market overview")
    total_market_size: str = Field(description="Total addressable market size")
    market_growth_rate: str = Field(description="Overall market growth rate")
    market_segments: List[MarketSegment] = Field(
        description="Key market segments")
    competitors: List[Competitor] = Field(
        description="Key competitors in the market")
    market_trends: List[MarketTrend] = Field(description="Key market trends")
    opportunities: List[MarketOpportunity] = Field(
        description="Market opportunities")
    risks_and_challenges: List[str] = Field(
        description="Key risks and challenges")
    recommendations: List[str] = Field(description="Strategic recommendations")
    research_methodology: str = Field(
        description="Methodology used for this research")
    data_sources: List[WebSource] = Field(
        description="Web sources used for research")
    key_findings: List[str] = Field(
        description="Key findings from web research")
    timestamp: str = Field(description="When this research was conducted")


class WebMarketResearchAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Web Market Research Agent

        This agent conducts EXTERNAL research by:
        1. Searching the web for real-time market data
        2. Extracting content from multiple sources
        3. Synthesizing external information into comprehensive reports

        Key Difference from Internal Research:
        - Internal Research: Uses only the AI's training data (static knowledge)
        - External Research: Actively searches and retrieves current web data

        Configure via environment / `.env`: OPENAI_API_KEY, TAVILY_API_KEY,
        ALLOW_SYNTHETIC_FALLBACK (default false), OPENAI_MODEL_*.
        """
        settings = get_settings()
        resolved_key = (api_key or settings.openai_api_key or "").strip()
        if not resolved_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Add it to the project root `.env` file "
                "(see `.env.example`) or pass api_key= when constructing "
                "WebMarketResearchAgent."
            )
        os.environ["OPENAI_API_KEY"] = resolved_key

        self.allow_synthetic_fallback = settings.allow_synthetic_fallback
        self._tavily_key = settings.tavily_api_key or ""

        self.llm = ChatOpenAI(
            temperature=0.3,
            model_name=settings.openai_model_synthesis,
            api_key=resolved_key,
        )
        self.llm_fast = ChatOpenAI(
            temperature=0.2,
            model_name=settings.openai_model_research,
            api_key=resolved_key,
        )
        self.parser = PydanticOutputParser(
            pydantic_object=WebMarketResearchReport)

        # Search engines and sources
        self.search_engines = {
            'google': 'https://www.google.com/search?q=',
            'bing': 'https://www.bing.com/search?q=',
            'duckduckgo': 'https://duckduckgo.com/?q='
        }

        # Headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Create prompts
        self.search_prompt = PromptTemplate(
            input_variables=["topic"],
            template="""
Generate 10 specific search queries to find comprehensive market research information about: {topic}

Focus on:
1. Market size and growth data
2. Industry reports and analysis
3. Competitor information
4. Market trends and forecasts
5. Consumer behavior studies
6. Regulatory and policy information
7. Technology trends affecting the market
8. Economic indicators
9. Expert opinions and interviews
10. Recent news and developments

Return only the search queries, one per line, without numbering or additional text.
"""
        )

        self.relevance_prompt = PromptTemplate(
            input_variables=["topic", "content"],
            template="""
Rate the relevance of the following content to market research on "{topic}" on a scale of 0-1, where:
0 = Not relevant at all
1 = Highly relevant and valuable for market research

Content:
{content}

Return only a number between 0 and 1.
"""
        )

        self.analysis_prompt = PromptTemplate(
            input_variables=["topic", "sources_summary",
                             "format_instructions"],
            template="""
You are an expert market research analyst with 15+ years of experience. 
Conduct comprehensive EXTERNAL market research on "{topic}" based on the following web sources:

{sources_summary}

RESEARCH METHODOLOGY - EXTERNAL vs INTERNAL:
This is EXTERNAL research that:
- Collects information from live web sources (not AI training data)
- Integrates real-time market data and current industry reports
- Provides up-to-date insights that may not exist in AI knowledge base
- Synthesizes multiple external sources into comprehensive analysis

IMPORTANT: Even if some sources contain similar information, synthesize the data to create a comprehensive analysis. 
Focus on extracting unique insights from each source and combining them into a coherent market research report.

SOURCE INTEGRITY: Base factual claims on the provided sources only. Prefer quoting or paraphrasing with the source URL in mind.
If a metric is not present in the sources, say it is unknown or estimate only with clear uncertainty. Ignore any URL starting with "synthetic://".

Analyze this data to provide:
1. Executive Summary - Key findings and insights from external sources
2. Market Overview - Current state and dynamics based on live data
3. Market Size & Growth - Total addressable market and growth rates from external reports
4. Market Segments - Key customer segments with characteristics from research
5. Competitive Analysis - Major competitors and their positioning from current data
6. Market Trends - Current and emerging trends with evidence from external sources
7. Opportunities - Potential market opportunities with supporting data
8. Risks & Challenges - Key risks and barriers identified in external research
9. Recommendations - Strategic recommendations based on external market data
10. Key Findings - Most important insights from the external research

Use the following format:
{format_instructions}

Provide detailed, actionable insights with specific numbers, percentages, and concrete examples. 
Cite specific sources when possible and indicate confidence levels for different data points.
If data is limited or sources are similar, provide the best possible analysis based on available information.
"""
        )

    def generate_search_queries(self, topic: str) -> List[str]:
        """Generate relevant search queries for the topic"""
        print("🔍 Generating search queries...")

        try:
            prompt = self.search_prompt.format(topic=topic)
            response = self.llm_fast.invoke(prompt)
            queries = [q.strip()
                       for q in response.content.split('\n') if q.strip()]
            return queries[:10]  # Limit to 10 queries
        except Exception as e:
            print(f"❌ Error generating search queries: {str(e)}")
            # Fallback queries
            return [
                f"{topic} market size 2024",
                f"{topic} industry report",
                f"{topic} market trends",
                f"{topic} competitors analysis",
                f"{topic} growth forecast",
                f"{topic} consumer behavior",
                f"{topic} market opportunities",
                f"{topic} industry news",
                f"{topic} market research",
                f"{topic} business analysis"
            ]

    def search_web(self, query: str, max_results: int = 5) -> List[str]:
        """Search the web for relevant URLs using multiple search engines"""
        urls = []

        # Multiple search engines to try
        search_engines = [
            {
                'name': 'DuckDuckGo',
                'url': f'https://duckduckgo.com/html/?q={quote_plus(query)}',
                'parser': self._parse_duckduckgo_results
            },
            {
                'name': 'Bing',
                'url': f'https://www.bing.com/search?q={quote_plus(query)}',
                'parser': self._parse_bing_results
            },
            {
                'name': 'Yahoo',
                'url': f'https://search.yahoo.com/search?p={quote_plus(query)}',
                'parser': self._parse_yahoo_results
            }
        ]

        for engine in search_engines:
            if len(urls) >= max_results:
                break

            try:
                print(f"  🔍 Searching with {engine['name']}...")
                response = requests.get(
                    engine['url'], headers=self.headers, timeout=15)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    engine_urls = engine['parser'](
                        soup, max_results - len(urls))

                    # Filter and add unique URLs
                    for url in engine_urls:
                        if url not in urls and self._is_valid_url(url):
                            urls.append(url)
                            if len(urls) >= max_results:
                                break

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(
                    f"    ⚠️  {engine['name']} search failed: {str(e)[:50]}...")
                continue

        # If no results from search engines, use curated market research URLs as fallback
        if not urls:
            print(
                f"  ⚠️  No results from search engines, using curated market research sources...")
            curated_urls = self._get_curated_urls(query)
            urls = curated_urls[:max_results]

        return urls[:max_results]

    def _search_with_alternative_methods(self, query: str, max_results: int = 10) -> List[str]:
        """Use alternative search methods when primary search fails"""
        urls = []

        # Method 1: Direct search on specific domains
        direct_domains = [
            f"https://www.statista.com/search/?q={quote_plus(query)}",
            f"https://www.mckinsey.com/search?q={quote_plus(query)}",
            f"https://www.bcg.com/search?q={quote_plus(query)}",
            f"https://www.forrester.com/search?q={quote_plus(query)}",
            f"https://www.gartner.com/search?q={quote_plus(query)}"
        ]

        for domain_url in direct_domains:
            try:
                response = requests.get(
                    domain_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Look for article links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        if href and self._is_valid_url(href):
                            urls.append(href)
                            if len(urls) >= max_results:
                                return urls
            except:
                continue

        # Method 2: Use news search
        news_queries = [
            f"site:reuters.com {query}",
            f"site:bloomberg.com {query}",
            f"site:cnbc.com {query}",
            f"site:forbes.com {query}",
            f"site:techcrunch.com {query}"
        ]

        for news_query in news_queries:
            try:
                search_url = f"https://duckduckgo.com/html/?q={quote_plus(news_query)}"
                response = requests.get(
                    search_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    engine_urls = self._parse_duckduckgo_results(soup, 3)
                    for url in engine_urls:
                        if url not in urls and self._is_valid_url(url):
                            urls.append(url)
                            if len(urls) >= max_results:
                                return urls
            except:
                continue

        return urls

    def _parse_duckduckgo_results(self, soup: BeautifulSoup, max_results: int) -> List[str]:
        """Parse DuckDuckGo search results"""
        urls = []

        # Try multiple selectors for DuckDuckGo
        selectors = [
            'a.result__a',
            'a.result__url',
            'a[href*="uddg="]',
            '.result__title a',
            '.result a[href]'
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    # Handle DuckDuckGo redirect URLs
                    if 'uddg=' in href:
                        try:
                            clean_url = urllib.parse.unquote(
                                href.split('uddg=')[-1])
                        except:
                            clean_url = href.split('uddg=')[-1]
                    else:
                        clean_url = href

                    if self._is_valid_url(clean_url):
                        urls.append(clean_url)
                        if len(urls) >= max_results:
                            return urls

        return urls

    def _parse_bing_results(self, soup: BeautifulSoup, max_results: int) -> List[str]:
        """Parse Bing search results"""
        urls = []

        # Bing result selectors
        selectors = [
            '.b_algo h2 a',
            '.b_title a',
            '.b_caption a',
            'h2 a[href]',
            '.b_algo a[href]'
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and self._is_valid_url(href):
                    urls.append(href)
                    if len(urls) >= max_results:
                        return urls

        return urls

    def _parse_yahoo_results(self, soup: BeautifulSoup, max_results: int) -> List[str]:
        """Parse Yahoo search results"""
        urls = []

        # Yahoo result selectors
        selectors = [
            '.algo a[href]',
            '.compTitle a[href]',
            'h3 a[href]',
            '.title a[href]',
            '.dd a[href]'
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and self._is_valid_url(href):
                    urls.append(href)
                    if len(urls) >= max_results:
                        return urls

        return urls

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not from search engines"""
        if not url or not url.startswith('http'):
            return False

        # Filter out search engine and unwanted domains
        unwanted_domains = [
            'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com',
            'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com',
            'linkedin.com', 'reddit.com', 'wikipedia.org'
        ]

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        return not any(unwanted in domain for unwanted in unwanted_domains)

    def _get_curated_urls(self, query: str) -> List[str]:
        """Get curated, high-quality market research URLs"""
        # Base URLs for different market research topics
        base_urls = {
            'fashion': [
                "https://www.statista.com/outlook/cmo/apparel/fashion-ecommerce/worldwide",
                "https://www.mckinsey.com/industries/retail/our-insights/the-state-of-fashion-2024",
                "https://www.bcg.com/publications/2024/fashion-industry-trends",
                "https://www.forrester.com/report/fashion-retail-trends-2024",
                "https://www.gartner.com/en/newsroom/press-releases/fashion-tech-trends",
                "https://www.deloitte.com/global/en/industries/consumer/perspectives/global-powers-of-luxury-goods.html",
                "https://www.pwc.com/gx/en/industries/retail-consumer/retail-consumer-insights.html",
                "https://www.ey.com/en_gl/consumer-products-retail/retail-trends",
                "https://www.reuters.com/business/retail-consumer/",
                "https://www.bloomberg.com/news/topics/retail",
                "https://www.cnbc.com/retail/",
                "https://www.forbes.com/sites/retail/",
                "https://techcrunch.com/tag/retail/",
                "https://www.emarketer.com/topics/category/retail-ecommerce",
                "https://www.ibisworld.com/industry-statistics/market-size/online-clothing-sales-united-states",
                "https://www.businesswire.com/news/home/",
                "https://www.prnewswire.com/news-releases/",
                "https://www.globenewswire.com/news-release/",
                "https://www.marketwatch.com/story/",
                "https://www.fool.com/investing/",
                "https://seekingalpha.com/news/",
                "https://www.investing.com/news/",
                "https://www.financialexpress.com/",
                "https://www.livemint.com/",
                "https://www.moneycontrol.com/news/",
                "https://www.ndtv.com/business/",
                "https://www.zeebiz.com/",
                "https://www.business-standard.com/",
                "https://www.thehindubusinessline.com/",
                "https://www.economictimes.indiatimes.com/",
                "https://www.financialpost.com/",
                "https://www.theglobeandmail.com/business/",
                "https://www.nationalpost.com/news/",
                "https://www.cbc.ca/news/business/",
                "https://www.ctvnews.ca/business/",
                "https://www.globalnews.ca/business/",
                "https://www.citynews.ca/business/",
                "https://www.680news.com/business/",
                "https://www.cp24.com/business/",
                "https://www.ctvnews.ca/business/",
                "https://www.globalnews.ca/business/",
                "https://www.citynews.ca/business/",
                "https://www.680news.com/business/",
                "https://www.cp24.com/business/"
            ],
            'ecommerce': [
                "https://www.statista.com/outlook/dmo/ecommerce/worldwide",
                "https://www.mckinsey.com/industries/retail/our-insights/the-great-retail-bifurcation",
                "https://www.bcg.com/publications/2024/ecommerce-trends",
                "https://www.forrester.com/report/ecommerce-trends-2024",
                "https://www.gartner.com/en/newsroom/press-releases/ecommerce-predictions",
                "https://www.deloitte.com/global/en/industries/consumer/perspectives/global-powers-of-retailing.html",
                "https://www.reuters.com/business/retail-consumer/",
                "https://www.bloomberg.com/news/topics/retail",
                "https://www.cnbc.com/retail/",
                "https://www.forbes.com/sites/retail/",
                "https://techcrunch.com/tag/ecommerce/",
                "https://www.emarketer.com/topics/category/retail-ecommerce",
                "https://www.ibisworld.com/industry-statistics/market-size/online-shopping-united-states",
                "https://www.businesswire.com/news/home/",
                "https://www.prnewswire.com/news-releases/",
                "https://www.globenewswire.com/news-release/",
                "https://www.marketwatch.com/story/",
                "https://www.fool.com/investing/",
                "https://seekingalpha.com/news/",
                "https://www.investing.com/news/",
                "https://www.financialexpress.com/",
                "https://www.livemint.com/",
                "https://www.moneycontrol.com/news/",
                "https://www.ndtv.com/business/",
                "https://www.zeebiz.com/",
                "https://www.business-standard.com/",
                "https://www.thehindubusinessline.com/",
                "https://www.economictimes.indiatimes.com/",
                "https://www.financialpost.com/",
                "https://www.theglobeandmail.com/business/",
                "https://www.nationalpost.com/news/",
                "https://www.cbc.ca/news/business/",
                "https://www.ctvnews.ca/business/",
                "https://www.globalnews.ca/business/",
                "https://www.citynews.ca/business/",
                "https://www.680news.com/business/",
                "https://www.cp24.com/business/",
                "https://www.ctvnews.ca/business/",
                "https://www.globalnews.ca/business/",
                "https://www.citynews.ca/business/",
                "https://www.680news.com/business/",
                "https://www.cp24.com/business/"
            ],
            'retail': [
                "https://www.statista.com/outlook/cmo/retail/worldwide",
                "https://www.mckinsey.com/industries/retail/our-insights/retail-industry-trends",
                "https://www.bcg.com/publications/2024/retail-transformation",
                "https://www.forrester.com/report/retail-trends-2024",
                "https://www.gartner.com/en/newsroom/press-releases/retail-predictions",
                "https://www.reuters.com/business/retail-consumer/",
                "https://www.bloomberg.com/news/topics/retail",
                "https://www.cnbc.com/retail/",
                "https://www.forbes.com/sites/retail/",
                "https://techcrunch.com/tag/retail/",
                "https://www.emarketer.com/topics/category/retail-ecommerce",
                "https://www.ibisworld.com/industry-statistics/market-size/retail-united-states",
                "https://www.businesswire.com/news/home/",
                "https://www.prnewswire.com/news-releases/",
                "https://www.globenewswire.com/news-release/",
                "https://www.marketwatch.com/story/",
                "https://www.fool.com/investing/",
                "https://seekingalpha.com/news/",
                "https://www.investing.com/news/",
                "https://www.financialexpress.com/",
                "https://www.livemint.com/",
                "https://www.moneycontrol.com/news/",
                "https://www.ndtv.com/business/",
                "https://www.zeebiz.com/",
                "https://www.business-standard.com/",
                "https://www.thehindubusinessline.com/",
                "https://www.economictimes.indiatimes.com/",
                "https://www.financialpost.com/",
                "https://www.theglobeandmail.com/business/",
                "https://www.nationalpost.com/news/",
                "https://www.cbc.ca/news/business/",
                "https://www.ctvnews.ca/business/",
                "https://www.globalnews.ca/business/",
                "https://www.citynews.ca/business/",
                "https://www.680news.com/business/",
                "https://www.cp24.com/business/",
                "https://www.ctvnews.ca/business/",
                "https://www.globalnews.ca/business/",
                "https://www.citynews.ca/business/",
                "https://www.680news.com/business/",
                "https://www.cp24.com/business/"
            ]
        }

        # Determine which category the query belongs to
        query_lower = query.lower()
        if any(word in query_lower for word in ['fashion', 'clothing', 'apparel', 'style']):
            return base_urls['fashion']
        elif any(word in query_lower for word in ['ecommerce', 'online', 'digital', 'shopping']):
            return base_urls['ecommerce']
        elif any(word in query_lower for word in ['retail', 'store', 'shopping']):
            return base_urls['retail']
        else:
            # Return a mix of all categories for general queries
            return base_urls['fashion'] + base_urls['ecommerce'] + base_urls['retail']

    def extract_content_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a URL using multiple methods"""
        try:
            print(f"    📄 Extracting content from: {url}")

            # Method 1: Try newspaper3k (best for news articles)
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
                print(f"      ⚠️  newspaper3k failed: {str(e)[:50]}...")
                pass

            # Method 2: Try trafilatura (best for general web content)
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    extracted_text = trafilatura.extract(response.text)
                    if extracted_text and len(extracted_text) > 100:
                        # Get title from trafilatura or fallback
                        title = trafilatura.extract_metadata(
                            response.text).get('title', 'Extracted content')
                        return {
                            'title': title,
                            'content': extracted_text,
                            'date_published': None,
                            'method': 'trafilatura'
                        }
            except Exception as e:
                print(f"      ⚠️  trafilatura failed: {str(e)[:50]}...")
                pass

            # Method 3: Enhanced BeautifulSoup extraction
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "header", "footer", "aside", "menu", "noscript"]):
                        element.decompose()

                    # Try to find main content area
                    main_content = None
                    content_selectors = [
                        'main', 'article', '.content', '.main-content',
                        '.post-content', '.entry-content', '#content', '#main',
                        '.post', '.blog-post', '.story', '.article'
                    ]

                    for selector in content_selectors:
                        main_content = soup.select_one(selector)
                        if main_content:
                            break

                    if not main_content:
                        main_content = soup.body if soup.body else soup

                    # Extract text with better formatting
                    text = main_content.get_text(separator=' ', strip=True)

                    # Clean up text
                    lines = [line.strip()
                             for line in text.splitlines() if line.strip()]
                    text = ' '.join(lines)

                    # Remove excessive whitespace
                    text = re.sub(r'\s+', ' ', text)

                    if text and len(text) > 100:
                        title = soup.title.string if soup.title else 'Extracted content'
                        return {
                            'title': title,
                            # Increased limit for better content
                            'content': text[:8000],
                            'date_published': None,
                            'method': 'beautifulsoup'
                        }
            except Exception as e:
                print(f"      ⚠️  beautifulsoup failed: {str(e)[:50]}...")
                pass

            # Method 4: Try to extract from specific content types
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Look for specific content patterns
                    content_patterns = [
                        '.article-content', '.post-body', '.story-content',
                        '.report-content', '.research-content', '.analysis-content',
                        '.entry', '.post-text', '.content-body', '.main-text'
                    ]

                    for pattern in content_patterns:
                        content_elem = soup.select_one(pattern)
                        if content_elem:
                            text = content_elem.get_text(
                                separator=' ', strip=True)
                            if len(text) > 100:
                                title = soup.title.string if soup.title else 'Extracted content'
                                return {
                                    'title': title,
                                    'content': text[:8000],
                                    'date_published': None,
                                    'method': 'pattern_extraction'
                                }
            except Exception as e:
                print(f"      ⚠️  pattern extraction failed: {str(e)[:50]}...")
                pass

            # Method 5: Try to extract from paragraphs
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "header", "footer"]):
                        element.decompose()

                    # Get all paragraphs
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        text = ' '.join([p.get_text().strip()
                                        for p in paragraphs if p.get_text().strip()])
                        if len(text) > 100:
                            title = soup.title.string if soup.title else 'Extracted content'
                            return {
                                'title': title,
                                'content': text[:8000],
                                'date_published': None,
                                'method': 'paragraph_extraction'
                            }
            except Exception as e:
                print(
                    f"      ⚠️  paragraph extraction failed: {str(e)[:50]}...")
                pass

            # Method 6: Try to extract from divs with text content
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "header", "footer"]):
                        element.decompose()

                    # Find divs with substantial text content
                    divs = soup.find_all('div')
                    best_div = None
                    max_text_length = 0

                    for div in divs:
                        text = div.get_text(strip=True)
                        if len(text) > max_text_length and len(text) > 200:
                            max_text_length = len(text)
                            best_div = div

                    if best_div:
                        text = best_div.get_text(separator=' ', strip=True)
                        title = soup.title.string if soup.title else 'Extracted content'
                        return {
                            'title': title,
                            'content': text[:8000],
                            'date_published': None,
                            'method': 'div_extraction'
                        }
            except Exception as e:
                print(f"      ⚠️  div extraction failed: {str(e)[:50]}...")
                pass

            print(f"      ❌ All extraction methods failed for {url}")
            return None

        except Exception as e:
            print(f"❌ Error extracting content from {url}: {str(e)}")
            return None

    def _generate_fallback_content(self, topic: str) -> List[WebSource]:
        """Generate fallback content when web search fails"""
        print("🔄 Generating fallback content due to web search limitations...")

        fallback_sources = []
        research_areas = [
            "market_size_and_growth",
            "consumer_behavior",
            "competitive_landscape",
            "technology_trends",
            "regulatory_environment"
        ]

        for i, area in enumerate(research_areas, 1):
            content_data = self._generate_research_content(topic, area, i)
            if content_data:
                source = WebSource(
                    url=f"synthetic://demo/fallback-research/{area}/{i}",
                    title=content_data['title'],
                    content=content_data['content'],
                    source_type="synthetic_demo",
                    date_published=content_data['date_published'],
                    relevance_score=0.8,  # High relevance for fallback
                    word_count=len(content_data['content'].split())
                )
                fallback_sources.append(source)

        return fallback_sources

    def assess_relevance(self, topic: str, content: str) -> float:
        """Assess the relevance of content to the research topic"""
        try:
            # Truncate content if too long
            if len(content) > 2000:
                content = content[:2000]

            prompt = self.relevance_prompt.format(topic=topic, content=content)
            response = self.llm_fast.invoke(prompt)

            try:
                return float(response.content.strip())
            except:
                return 0.5  # Default relevance score

        except Exception as e:
            print(f"❌ Error assessing relevance: {str(e)}")
            return 0.5

    def gather_web_sources(self, topic: str, max_sources: int = 20) -> List[WebSource]:
        """Gather web sources for the research topic"""
        print(f"🌐 Gathering market research data for: {topic}")

        # Generate search queries for content variety
        queries = self.generate_search_queries(topic)
        print(f"📝 Generated {len(queries)} search queries")

        all_sources = []
        processed_urls = set()

        # Strategy 0: Tavily API (real URLs + snippets) when TAVILY_API_KEY is set
        if self._tavily_key:
            print("🔍 Strategy 0: Tavily API...")
            t_seen: set[str] = set()
            for q in queries[:6]:
                if len(all_sources) >= max_sources:
                    break
                for row in tavily_search(
                    q, self._tavily_key, max_results=4
                ):
                    url = row["url"]
                    if url in t_seen or url in processed_urls:
                        continue
                    t_seen.add(url)
                    content = row["content"]
                    relevance = self.assess_relevance(topic, content)
                    if relevance > 0.05:
                        all_sources.append(
                            WebSource(
                                url=url,
                                title=row["title"],
                                content=content,
                                source_type="tavily",
                                date_published=None,
                                relevance_score=relevance,
                                word_count=len(content.split()),
                            )
                        )
                        processed_urls.add(url)
                        print(
                            f"      ✅ Tavily source (relevance: {relevance:.2f}, words: {len(content.split())})"
                        )
                    if len(all_sources) >= max_sources:
                        break

        # Strategy 1: Primary web search with more aggressive approach
        print("🔍 Strategy 1: Primary web search...")
        for i, query in enumerate(queries[:10], 1):  # Use first 10 queries
            if len(all_sources) >= max_sources:
                break

            print(f"  🔍 Search {i}/10: {query}")

            try:
                # Search for URLs with higher max_results
                urls = self.search_web(query, max_results=10)

                if not urls:
                    print(f"    ⚠️  No URLs found for query: {query}")
                    continue

                # Extract content from each URL
                for url in urls:
                    if url in processed_urls:
                        continue

                    if len(all_sources) >= max_sources:
                        break

                    # Extract content
                    content_data = self.extract_content_from_url(url)

                    # Even lower minimum content
                    if content_data and len(content_data['content']) > 100:
                        # Assess relevance
                        relevance = self.assess_relevance(
                            topic, content_data['content'])

                        if relevance > 0.05:  # Much lower threshold to include more sources
                            source = WebSource(
                                url=url,
                                title=content_data['title'],
                                content=content_data['content'],
                                source_type=self._classify_source_type(
                                    url, content_data['title']),
                                date_published=content_data['date_published'],
                                relevance_score=relevance,
                                word_count=len(content_data['content'].split())
                            )
                            all_sources.append(source)
                            processed_urls.add(url)
                            print(
                                f"      ✅ Added source (relevance: {relevance:.2f}, words: {source.word_count})")
                        else:
                            print(
                                f"      ⚠️  Low relevance ({relevance:.2f}) for {url}")
                    else:
                        print(f"      ❌ Failed to extract content from {url}")

                    # Faster rate limiting
                    time.sleep(0.2)

                # Faster rate limiting between queries
                time.sleep(0.3)

            except Exception as e:
                print(f"    ❌ Error processing query '{query}': {str(e)}")
                continue

        # Strategy 2: Alternative search methods
        if len(all_sources) < max_sources // 2:
            print("🔍 Strategy 2: Alternative search methods...")
            for i, query in enumerate(queries[10:15], 1):  # Use next 5 queries
                if len(all_sources) >= max_sources:
                    break

                print(f"  🔍 Alternative search {i}/5: {query}")

                try:
                    # Use alternative search methods
                    urls = self._search_with_alternative_methods(
                        query, max_results=10)

                    for url in urls:
                        if url in processed_urls:
                            continue

                        if len(all_sources) >= max_sources:
                            break

                        content_data = self.extract_content_from_url(url)

                        if content_data and len(content_data['content']) > 100:
                            relevance = self.assess_relevance(
                                topic, content_data['content'])

                            if relevance > 0.05:
                                source = WebSource(
                                    url=url,
                                    title=content_data['title'],
                                    content=content_data['content'],
                                    source_type=self._classify_source_type(
                                        url, content_data['title']),
                                    date_published=content_data['date_published'],
                                    relevance_score=relevance,
                                    word_count=len(
                                        content_data['content'].split())
                                )
                                all_sources.append(source)
                                processed_urls.add(url)
                                print(
                                    f"      ✅ Added alternative source (relevance: {relevance:.2f}, words: {source.word_count})")

                        time.sleep(0.2)

                    time.sleep(0.3)

                except Exception as e:
                    print(f"    ❌ Error in alternative search: {str(e)}")
                    continue

        # Strategy 3: Curated high-quality sources
        if len(all_sources) < max_sources // 2:
            print("🔍 Strategy 3: Curated high-quality sources...")
            curated_urls = self._get_curated_urls(topic)

            for url in curated_urls:
                if url in processed_urls:
                    continue

                if len(all_sources) >= max_sources:
                    break

                content_data = self.extract_content_from_url(url)

                if content_data and len(content_data['content']) > 100:
                    relevance = self.assess_relevance(
                        topic, content_data['content'])

                    if relevance > 0.05:
                        source = WebSource(
                            url=url,
                            title=content_data['title'],
                            content=content_data['content'],
                            source_type=self._classify_source_type(
                                url, content_data['title']),
                            date_published=content_data['date_published'],
                            relevance_score=relevance,
                            word_count=len(content_data['content'].split())
                        )
                        all_sources.append(source)
                        processed_urls.add(url)
                        print(
                            f"    ✅ Added curated source (relevance: {relevance:.2f}, words: {source.word_count})")

                time.sleep(0.2)

        # Strategy 4: News and blog search
        if len(all_sources) < 10:
            print("🔍 Strategy 4: News and blog search...")
            news_queries = [
                f"site:medium.com {topic}",
                f"site:linkedin.com {topic}",
                f"site:wordpress.com {topic}",
                f"site:blogspot.com {topic}",
                f"site:substack.com {topic}"
            ]

            for i, query in enumerate(news_queries, 1):
                if len(all_sources) >= max_sources:
                    break

                print(f"  🔍 News search {i}/5: {query}")

                try:
                    urls = self.search_web(query, max_results=5)

                    for url in urls:
                        if url in processed_urls:
                            continue

                        if len(all_sources) >= max_sources:
                            break

                        content_data = self.extract_content_from_url(url)

                        if content_data and len(content_data['content']) > 100:
                            relevance = self.assess_relevance(
                                topic, content_data['content'])

                            if relevance > 0.05:
                                source = WebSource(
                                    url=url,
                                    title=content_data['title'],
                                    content=content_data['content'],
                                    source_type=self._classify_source_type(
                                        url, content_data['title']),
                                    date_published=content_data['date_published'],
                                    relevance_score=relevance,
                                    word_count=len(
                                        content_data['content'].split())
                                )
                                all_sources.append(source)
                                processed_urls.add(url)
                                print(
                                    f"      ✅ Added news source (relevance: {relevance:.2f}, words: {source.word_count})")

                        time.sleep(0.2)

                    time.sleep(0.3)

                except Exception as e:
                    print(f"    ❌ Error in news search: {str(e)}")
                    continue

        # Strategy 5: Optional synthetic placeholders (demo only — off by default)
        if len(all_sources) < 10 and self.allow_synthetic_fallback:
            print(
                "🔍 Strategy 5: synthetic demo sources (ALLOW_SYNTHETIC_FALLBACK=true)..."
            )
            additional_sources = self._generate_fallback_content(topic)
            for source in additional_sources:
                if len(all_sources) >= max_sources:
                    break
                all_sources.append(source)
                print(
                    f"    ✅ Added synthetic demo source (relevance: {source.relevance_score:.2f}, words: {source.word_count})")
        elif len(all_sources) < 10:
            print(
                "⚠️  Few web sources found; synthetic fallback disabled (set ALLOW_SYNTHETIC_FALLBACK=true only for demos)."
            )

        # Strategy 6: Try more general search terms
        if len(all_sources) < 10:
            print("🔍 Strategy 6: General search terms...")
            general_queries = [
                f"{topic} market",
                f"{topic} industry",
                f"{topic} business",
                f"{topic} trends",
                f"{topic} analysis"
            ]

            for i, query in enumerate(general_queries, 1):
                if len(all_sources) >= max_sources:
                    break

                print(f"  🔍 General search {i}/5: {query}")

                try:
                    urls = self.search_web(query, max_results=5)

                    for url in urls:
                        if url in processed_urls:
                            continue

                        if len(all_sources) >= max_sources:
                            break

                        content_data = self.extract_content_from_url(url)

                        if content_data and len(content_data['content']) > 100:
                            relevance = self.assess_relevance(
                                topic, content_data['content'])

                            if relevance > 0.05:
                                source = WebSource(
                                    url=url,
                                    title=content_data['title'],
                                    content=content_data['content'],
                                    source_type=self._classify_source_type(
                                        url, content_data['title']),
                                    date_published=content_data['date_published'],
                                    relevance_score=relevance,
                                    word_count=len(
                                        content_data['content'].split())
                                )
                                all_sources.append(source)
                                processed_urls.add(url)
                                print(
                                    f"      ✅ Added general source (relevance: {relevance:.2f}, words: {source.word_count})")

                        time.sleep(0.2)

                    time.sleep(0.3)

                except Exception as e:
                    print(f"    ❌ Error in general search: {str(e)}")
                    continue

        # Sort by relevance
        all_sources.sort(key=lambda x: x.relevance_score, reverse=True)

        print(f"✅ Found {len(all_sources)} relevant sources from web search")
        return all_sources[:max_sources]

    def _generate_research_content(self, topic: str, area: str, index: int) -> Dict[str, Any]:
        """Generate realistic market research content for a specific area"""

        # Create unique content based on topic and area
        topic_hash = hashlib.md5(
            f"{topic}_{area}_{index}".encode()).hexdigest()
        hash_int = int(topic_hash[:8], 16)

        if area == "market_size_and_growth":
            return {
                'title': f'Market Size and Growth Analysis: {topic.title()}',
                'content': f'''
                Comprehensive market size and growth analysis for the {topic} industry.
                
                Market Size Metrics:
                - Total addressable market (TAM): ${(hash_int % 2000 + 500)} billion
                - Serviceable addressable market (SAM): ${(hash_int % 1000 + 200)} billion
                - Serviceable obtainable market (SOM): ${(hash_int % 500 + 100)} billion
                
                Growth Projections:
                - Current market size: ${(hash_int % 1500 + 300)} billion
                - CAGR (2024-2029): {(hash_int % 15 + 8)}.{(hash_int % 10)}%
                - Expected market size by 2029: ${(hash_int % 3000 + 800)} billion
                
                Regional Breakdown:
                - North America: {(hash_int % 30 + 35)}% of global market
                - Europe: {(hash_int % 25 + 25)}% of global market
                - Asia-Pacific: {(hash_int % 20 + 30)}% of global market
                - Rest of World: {(hash_int % 15 + 10)}% of global market
                
                Growth Drivers:
                - Digital transformation acceleration
                - Changing consumer preferences
                - Technology innovation and adoption
                - Regulatory environment evolution
                - Economic recovery and expansion
                
                Market Maturity Assessment:
                - Current stage: {(hash_int % 3 + 1)} out of 5 (1=Emerging, 5=Mature)
                - Growth potential: {(hash_int % 40 + 60)}% remaining
                - Consolidation phase: {(hash_int % 5 + 3)} years away
                ''',
                'source_type': 'market_analysis',
                'date_published': '2024-01-15'
            }

        elif area == "consumer_behavior":
            return {
                'title': f'Consumer Behavior Analysis: {topic.title()}',
                'content': f'''
                In-depth consumer behavior analysis for {topic} market.
                
                Consumer Demographics:
                - Primary age group: {(hash_int % 20 + 25)}-{(hash_int % 15 + 45)} years
                - Gender distribution: {(hash_int % 20 + 40)}% female, {(hash_int % 20 + 40)}% male
                - Income level: ${(hash_int % 50 + 50)}K - ${(hash_int % 100 + 150)}K annually
                - Education: {(hash_int % 30 + 60)}% college educated
                
                Purchase Behavior:
                - Average purchase frequency: {(hash_int % 10 + 3)} times per month
                - Average transaction value: ${(hash_int % 100 + 50)}
                - Preferred shopping channels: Online ({(hash_int % 30 + 60)}%), In-store ({(hash_int % 30 + 30)}%)
                - Decision-making time: {(hash_int % 5 + 2)} days average
                
                Consumer Preferences:
                - Price sensitivity: {(hash_int % 30 + 50)}% consider price primary factor
                - Quality focus: {(hash_int % 25 + 60)}% prioritize quality over price
                - Brand loyalty: {(hash_int % 20 + 40)}% show strong brand preference
                - Innovation adoption: {(hash_int % 30 + 50)}% early adopters
                
                Pain Points and Needs:
                - Convenience requirements: {(hash_int % 30 + 70)}% value time-saving
                - Quality assurance: {(hash_int % 25 + 65)}% concerned about product quality
                - Customer service: {(hash_int % 20 + 60)}% prioritize good service
                - Sustainability: {(hash_int % 25 + 45)}% consider environmental impact
                
                Technology Adoption:
                - Mobile usage: {(hash_int % 20 + 70)}% prefer mobile interfaces
                - Social media influence: {(hash_int % 30 + 50)}% influenced by social platforms
                - AI/ML acceptance: {(hash_int % 25 + 55)}% comfortable with AI recommendations
                ''',
                'source_type': 'consumer_research',
                'date_published': '2024-01-15'
            }

        elif area == "competitive_landscape":
            return {
                'title': f'Competitive Landscape Analysis: {topic.title()}',
                'content': f'''
                Comprehensive competitive analysis for the {topic} market.
                
                Market Concentration:
                - Top 5 players market share: {(hash_int % 30 + 40)}%
                - Market leader share: {(hash_int % 15 + 12)}%
                - Fragmentation level: {(hash_int % 3 + 1)} out of 5 (1=Highly concentrated, 5=Highly fragmented)
                
                Key Competitors:
                1. Market Leader: {(hash_int % 15 + 12)}% share, strong brand recognition
                2. Challenger: {(hash_int % 10 + 8)}% share, aggressive growth strategy
                3. Niche Player: {(hash_int % 8 + 5)}% share, specialized positioning
                4. Regional Player: {(hash_int % 6 + 4)}% share, geographic focus
                5. New Entrant: {(hash_int % 4 + 2)}% share, innovative approach
                
                Competitive Advantages:
                - Technology leadership: {(hash_int % 25 + 60)}% of players
                - Cost efficiency: {(hash_int % 20 + 45)}% of players
                - Brand strength: {(hash_int % 20 + 50)}% of players
                - Distribution network: {(hash_int % 15 + 40)}% of players
                
                Entry Barriers:
                - Capital requirements: ${(hash_int % 50 + 100)}M minimum investment
                - Regulatory compliance: {(hash_int % 20 + 60)}% complexity level
                - Technology requirements: {(hash_int % 25 + 55)}% technical barriers
                - Brand loyalty: {(hash_int % 20 + 50)}% customer switching costs
                
                Competitive Strategies:
                - Differentiation focus: {(hash_int % 30 + 50)}% of market
                - Cost leadership: {(hash_int % 25 + 35)}% of market
                - Innovation focus: {(hash_int % 20 + 40)}% of market
                - Partnership strategies: {(hash_int % 15 + 30)}% of market
                ''',
                'source_type': 'competitive_analysis',
                'date_published': '2024-01-15'
            }

        elif area == "technology_trends":
            return {
                'title': f'Technology Trends Impact: {topic.title()}',
                'content': f'''
                Technology trends and their impact on the {topic} market.
                
                Emerging Technologies:
                - Artificial Intelligence: {(hash_int % 30 + 60)}% adoption rate
                - Machine Learning: {(hash_int % 25 + 55)}% implementation level
                - Blockchain: {(hash_int % 20 + 30)}% market penetration
                - IoT Integration: {(hash_int % 25 + 45)}% connectivity adoption
                - AR/VR Applications: {(hash_int % 15 + 25)}% market presence
                
                Digital Transformation:
                - Digital maturity: {(hash_int % 30 + 50)}% of companies advanced
                - Cloud adoption: {(hash_int % 25 + 65)}% migration complete
                - Data analytics: {(hash_int % 30 + 60)}% implementation rate
                - Automation level: {(hash_int % 25 + 45)}% processes automated
                
                Technology Investment:
                - R&D spending: {(hash_int % 5 + 8)}% of revenue average
                - Technology budget: ${(hash_int % 50 + 100)}M average per company
                - Innovation focus: {(hash_int % 30 + 60)}% prioritize tech innovation
                
                Impact on Business Models:
                - Platform-based models: {(hash_int % 25 + 45)}% market adoption
                - Subscription services: {(hash_int % 20 + 40)}% revenue model
                - Data monetization: {(hash_int % 15 + 35)}% value creation
                - Ecosystem development: {(hash_int % 20 + 30)}% partnership focus
                
                Future Technology Roadmap:
                - 1-2 years: AI/ML mainstream adoption
                - 3-5 years: Blockchain integration
                - 5+ years: Quantum computing impact
                ''',
                'source_type': 'technology_research',
                'date_published': '2024-01-15'
            }

        else:
            # Generic research content for other areas
            return {
                'title': f'{area.replace("_", " ").title()} Analysis: {topic.title()}',
                'content': f'''
                Comprehensive {area.replace("_", " ")} analysis for the {topic} market.
                
                Key Findings:
                - Market impact: {(hash_int % 30 + 50)}% significance level
                - Growth potential: {(hash_int % 25 + 60)}% opportunity assessment
                - Risk factors: {(hash_int % 20 + 40)}% risk level identified
                - Implementation timeline: {(hash_int % 24 + 12)} months average
                
                Strategic Implications:
                - Business model adaptation required
                - Technology investment needed
                - Partnership opportunities available
                - Regulatory compliance considerations
                
                Recommendations:
                - Immediate actions: {(hash_int % 5 + 3)} priority initiatives
                - Medium-term strategy: {(hash_int % 10 + 6)} month roadmap
                - Long-term vision: {(hash_int % 5 + 3)} year planning horizon
                ''',
                'source_type': 'market_research',
                'date_published': '2024-01-15'
            }

    def _classify_source_type(self, url: str, title: str) -> str:
        """Classify the type of source based on URL and title"""
        url_lower = url.lower()
        title_lower = title.lower()

        if any(word in url_lower for word in ['news', 'article', 'blog']):
            return 'news'
        elif any(word in url_lower for word in ['report', 'study', 'research']):
            return 'report'
        elif any(word in url_lower for word in ['market', 'industry', 'business']):
            return 'market_analysis'
        elif any(word in url_lower for word in ['academic', 'edu', 'scholar']):
            return 'academic'
        else:
            return 'general'

    def create_sources_summary(self, sources: List[WebSource]) -> str:
        """Create a summary of all sources for analysis"""
        summary = "WEB SOURCES SUMMARY:\n\n"

        for i, source in enumerate(sources, 1):
            summary += f"Source {i}: {source.title}\n"
            summary += f"URL: {source.url}\n"
            summary += f"Type: {source.source_type}\n"
            summary += f"Relevance: {source.relevance_score:.2f}\n"
            summary += f"Word Count: {source.word_count}\n"
            summary += f"Key Content: {source.content[:500]}...\n\n"

        return summary

    def conduct_web_research(self, topic: str) -> WebMarketResearchReport:
        """Conduct comprehensive web-based market research

        EXTERNAL RESEARCH PROCESS:
        1. Generate targeted search queries for the topic
        2. Search multiple web sources (DuckDuckGo, Bing, Yahoo)
        3. Extract and analyze content from relevant URLs
        4. Assess relevance and quality of each source
        5. Synthesize external data into comprehensive market report

        This differs from internal research which only uses AI training data.
        """
        print(f"🔬 Starting EXTERNAL web-based market research on: {topic}")
        print("🌐 This agent searches live web sources (not AI training data)")
        print("⏳ This may take several minutes...")

        try:
            # Gather web sources
            sources = self.gather_web_sources(topic)

            if not sources:
                print("❌ No relevant sources found. Please try a different topic.")
                return None

            print(f"📊 Analyzing {len(sources)} sources...")

            # Create sources summary
            sources_summary = self.create_sources_summary(sources)

            # Get format instructions
            format_instructions = self.parser.get_format_instructions()

            # Create analysis prompt
            prompt = self.analysis_prompt.format(
                topic=topic,
                sources_summary=sources_summary,
                format_instructions=format_instructions
            )

            # Run analysis
            print("🧠 Analyzing data and generating report...")
            response = self.llm.invoke(prompt)

            # Parse the response
            try:
                report = self.parser.parse(response.content)
                report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                report.data_sources = sources
                return report
            except Exception as parse_error:
                print(f"⚠️  Parsing error: {str(parse_error)}")
                print("🔄 Attempting to generate a simplified report...")

                # Create a simplified report structure
                simplified_report = WebMarketResearchReport(
                    topic=topic,
                    executive_summary="Analysis based on web research sources",
                    market_overview="Market analysis from gathered sources",
                    total_market_size="Based on research data",
                    market_growth_rate="Growth analysis from sources",
                    market_segments=[],
                    competitors=[],
                    market_trends=[],
                    opportunities=[],
                    risks_and_challenges=["Data parsing limitations"],
                    recommendations=["Conduct additional research"],
                    research_methodology="Web-based research with content extraction",
                    data_sources=sources,
                    key_findings=["Web research completed",
                                  "Sources analyzed"],
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                return simplified_report

        except Exception as e:
            print(f"❌ Error conducting web research: {str(e)}")
            return None

    def save_report(self, report: WebMarketResearchReport, filename: str = None) -> str:
        """Save the market research report to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = re.sub(r'[^a-zA-Z0-9\s]', '',
                                report.topic).replace(' ', '_')
            filename = f"web_market_research_{safe_topic}_{timestamp}.json"

        try:
            out_path = Path(filename)
            if not out_path.is_absolute():
                out_path = data_outputs_dir() / out_path.name
            # Convert sources to dict for JSON serialization
            report_dict = report.dict()
            report_dict['data_sources'] = [source.dict()
                                           for source in report.data_sources]

            with open(out_path, 'w') as f:
                json.dump(report_dict, f, indent=2)
            print(f"✅ Report saved to: {out_path}")
            return str(out_path)
        except Exception as e:
            print(f"❌ Error saving report: {str(e)}")
            return None

    def display_report(self, report: WebMarketResearchReport):
        """Display the market research report in a formatted way"""
        print("\n" + "="*80)
        print(f"🌐 WEB-BASED MARKET RESEARCH REPORT: {report.topic.upper()}")
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

        # Key Findings
        print(f"\n🔍 KEY FINDINGS")
        print("-" * 40)
        for i, finding in enumerate(report.key_findings, 1):
            print(f"{i}. {finding}")

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
            print(
                f"   Value Proposition: {competitor.unique_value_proposition}")
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
            print(f"   Supporting Evidence:")
            for evidence in trend.supporting_evidence:
                print(f"     • {evidence}")

        # Opportunities
        print(f"\n💡 MARKET OPPORTUNITIES")
        print("-" * 40)
        for i, opportunity in enumerate(report.opportunities, 1):
            print(f"\n{i}. {opportunity.opportunity_name}")
            print(f"   Market Size: {opportunity.market_size}")
            print(f"   Feasibility: {opportunity.feasibility}")
            print(f"   Time to Market: {opportunity.time_to_market}")
            print(f"   Description: {opportunity.description}")
            print(f"   Supporting Data:")
            for data in opportunity.supporting_data:
                print(f"     • {data}")

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

        # Research Methodology
        print(f"\n📚 RESEARCH METHODOLOGY")
        print("-" * 40)
        print("EXTERNAL RESEARCH APPROACH:")
        print("• Web-based data collection from live sources")
        print("• Multi-source synthesis and analysis")
        print("• Real-time market data integration")
        print("• Current industry report analysis")
        print("• External source validation and relevance scoring")
        print(f"\n{report.research_methodology}")

        # Data Sources Summary
        print(f"\n📖 DATA SOURCES ({len(report.data_sources)} sources)")
        print("-" * 40)
        for i, source in enumerate(report.data_sources, 1):
            print(f"{i}. {source.title}")
            print(f"   URL: {source.url}")
            print(f"   Type: {source.source_type}")
            print(f"   Relevance: {source.relevance_score:.2f}")
            print(f"   Word Count: {source.word_count}")

        print(f"\n⏰ Research conducted on: {report.timestamp}")
        print("="*80)


def main():
    """Main function to run the web market research agent"""
    print("🌐 WEB-BASED MARKET RESEARCH AGENT")
    print("="*50)

    # Check if API key is already set in environment
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        # Only prompt for API key if not already set
        api_key = input("Enter your OpenAI API key: ").strip()
        if not api_key:
            print(
                "❌ OpenAI API key is required. Please set it in your environment or provide it here.")
            return
    else:
        print("✅ Using OpenAI API key from environment variables")

    # Initialize agent
    agent = WebMarketResearchAgent(api_key)

    while True:
        print("\n" + "="*50)
        print("Choose an option:")
        print("1. Conduct web-based market research")
        print("2. Load and display a saved report")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            topic = input("\nEnter the market research topic: ").strip()
            if topic:
                # Conduct research
                report = agent.conduct_web_research(topic)

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
                    # Reconstruct sources
                    sources = [WebSource(**source_data)
                               for source_data in data.get('data_sources', [])]
                    data['data_sources'] = sources
                    report = WebMarketResearchReport(**data)
                    agent.display_report(report)
            except FileNotFoundError:
                print(f"❌ File '{filename}' not found.")
            except Exception as e:
                print(f"❌ Error loading report: {str(e)}")

        elif choice == "3":
            print("👋 Thank you for using the Web Market Research Agent!")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
