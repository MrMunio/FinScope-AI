import os
import requests
import time
import threading
from typing import Optional, List, Dict
from dotenv import load_dotenv
from langchain_core.tools import tool
from queue import Queue
from functools import wraps
import asyncio
import aiohttp

class RateLimitedWebSearch:
    def __init__(self, brave_api_key: str, requests_per_second: float = 1.0):
        self.brave_api_key = brave_api_key
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time = 0
        self._lock = threading.Lock()
        
        # Request queue for batching
        self._request_queue = Queue()
        self._processing_queue = False

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        with self._lock:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            
            if time_since_last_request < self.min_interval:
                sleep_time = self.min_interval - time_since_last_request
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()

    def run(self, query: str, exact_term: str = "", start_page: int = 1, end_page: int = 1) -> list:
        """Rate-limited search with automatic throttling and Brave API limit handling"""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        all_results = []
        
        # Brave Search Free tier limitation: offset must be <= 9 (only first page allowed)
        # This means start_page and end_page should both be 1 for free tier
        if start_page > 1 or end_page > 1:
            print(f"Warning: Brave Search Free tier only supports page 1 (offset <= 9). Adjusting to page 1.")
            start_page = 1
            end_page = 1
        
        for page in range(start_page, end_page + 1):
            # Wait for rate limit before making request
            self._wait_for_rate_limit()
            
            # Calculate offset, but ensure it doesn't exceed 9 for free tier
            offset = (page - 1) * 10
            if offset > 9:
                print(f"Skipping page {page} as offset ({offset}) exceeds free tier limit (9)")
                continue
            
            search_query = f'{query} in {exact_term}' if exact_term else query
            
            params = {
                "q": search_query,
                "offset": offset,
                "count": 10,
                "search_lang": "en"
            }
            
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for item in data.get("web", {}).get("results", []):
                            all_results.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("description", ""),
                                "url": item.get("url", "")
                            })
                        break  # Success, exit retry loop
                        
                    elif response.status_code == 429:  # Rate limit exceeded
                        retry_count += 1
                        wait_time = min(2 ** retry_count, 8)  # Exponential backoff, max 8 seconds
                        print(f"Rate limit hit (attempt {retry_count}/{max_retries}), waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                        
                    elif response.status_code == 422:  # Validation error
                        error_data = response.json()
                        print(f"Validation error: {error_data.get('error', {}).get('detail', 'Unknown validation error')}")
                        # Check if it's an offset validation error
                        if 'offset' in str(error_data):
                            print("Offset validation failed - likely exceeds free tier limit")
                            return all_results  # Return what we have so far
                        break  # Don't retry validation errors
                        
                    else:
                        print(f"Error in Brave Search API: {response.status_code} - {response.text}")
                        break  # Don't retry other HTTP errors
                        
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 8)
                        print(f"Request failed (attempt {retry_count}/{max_retries}): {e}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Request failed after {max_retries} attempts: {e}")
                        break

        return all_results

    def batch_search(self, queries: List[Dict]) -> Dict[str, List]:
        """Process multiple queries sequentially with rate limiting"""
        results = {}
        
        for i, query_data in enumerate(queries):
            query = query_data.get('query', '')
            exact_term = query_data.get('exact_term', '')
            start_page = query_data.get('start_page', 1)
            end_page = query_data.get('end_page', 1)
            
            # print(f"Processing query {i+1}/{len(queries)}: {query}")
            
            try:
                search_results = self.run(
                    query=query, 
                    exact_term=exact_term, 
                    start_page=start_page, 
                    end_page=end_page
                )
                results[query] = search_results
            except Exception as e:
                print(f"Failed to process query '{query}': {e}")
                results[query] = []
                
        return results

# Async version for better concurrency control
class AsyncRateLimitedWebSearch:
    def __init__(self, brave_api_key: str, requests_per_second: float = 1.0):
        self.brave_api_key = brave_api_key
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time = 0
        self._semaphore = asyncio.Semaphore(1)  # Only 1 concurrent request

    async def _wait_for_rate_limit(self):
        """Async rate limiting"""
        async with self._semaphore:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            
            if time_since_last_request < self.min_interval:
                sleep_time = self.min_interval - time_since_last_request
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()

    async def run_async(self, query: str, exact_term: str = "", start_page: int = 1, end_page: int = 1) -> list:
        """Async rate-limited search with Brave API limit handling"""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        all_results = []
        
        # Handle Brave Search Free tier limitation
        if start_page > 1 or end_page > 1:
            print(f"Warning: Brave Search Free tier only supports page 1. Adjusting to page 1.")
            start_page = 1
            end_page = 1
        
        async with aiohttp.ClientSession() as session:
            for page in range(start_page, end_page + 1):
                await self._wait_for_rate_limit()
                
                offset = (page - 1) * 10
                if offset > 9:
                    print(f"Skipping page {page} as offset ({offset}) exceeds free tier limit")
                    continue
                
                search_query = f'{query} in {exact_term}' if exact_term else query
                
                params = {
                    "q": search_query,
                    "offset": offset,
                    "count": 10,
                    "search_lang": "en"
                }
                
                retry_count = 0
                max_retries = 3
                
                while retry_count < max_retries:
                    try:
                        async with session.get(self.api_url, headers=headers, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                for item in data.get("web", {}).get("results", []):
                                    all_results.append({
                                        "title": item.get("title", ""),
                                        "snippet": item.get("description", ""),
                                        "url": item.get("url", "")
                                    })
                                break
                                
                            elif response.status == 429:
                                retry_count += 1
                                wait_time = min(2 ** retry_count, 8)
                                print(f"Rate limit hit (attempt {retry_count}/{max_retries}), waiting {wait_time} seconds...")
                                await asyncio.sleep(wait_time)
                                continue
                                
                            elif response.status == 422:
                                error_text = await response.text()
                                print(f"Validation error: {error_text}")
                                if 'offset' in error_text:
                                    print("Offset validation failed - likely exceeds free tier limit")
                                    return all_results
                                break
                                
                            else:
                                error_text = await response.text()
                                print(f"Error: {response.status} - {error_text}")
                                break
                                
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = min(2 ** retry_count, 8)
                            print(f"Request failed (attempt {retry_count}/{max_retries}): {e}. Retrying in {wait_time} seconds...")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"Request failed after {max_retries} attempts: {e}")
                            break

        return all_results

# Decorator for rate limiting tool calls
def rate_limit_tool(requests_per_second: float = 1.0):
    def decorator(func):
        min_interval = 1.0 / requests_per_second
        last_call_time = [0]  # Use list to make it mutable in closure
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                current_time = time.time()
                time_since_last_call = current_time - last_call_time[0]
                
                if time_since_last_call < min_interval:
                    sleep_time = min_interval - time_since_last_call
                    time.sleep(sleep_time)
                
                last_call_time[0] = time.time()
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Load environment
load_dotenv()
brave_api_key = os.getenv("BRAVE_API_KEY")

# Initialize rate-limited search
rate_limited_web_search = RateLimitedWebSearch(brave_api_key=brave_api_key, requests_per_second=0.9)  # Slightly under 1 RPS

@tool
@rate_limit_tool(requests_per_second=0.9)
def brave_web_search_rate_limited(query: str) -> str:
    """Rate-limited web search tool that respects API limits"""
    results = rate_limited_web_search.run(query=query)
    import html
   
    formatted = []
    for i, entry in enumerate(results, 1):
        title = entry['title']
        url = entry['url']
        snippet = html.unescape(entry['snippet']).replace('<strong>', '').replace('</strong>', '')
        formatted.append(f"{i}. {title}\nURL: {url}\nSnippet: {snippet}\n")

    formatted_string = "\n".join(formatted)
    return formatted_string

# Batch processing tool
@tool
def batch_web_search(queries: List[str]) -> str:
    """
    Process multiple web search queries and returns concatinated result as string.
    """
    query_list = [{"query": q.strip()} for q in queries]
    results = rate_limited_web_search.batch_search(query_list)
    
    formatted_results = []
    for query, search_results in results.items():
        formatted_results.append(f"=== Results for: '{query}' ===")
        for i, entry in enumerate(search_results, 1):
            title = entry['title']
            url = entry['url']
            snippet = entry['snippet']
            formatted_results.append(f"{i}. {title}\nURL: {url}\nSnippet: {snippet}\n")
        formatted_results.append("--"*50)
    
    return "\n".join(formatted_results)

# Test the tools properly
if __name__ == "__main__":
    # # Test individual search tool
    # print("=== Testing Individual Search Tool ===")
    # try:
    #     result = brave_web_search_rate_limited.invoke({"query": "python programming"})
    #     print(result[:200] + "..." if len(result) > 200 else result)
    # except Exception as e:
    #     print(f"Individual search failed: {e}")
    
    # print("\n" + "="*50 + "\n")
    
    # Test batch search tool with correct format
    print("=== Testing Batch Search Tool ===")
    try:
        result = batch_web_search.invoke({"queries": ["google","facebook",]})
        print(result)
    except Exception as e:
        print(f"Batch search failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # # Test direct class usage (for debugging)
    # print("=== Testing Direct Class Usage ===")
    # try:clear
    #     queries = ["microsoft", "apple"]
    #     batch_results = rate_limited_web_search.batch_search(queries)
        
    #     for query, results in batch_results.items():
    #         print(f"\n=== Results for '{query}' ===")
    #         for result in results[:1]:  # Show first result only
    #             print(f"Title: {result['title']}")
    #             print(f"URL: {result['url']}")
    #             print(f"Snippet: {result['snippet'][:100]}...")
    #             print("-" * 30)
    # except Exception as e:
    #     print(f"Direct class usage failed: {e}")
    
    # # Original test format (corrected for free tier limitations)
    # print("\n" + "="*50 + "\n")
    # print("=== Testing Original Format (Dict-based) ===")
 