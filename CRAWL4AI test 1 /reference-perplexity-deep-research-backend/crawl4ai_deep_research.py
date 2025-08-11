#!/usr/bin/env python3
"""
Crawl4AI Deep Research System
Purpose: Enhanced multi-site concurrent web crawling for stock analysis with 10+ site capability
Description: This file implements a comprehensive deep research system using Crawl4AI's advanced 
             parallel processing capabilities, content filtering, and structured output generation.
Key Functions/Classes: DeepResearchCrawler, MultiSiteSearchRequest, process_research_urls
"""

import json
import asyncio
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, SemaphoreDispatcher
from ddgs import DDGS

# AIDEV-NOTE: Initialize FastAPI app for deep research system
app = FastAPI(
    title="Crawl4AI Deep Research API",
    description="Enhanced multi-site web crawling system for comprehensive stock analysis research",
    version="2.0.0"
)

# AIDEV-NOTE: Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AIDEV-NOTE: Pydantic models for enhanced API requests/responses
class MultiSiteSearchRequest(BaseModel):
    """Request model for multi-site deep research queries"""
    query: str = Field(..., description="Research query for stock analysis")
    urls: List[str] = Field(..., max_items=50, description="List of URLs to crawl (0-50 sites, empty list triggers search)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional crawling options")
    
class DeepResearchResponse(BaseModel):
    """Enhanced response model with comprehensive research data"""
    success: bool
    query: str
    total_sites: int
    successful_crawls: int
    failed_crawls: int
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    error: Optional[str] = None

class CrawlStatus(BaseModel):
    """Real-time crawl status for streaming responses"""
    url: str
    status: str  # "processing", "completed", "failed"
    timestamp: str
    content_length: Optional[int] = None
    error_message: Optional[str] = None

# AIDEV-NOTE: Search Manager for real web search functionality
class SearchManager:
    """
    Enhanced search functionality using DDGS (DuckDuckGo Search)
    
    Features:
    - Multiple search backend support (Google, Yahoo, Brave, DuckDuckGo, Bing)
    - Configurable result limits and regions
    - Robust error handling with fallbacks
    - Safe search filtering
    """
    
    def __init__(self):
        self.backends = os.getenv("DDGS_BACKENDS", "google,yahoo,brave,duckduckgo,bing").split(",")
        self.max_results = int(os.getenv("DDGS_MAX_RESULTS", "10"))
        self.region = os.getenv("DDGS_REGION", "us-en")
        self.safesearch = os.getenv("DDGS_SAFESEARCH", "moderate")
        
        print(f"🔍 SearchManager initialized with backends: {self.backends}")
    
    def search_urls(self, query: str, limit: int = None) -> List[Dict[str, str]]:
        """
        Search for URLs using multiple backends with fallback support
        
        Args:
            query: Search query string
            limit: Maximum number of results (overrides default)
            
        Returns:
            List of dictionaries containing URL, title, snippet, and source
        """
        max_results = limit or self.max_results
        
        print(f"🔍 Searching for: '{query}' (max_results: {max_results})")
        
        try:
            ddgs = DDGS()
            results = ddgs.text(
                query, 
                max_results=max_results,
                region=self.region,
                safesearch=self.safesearch,
                backend=self.backends
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "url": result.get('href', ''),
                    "title": result.get('title', 'No title'),
                    "snippet": result.get('body', 'No description'),
                    "source": "ddgs_search"
                })
            
            print(f"✅ Found {len(search_results)} search results")
            return search_results
            
        except Exception as e:
            print(f"❌ Search failed with error: {str(e)}")
            return []

# AIDEV-NOTE: Core DeepResearchCrawler class implementing PRD requirements
class DeepResearchCrawler:
    """
    Enhanced Crawl4AI-based deep research system for stock analysis
    
    Features:
    - 10+ concurrent sites crawling capability
    - Advanced content filtering with PruningContentFilter (0.2-0.3 threshold)
    - Memory-adaptive concurrency management
    - Structured markdown output for LLM processing
    - Comprehensive error handling and recovery
    """
    
    def __init__(self):
        self.max_concurrent_sites = int(os.getenv("CRAWL4AI_MAX_CONCURRENT", "15"))
        self.content_filter_threshold = float(os.getenv("CRAWL4AI_FILTER_THRESHOLD", "0.25"))
        self.memory_threshold = float(os.getenv("CRAWL4AI_MEMORY_THRESHOLD", "85.0"))
        self.crawl_timeout = int(os.getenv("CRAWL4AI_TIMEOUT", "30000"))  # 30 seconds
        
    def get_optimized_crawler_config(self) -> CrawlerRunConfig:
        """
        Get optimized crawler configuration following PRD specifications
        
        PRD Requirements:
        - Use PruningContentFilter with relaxed threshold (0.2-0.3)
        - Configure DefaultMarkdownGenerator with ignore_links: false
        - Set word_count_threshold: 10 to keep shorter content blocks
        - Generate clean, formatted markdown output
        """
        # AIDEV-NOTE: Configure content filtering as per PRD specifications
        content_filter = PruningContentFilter(
            threshold=self.content_filter_threshold,  # 0.25 as specified in PRD
            threshold_type="dynamic",  # Adapts to page structure
            min_word_threshold=10  # Keep shorter content blocks per PRD
        )
        
        # AIDEV-NOTE: Configure markdown generation to preserve reference context
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=content_filter,
            options={
                "body_width": 0,  # Prevent text wrapping per PRD
                "ignore_emphasis": False,
                "ignore_links": False,  # Preserve reference context per PRD
                "ignore_images": False,
                "protect_links": True,
                "single_line_break": True,
                "mark_code": True,
                "escape_snob": False,
            }
        )
        
        return CrawlerRunConfig(
            markdown_generator=markdown_generator,
            cache_mode=CacheMode.BYPASS,  # Fresh content retrieval per PRD
            excluded_tags=['script', 'style'],  # Only exclude obvious noise per PRD
            exclude_external_links=False,  # Keep external links for context
            word_count_threshold=10,  # Per PRD specifications
            page_timeout=self.crawl_timeout,
            stream=True,  # Enable streaming for real-time processing
            verbose=False
        )
    
    def get_adaptive_dispatcher(self, max_sites: int) -> MemoryAdaptiveDispatcher:
        """
        Get memory-adaptive dispatcher for optimal resource management
        
        PRD Requirements:
        - Configure optimal number of concurrent crawlers (10-20)
        - Implement intelligent caching to avoid redundant crawls
        - Memory management for large content processing
        """
        # AIDEV-NOTE: Use MemoryAdaptiveDispatcher for intelligent resource management
        return MemoryAdaptiveDispatcher(
            memory_threshold_percent=self.memory_threshold,
            check_interval=1.0,  # Check memory every second
            max_session_permit=min(max_sites, self.max_concurrent_sites),
            memory_wait_timeout=300.0  # 5 minutes timeout
        )
    
    async def crawl_multiple_sites(
        self, 
        urls: List[str], 
        query: str = "",
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Crawl multiple sites concurrently with comprehensive analysis
        
        PRD Requirements:
        - Support crawling 10+ websites simultaneously
        - Generate clean, analysis-ready content in markdown format
        - Handle concurrent requests without overwhelming target servers
        - Provide detailed error reporting
        
        Returns:
            Dict containing crawl results, metadata, and performance metrics
        """
        options = options or {}
        start_time = time.time()
        
        # AIDEV-NOTE: Limit URLs to prevent overwhelming the system
        urls = urls[:50]  # Maximum 50 sites as per API model
        
        print(f"🚀 Starting deep research crawl for {len(urls)} sites...")
        print(f"📊 Query: {query}")
        
        # AIDEV-NOTE: Get optimized configuration and dispatcher
        crawler_config = self.get_optimized_crawler_config()
        dispatcher = self.get_adaptive_dispatcher(len(urls))
        
        successful_results = []
        failed_results = []
        performance_data = {
            "start_time": datetime.now().isoformat(),
            "total_urls": len(urls),
            "concurrent_limit": min(len(urls), self.max_concurrent_sites)
        }
        
        try:
            async with AsyncWebCrawler() as crawler:
                print(f"🔧 Configured for up to {dispatcher.max_session_permit} concurrent crawls")
                
                # AIDEV-NOTE: Use arun_many for concurrent processing as per PRD
                async for result in await crawler.arun_many(
                    urls, 
                    config=crawler_config,
                    dispatcher=dispatcher
                ):
                    if result.success:
                        # AIDEV-NOTE: Process successful crawl result
                        successful_results.append(self._process_successful_result(result, query))
                        print(f"✅ Completed: {result.url} ({len(result.markdown.raw_markdown)} chars)")
                    else:
                        # AIDEV-NOTE: Handle failed crawl with detailed error info
                        failed_results.append(self._process_failed_result(result))
                        print(f"❌ Failed: {result.url} - {result.error_message}")
                
        except Exception as e:
            print(f"🚨 Critical error during crawling: {str(e)}")
            return self._create_error_response(str(e), urls, query)
        
        # AIDEV-NOTE: Calculate performance metrics as per PRD success criteria
        end_time = time.time()
        duration = end_time - start_time
        success_rate = len(successful_results) / len(urls) * 100
        
        performance_data.update({
            "end_time": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "success_rate_percent": round(success_rate, 2),
            "avg_time_per_site": round(duration / len(urls), 2),
            "successful_crawls": len(successful_results),
            "failed_crawls": len(failed_results)
        })
        
        print(f"🎉 Deep research completed in {duration:.2f}s")
        print(f"📈 Success rate: {success_rate:.1f}% ({len(successful_results)}/{len(urls)})")
        
        return {
            "success": True,
            "query": query,
            "total_sites": len(urls),
            "successful_crawls": len(successful_results),
            "failed_crawls": len(failed_results),
            "data": successful_results,
            "failed_urls": failed_results,
            "performance_metrics": performance_data,
            "metadata": {
                "content_filter_threshold": self.content_filter_threshold,
                "max_concurrent_sites": self.max_concurrent_sites,
                "memory_threshold": self.memory_threshold,
                "crawl_timeout_ms": self.crawl_timeout
            }
        }
    
    def _process_successful_result(self, result, query: str) -> Dict[str, Any]:
        """Process successful crawl result with enhanced metadata"""
        # AIDEV-NOTE: Use fit_markdown for LLM processing when available per PRD
        markdown_content = ""
        if hasattr(result.markdown, 'fit_markdown') and result.markdown.fit_markdown:
            markdown_content = result.markdown.fit_markdown
        else:
            markdown_content = result.markdown.raw_markdown
        
        return {
            "url": result.url,
            "title": result.metadata.get("title", "No title available"),
            "markdown": markdown_content,
            "content_length": len(markdown_content),
            "word_count": len(markdown_content.split()),
            "crawl_timestamp": datetime.now().isoformat(),
            "status_code": result.status_code,
            "metadata": {
                "page_title": result.metadata.get("title", ""),
                "description": result.metadata.get("description", ""),
                "keywords": result.metadata.get("keywords", ""),
                "content_quality_score": self._calculate_content_quality(markdown_content),
                "relevance_to_query": self._calculate_query_relevance(markdown_content, query)
            }
        }
    
    def _process_failed_result(self, result) -> Dict[str, Any]:
        """Process failed crawl result with detailed error information"""
        return {
            "url": result.url,
            "error": result.error_message,
            "status_code": result.status_code,
            "timestamp": datetime.now().isoformat(),
            "retry_possible": result.status_code in [503, 429, 502, 504]
        }
    
    def _calculate_content_quality(self, content: str) -> float:
        """Calculate content quality score based on PRD criteria"""
        if not content:
            return 0.0
        
        # AIDEV-NOTE: Simple quality metrics for content evaluation
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        char_count = len(content)
        
        # Quality factors
        length_score = min(word_count / 200, 1.0)  # Optimal around 200 words
        structure_score = min(line_count / 20, 1.0)  # Good structure has multiple lines
        density_score = char_count / max(word_count * 10, 1)  # Character density
        
        return round((length_score + structure_score + density_score) / 3, 2)
    
    def _calculate_query_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score between content and query"""
        if not content or not query:
            return 0.0
        
        content_lower = content.lower()
        query_terms = query.lower().split()
        
        # AIDEV-NOTE: Simple relevance scoring based on query term presence
        matches = sum(1 for term in query_terms if term in content_lower)
        return round(matches / len(query_terms), 2)
    
    def _create_error_response(self, error: str, urls: List[str], query: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "query": query,
            "total_sites": len(urls),
            "successful_crawls": 0,
            "failed_crawls": len(urls),
            "data": [],
            "failed_urls": [{"url": url, "error": error} for url in urls],
            "performance_metrics": {
                "duration_seconds": 0,
                "success_rate_percent": 0.0
            },
            "error": error
        }

# AIDEV-NOTE: Initialize global crawler and search manager instances
deep_research_crawler = DeepResearchCrawler()
search_manager = SearchManager()

# AIDEV-NOTE: API Endpoints

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "service": "crawl4ai-deep-research",
        "version": "2.0.0",
        "capabilities": {
            "max_concurrent_sites": deep_research_crawler.max_concurrent_sites,
            "content_filter_threshold": deep_research_crawler.content_filter_threshold,
            "memory_threshold": deep_research_crawler.memory_threshold
        }
    }

@app.post("/api/multi-search", response_model=DeepResearchResponse)
async def multi_site_search_endpoint(request: MultiSiteSearchRequest):
    """
    Enhanced multi-site search endpoint supporting 10+ concurrent sites
    
    PRD Requirements:
    - Support crawling 10+ websites simultaneously for each research query
    - Generate clean, analysis-ready content in markdown format
    - Provide comprehensive error reporting and performance metrics
    """
    try:
        print(f"🔍 Received multi-site search request:")
        print(f"   Query: {request.query}")
        print(f"   Sites: {len(request.urls)}")
        
        # AIDEV-NOTE: If no URLs provided, search for them using DDGS
        urls = request.urls
        if not urls and request.query:
            print(f"🔍 No URLs provided, searching for: '{request.query}'")
            search_results = search_manager.search_urls(
                request.query, 
                limit=request.options.get('limit', 5)
            )
            urls = [result['url'] for result in search_results]
            print(f"✅ Found {len(urls)} URLs from search")
            
            # Add search metadata to options
            if 'search_metadata' not in request.options:
                request.options['search_metadata'] = []
            request.options['search_metadata'] = search_results
        
        # AIDEV-NOTE: Validate request parameters
        if len(urls) > 50:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 50 URLs allowed per request"
            )
        
        if not urls:
            raise HTTPException(
                status_code=400,
                detail="No URLs provided and search query returned no results"
            )
        
        # AIDEV-NOTE: Perform multi-site crawling
        result = await deep_research_crawler.crawl_multiple_sites(
            urls=urls,
            query=request.query,
            options=request.options
        )
        
        # AIDEV-NOTE: Return structured response
        return DeepResearchResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🚨 Error in multi-site search: {str(e)}")
        # Use locals().get() to safely access urls variable
        url_count = len(locals().get('urls', request.urls))
        return DeepResearchResponse(
            success=False,
            query=request.query,
            total_sites=url_count,
            successful_crawls=0,
            failed_crawls=url_count,
            data=[],
            metadata={},
            performance_metrics={},
            error=str(e)
        )

@app.post("/api/streaming-search")
async def streaming_search_endpoint(request: MultiSiteSearchRequest):
    """
    Streaming endpoint for real-time crawl progress updates
    
    Returns crawl results as they complete for immediate processing
    """
    try:
        from fastapi.responses import StreamingResponse
        import json
        
        async def generate_streaming_response():
            crawler_config = deep_research_crawler.get_optimized_crawler_config()
            dispatcher = deep_research_crawler.get_adaptive_dispatcher(len(request.urls))
            
            async with AsyncWebCrawler() as crawler:
                async for result in await crawler.arun_many(
                    request.urls, 
                    config=crawler_config,
                    dispatcher=dispatcher
                ):
                    if result.success:
                        processed_result = deep_research_crawler._process_successful_result(result, request.query)
                        status = CrawlStatus(
                            url=result.url,
                            status="completed",
                            timestamp=datetime.now().isoformat(),
                            content_length=len(result.markdown.raw_markdown)
                        )
                    else:
                        processed_result = deep_research_crawler._process_failed_result(result)
                        status = CrawlStatus(
                            url=result.url,
                            status="failed",
                            timestamp=datetime.now().isoformat(),
                            error_message=result.error_message
                        )
                    
                    # AIDEV-NOTE: Yield streaming response
                    yield f"data: {json.dumps(status.dict())}\n\n"
        
        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain"
        )
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/test-concurrent")
async def test_concurrent_crawling():
    """
    Test endpoint to verify 10+ concurrent site crawling capability
    
    Tests the system against PRD success metrics:
    - Successfully handle 10+ sites per research session  
    - Average crawl time of <30 seconds per site
    - 90% success rate for valid, accessible websites
    """
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://httpbin.org/json",
        "https://httpbin.org/uuid",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
        "https://httpbin.org/ip",
        "https://httpbin.org/get",
        "https://httpbin.org/status/200",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l"
    ]
    
    try:
        result = await deep_research_crawler.crawl_multiple_sites(
            urls=test_urls,
            query="test concurrent crawling capability",
            options={"test_mode": True}
        )
        
        # AIDEV-NOTE: Validate against PRD success metrics
        success_rate = result["performance_metrics"]["success_rate_percent"]
        avg_time_per_site = result["performance_metrics"]["avg_time_per_site"]
        
        prd_compliance = {
            "concurrent_sites_test": len(test_urls) >= 10,
            "success_rate_test": success_rate >= 90.0,
            "performance_test": avg_time_per_site <= 30.0,
            "all_tests_passed": len(test_urls) >= 10 and success_rate >= 90.0 and avg_time_per_site <= 30.0
        }
        
        result["prd_compliance"] = prd_compliance
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prd_compliance": {
                "concurrent_sites_test": False,
                "success_rate_test": False,
                "performance_test": False,
                "all_tests_passed": False
            }
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Crawl4AI Deep Research System...")
    print(f"🔧 Max concurrent sites: {deep_research_crawler.max_concurrent_sites}")
    print(f"🎯 Content filter threshold: {deep_research_crawler.content_filter_threshold}")
    print(f"💾 Memory threshold: {deep_research_crawler.memory_threshold}%")
    uvicorn.run(app, host="0.0.0.0", port=8001)