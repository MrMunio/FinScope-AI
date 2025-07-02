# utils/pse_web_search.py
from typing import List
import requests
import json
import time
import threading
import html
from langchain_core.tools import tool
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,filename='logs/web_search.log',)
logger = logging.getLogger(__name__)

class BatchWebSearch:
    def __init__(
        self,
        pse_api_key: str,
        pse_cx: str,
        requests_per_second: float = 0.5,  # Conservative for free tier
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        self.pse_api_key = pse_api_key
        self.pse_cx = pse_cx
        self.requests_per_second = requests_per_second
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Rate limiting
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()

    def _rate_limit(self):
        """Ensure we don't exceed the rate limit"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()

    def _make_request_with_retry(self, url: str, query: str) -> dict:
        """Make HTTP request with exponential backoff retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                self._rate_limit()
                
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "error" in data:
                    error_msg = data['error'].get('message', 'Unknown error')
                    error_code = data['error'].get('code', 'Unknown code')
                    
                    if error_code == 429 or 'rate limit' in error_msg.lower():
                        if attempt < self.max_retries:
                            wait_time = (self.backoff_factor ** attempt) * 2
                            logger.warning(f"Rate limit hit for query '{query}', retrying in {wait_time} seconds")
                            time.sleep(wait_time)
                            continue
                    
                    logger.error(f"Google PSE API error for query '{query}': {error_msg}")
                    return {"items": []}
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = (self.backoff_factor ** attempt)
                    logger.warning(f"Request failed for query '{query}', retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed for query '{query}' after {self.max_retries} retries")
                    return {"items": []}
        
        return {"items": []}

    def search_single(self, query: str, exact_term: str = "") -> List[dict]:
        """Search for a single query"""
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.pse_api_key}&cx={self.pse_cx}&exactTerms={exact_term}&gl=IN&hl=en-IN"
        
        logger.info(f"Searching for: {query}")
        data = self._make_request_with_retry(url, query)
        
        results = []
        items = data.get("items", [])
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", "")
            })
        
        logger.info(f"Retrieved {len(results)} results for: {query}")
        return results

    def batch_search(self, queries: List[str], exact_term: str = "") -> str:
        """
        Search multiple queries sequentially and return formatted concatenated results
        
        Args:
            queries: List of search queries
            exact_term: Optional exact term to include in all searches
            
        Returns:
            Formatted string with all results concatenated
        """
        if not queries:
            return "No queries provided."
        
        all_formatted_results = []
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Processing query {i}/{len(queries)}: {query}")
            
            # Search for this query
            results = self.search_single(query, exact_term)
            
            # Format results for this query
            if results:
                query_section = f"=== QUERY {i}: {query} ===\n"
                formatted_results = []
                
                for j, result in enumerate(results, 1):
                    title = result['title']
                    url = result['url']
                    snippet = html.unescape(result['snippet']).replace('<strong>', '').replace('</strong>', '')
                    formatted_results.append(f"{j}. {title}\nURL: {url}\nSnippet: {snippet}\n")
                
                query_results = "\n".join(formatted_results)
                all_formatted_results.append(f"{query_section}{query_results}")
            else:
                all_formatted_results.append(f"=== QUERY {i}: {query} ===\nNo results found.\n")
        
        # Concatenate all results
        final_result = "\n" + "="*50 + "\n".join(all_formatted_results) + "="*50
        
        logger.info(f"Completed batch search for {len(queries)} queries")
        return final_result


# Initialize the web search tool
import os
from dotenv import load_dotenv
load_dotenv()

pse_api_key = os.getenv("PSE_API_KEY")
pse_cx = os.getenv("PSE_ENGINE_ID")

# Create the batch search instance
batch_web_search = BatchWebSearch(
    pse_api_key=pse_api_key,
    pse_cx=pse_cx,
    requests_per_second=0.5  # Conservative for free tier
)

@tool
def batch_pse_web_search(queries: List[str]) -> str:
    """
    Performs batch web search for multiple queries and returns formatted concatenated results.
    """
    exact_term: str = ""
    try:
        if not queries:
            return "Error: No queries provided."
        
        if not isinstance(queries, list):
            return "Error: Queries must be provided as a list."
        
        # Convert any non-string queries to strings
        queries = [str(q).strip() for q in queries if str(q).strip()]
        
        if not queries:
            return "Error: No valid queries after filtering."
        
        logger.info(f"Starting batch search for {len(queries)} queries")
        result = batch_web_search.batch_search(queries, exact_term)
        
        return result
        
    except Exception as e:
        logger.error(f"Batch search failed: {str(e)}")
        return f"Batch search failed: {str(e)}"


if __name__ == "__main__":
    # Test the batch search tool
    test_queries = [
        "Larsen and Turbo contact email india",
        "Larsen Turbo customer support",
        "L&T contact information"
    ]
    
    print("Testing batch search...")
    result = batch_pse_web_search({"queries":test_queries})
    print(result)