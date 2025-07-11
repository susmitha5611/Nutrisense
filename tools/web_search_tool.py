import os
import time
import hashlib
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import json
import exa_py
from loguru import logger
from datetime import datetime, timedelta

# Simple in-memory cache for search results
class SearchCache:
    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        self.cache = {}
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.last_cleanup = datetime.now()
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        if datetime.now() - self.last_cleanup < timedelta(hours=1):
            return
        
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > timedelta(hours=self.ttl_hours)
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        self.last_cleanup = current_time
    
    def get(self, query: str) -> Optional[str]:
        """Get cached result for a query"""
        self._cleanup_expired()
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        
        if query_hash in self.cache:
            result, timestamp = self.cache[query_hash]
            if datetime.now() - timestamp < timedelta(hours=self.ttl_hours):
                logger.info(f"Cache hit for query: {query}")
                return result
            else:
                del self.cache[query_hash]
        
        return None
    
    def set(self, query: str, result: str):
        """Cache a search result"""
        self._cleanup_expired()
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[query_hash] = (result, datetime.now())
        logger.info(f"Cached result for query: {query}")

# Global cache instance
search_cache = SearchCache()

# Rate limiting
class RateLimiter:
    def __init__(self, max_requests: int = 20, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding rate limit"""
        current_time = datetime.now()
        # Remove requests outside the window
        self.requests = [
            req_time for req_time in self.requests
            if current_time - req_time < timedelta(minutes=self.window_minutes)
        ]
        
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record a new request"""
        self.requests.append(datetime.now())

# Global rate limiter
rate_limiter = RateLimiter()

def get_exa_client():
    """Get Exa client with API key from environment"""
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        logger.error("EXA_API_KEY not found in environment variables")
        return None
    return exa_py.Exa(exa_api_key)

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "exa_web_search",
        "description": "Search the web for real-time information using Exa's neural search engine. Useful for finding current nutrition trends, health information, recipes, and dietary advice.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information on the web"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (default: 5, max: 10)",
                    "default": 5
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Whether to include the full text content of the pages (default: true)",
                    "default": True
                }
            },
            "required": ["query"]
        }
    }
}

class WebSearchResult(BaseModel):
    """Structure for web search results"""
    title: str = Field(description="Title of the web page")
    url: str = Field(description="URL of the web page")
    content: str = Field(description="Content snippet from the web page")
    published_date: str = Field(description="Published date if available", default="Not available")

def exa_web_search(query: str, num_results: int = 5, include_content: bool = True) -> str:
    """
    Search the web using Exa's neural search engine with caching and rate limiting.
    
    Args:
        query: The search query
        num_results: Number of results to return (max 10)
        include_content: Whether to include full text content
        
    Returns:
        JSON string containing search results
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            return json.dumps({
                "error": "Search query cannot be empty"
            })
        
        query = query.strip()
        num_results = min(max(num_results, 1), 10)  # Clamp between 1 and 10
        
        # Check cache first
        cache_key = f"{query}_{num_results}_{include_content}"
        cached_result = search_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Check rate limit
        if not rate_limiter.can_make_request():
            return json.dumps({
                "error": "Rate limit exceeded. Please try again later.",
                "query": query,
                "cached": False
            })
        
        # Get Exa client
        exa = get_exa_client()
        if not exa:
            return json.dumps({
                "error": "Exa API key not configured. Please add EXA_API_KEY to your environment variables."
            })
        
        logger.info(f"Performing web search with query: {query}")
        
        # Record the request for rate limiting
        rate_limiter.record_request()
        
        # Perform search with timeout and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if include_content:
                    search_response = exa.search_and_contents(
                        query,
                        num_results=num_results,
                        text=True,
                        highlights=True
                    )
                else:
                    search_response = exa.search(
                        query,
                        num_results=num_results
                    )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Search attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
        
        # Process results
        results = []
        for result in search_response.results:
            content = ""
            if hasattr(result, 'text') and result.text:
                # Limit content length to avoid overwhelming responses
                content = result.text[:800] + "..." if len(result.text) > 800 else result.text
            
            search_result = {
                "title": result.title[:200] if result.title else "No title",  # Limit title length
                "url": result.url,
                "content": content if content else "No content available",
                "published_date": getattr(result, 'published_date', 'Not available')
            }
            results.append(search_result)
        
        # Create response
        response_data = {
            "status": "success",
            "query": query,
            "num_results": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        
        result_json = json.dumps(response_data, indent=2)
        
        # Cache the result
        search_cache.set(cache_key, result_json)
        
        logger.info(f"Web search completed successfully. Found {len(results)} results.")
        return result_json
        
    except Exception as e:
        logger.error(f"Error during web search: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": f"Web search failed: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        })

# Export the tool and function for use in other modules
__all__ = ["WEB_SEARCH_TOOL", "exa_web_search"] 