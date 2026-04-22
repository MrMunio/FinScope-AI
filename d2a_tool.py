import asyncio
import aiohttp
import time
import logging
import json
from typing import List, Union, Dict, Any
from pydantic import BaseModel, Field
from newspaper import Article, Config as NewsConfig
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Separate class for Brave Web Search
class AsyncBraveSearch:
    def __init__(self, api_key: str, requests_per_second: float = 1.0):
        self.api_key = api_key
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time = 0
        self._semaphore = asyncio.Semaphore(1)

    async def _wait_for_rate_limit(self):
        """Async rate limiting"""
        async with self._semaphore:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            
            if time_since_last_request < self.min_interval:
                sleep_time = self.min_interval - time_since_last_request
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()

    async def search_single(self, query: str) -> dict:
        """Execute a single search query with rate limiting and retry logic"""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "offset": 0,  # Free tier only supports offset 0
            "count": 10,
            "search_lang": "en"
        }
        
        retry_count = 0
        max_retries = 3
        
        async with aiohttp.ClientSession() as session:
            while retry_count < max_retries:
                try:
                    await self._wait_for_rate_limit()
                    
                    async with session.get(
                        self.api_url,
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []
                            
                            for item in data.get("web", {}).get("results", []):
                                results.append({
                                    "title": item.get("title", ""),
                                    "snippet": item.get("description", ""),
                                    "url": item.get("url", "")
                                })
                            
                            return {
                                "query": query,
                                "results": results,
                                "status": "success"
                            }
                            
                        elif response.status == 429:
                            retry_count += 1
                            wait_time = min(2 ** retry_count, 8)
                            logger.warning(
                                f"Rate limit hit for query '{query}' "
                                f"(attempt {retry_count}/{max_retries}), "
                                f"waiting {wait_time} seconds..."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                            
                        elif response.status == 422:
                            error_text = await response.text()
                            logger.error(f"Validation error for query '{query}': {error_text}")
                            return {
                                "query": query,
                                "results": [],
                                "status": "validation_error",
                                "error": error_text
                            }
                            
                        else:
                            error_text = await response.text()
                            logger.error(f"Error {response.status} for query '{query}': {error_text}")
                            return {
                                "query": query,
                                "results": [],
                                "status": "error",
                                "error": f"HTTP {response.status}: {error_text}"
                            }
                            
                except asyncio.TimeoutError:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 8)
                        logger.warning(
                            f"Timeout for query '{query}' "
                            f"(attempt {retry_count}/{max_retries}), "
                            f"retrying in {wait_time} seconds..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Timeout after {max_retries} attempts for query '{query}'")
                        return {
                            "query": query,
                            "results": [],
                            "status": "timeout",
                            "error": "Request timeout after retries"
                        }
                        
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 8)
                        logger.warning(
                            f"Request failed for query '{query}': {e}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Request failed after {max_retries} attempts for query '{query}': {e}")
                        return {
                            "query": query,
                            "results": [],
                            "status": "error",
                            "error": str(e)
                        }
        
        return {
            "query": query,
            "results": [],
            "status": "error",
            "error": "Max retries exceeded"
        }

    async def search_multiple(self, queries: List[str]) -> List[dict]:
        """Execute multiple search queries sequentially"""
        results = []
        for idx, query in enumerate(queries, 1):
            logger.info(f"Processing query {idx}/{len(queries)}: {query}")
            result = await self.search_single(query)
            results.append(result)
        return results


# Separate class for URL Scraping
class AsyncURLScraper:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _scrape_single_sync(self, url: str) -> dict:
        """Synchronous scraping function to run in thread pool"""
        try:
            config = NewsConfig()
            config.request_timeout = self.timeout
            
            article = Article(url, config=config)
            article.download()
            article.parse()
            content = article.text.strip()
            
            return {
                "url": url,
                "content": content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "url": url,
                "content": "",
                "status": "error",
                "error": str(e)
            }

    async def scrape_single(self, url: str) -> dict:
        """Async wrapper for single URL scraping"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._scrape_single_sync, url)

    async def scrape_multiple(self, urls: List[str]) -> List[dict]:
        """Scrape multiple URLs concurrently"""
        tasks = [self.scrape_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    def cleanup(self):
        """Cleanup executor"""
        self.executor.shutdown(wait=False)


# Main Tools class
class Tools:
    class Valves(BaseModel):
        BRAVE_API_KEY: str = Field(
            default="", description="Brave Search API Key"
        )
        SCRAPER_TIMEOUT: int = Field(
            default=20, description="Timeout for URL scraping in seconds"
        )

    def __init__(self):
        self.valves = self.Valves()
        self._brave_search = None
        self._url_scraper = None

    def _get_brave_search(self) -> AsyncBraveSearch:
        """Lazy initialization of Brave Search client"""
        if self._brave_search is None:
            self._brave_search = AsyncBraveSearch(
                api_key=self.valves.BRAVE_API_KEY,
                requests_per_second=1.0  # Free tier limit
            )
        return self._brave_search

    def _get_url_scraper(self) -> AsyncURLScraper:
        """Lazy initialization of URL Scraper"""
        if self._url_scraper is None:
            self._url_scraper = AsyncURLScraper(timeout=self.valves.SCRAPER_TIMEOUT)
        return self._url_scraper

    async def web_search(
        self,
        queries: Union[str, List[str]] = Field(
            ..., description="Search query or list of search queries to execute"
        ),
    ) -> str:
        """
        Performs web search using Brave Search API for one or multiple queries.
        Queries are executed sequentially with rate limiting (1 req/sec for free tier).
        Returns structured JSON with search results containing titles, snippets, and URLs.
        """
        if isinstance(queries, str):
            queries = [queries]

        if not self.valves.BRAVE_API_KEY:
            return json.dumps({
                "error": "BRAVE_API_KEY not configured in Valves",
                "queries": queries,
                "results": []
            }, indent=2)

        search_client = self._get_brave_search()
        results = await search_client.search_multiple(queries)

        # Return structured JSON
        output = {
            "total_queries": len(queries),
            "results": results
        }
        
        return json.dumps(output, indent=2)

    async def scrape_urls(
        self,
        urls: Union[str, List[str]] = Field(
            ..., description="URL or list of URLs to scrape and extract main article content"
        ),
    ) -> str:
        """
        Scrapes and extracts the main article content from one or more URLs using the newspaper3k library.
        Multiple URLs are processed concurrently for better performance.
        Returns extracted text content for each URL.
        """
        if isinstance(urls, str):
            urls = [urls]

        scraper = self._get_url_scraper()
        results = await scraper.scrape_multiple(urls)

        # Format output
        output = []
        for result in results:
            output.append(f"URL: {result['url']}")
            output.append(f"Status: {result['status']}")
            
            if result['status'] == 'success':
                output.append(f"Content:\n{result['content']}")
            else:
                output.append(f"Error: {result.get('error', 'Unknown error')}")
            
            output.append("-" * 80)

        return "\n\n".join(output)

    async def agent_scratch_pad(
        self,
        thoughts: str = Field(
            ..., description="Agent's reasoning, thoughts, or scratch pad notes"
        ),
    ) -> str:
        """
        A scratch pad for the agent to record its thinking process and reasoning.
        This helps induce a thinking mode where the agent can work through problems step by step.
        Thoughts are logged but not stored permanently.
        """
        logger.info(f"Agent Scratch Pad - Thoughts: {thoughts}")
        return f"✓ Thoughts logged successfully. Continue with your reasoning process."


if __name__ == "__main__":
        
    async def test_web_search_and_scrape(tools):
        """Test web search with 3 queries and scrape the URLs from results"""
        print("\n" + "="*80)
        print("TEST: Web Search (3 Queries) + URL Scraping")
        print("="*80)
        
        # Step 1: Search with 3 queries
        queries = [
            "Python async programming",
            "FastAPI tutorial",
            "Machine learning basics"
        ]
        
        print(f"\n🔍 Searching for {len(queries)} queries...")
        search_result = await tools.web_search(queries)
        print("\n📊 Search Results (JSON):")
        print(search_result)
        
        # Step 2: Parse JSON to extract all URLs
        print("\n" + "-"*80)
        print("📋 Extracting URLs from search results...")
        
        search_data = json.loads(search_result)
        urls_to_scrape = []
        
        for result in search_data.get("results", []):
            if result.get("status") == "success":
                query = result.get("query", "")
                print(f"\n  Query: '{query}'")
                
                for idx, item in enumerate(result.get("results", []), 1):
                    url = item.get("url", "")
                    if url:
                        urls_to_scrape.append(url)
                        print(f"    [{idx}] {url}")
        
        # Step 3: Scrape all collected URLs
        if urls_to_scrape:
            print("\n" + "-"*80)
            print(f"🌐 Scraping {len(urls_to_scrape)} URLs concurrently...")
            print("-"*80)
            
            scrape_result = await tools.scrape_urls(urls_to_scrape)
            print("\n📄 Scraping Results:")
            print(scrape_result)
        else:
            print("\n⚠️  No URLs found in search results to scrape")


    async def main():
        """Main test function"""
        print("\n" + "#"*80)
        print("# WEB SEARCH + SCRAPING TEST")
        print("#"*80)
        
        # Initialize Tools
        tools = Tools()
        
        # Set your Brave API key here
        tools.valves.BRAVE_API_KEY = ""  # Replace with actual key
        tools.valves.SCRAPER_TIMEOUT = 20
        
        # Check if API key is set
        if not tools.valves.BRAVE_API_KEY or tools.valves.BRAVE_API_KEY == "YOUR_BRAVE_API_KEY_HERE":
            print("\n⚠️  WARNING: Please set your BRAVE_API_KEY in the code before running tests")
            print("Cannot proceed without API key.\n")
            return
        
        # Run the combined test
        await test_web_search_and_scrape(tools)
        
        # Cleanup
        if tools._url_scraper:
            tools._url_scraper.cleanup()
        
        print("\n" + "#"*80)
        print("# TEST COMPLETED")
        print("#"*80)

    # Run the async main function
    asyncio.run(main())