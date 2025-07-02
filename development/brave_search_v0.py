import os
import requests
from typing import Optional
from dotenv import load_dotenv
from langchain_core.tools import tool
class WebSearch:
    def __init__(self, brave_api_key: str):
        self.brave_api_key = brave_api_key
        self.api_url = "https://api.search.brave.com/res/v1/web/search"

    def run(self, query: str, exact_term: str = "", start_page: int = 1, end_page: int = 1) -> list:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        all_results = []
        
        # Each page in Brave Search API represents 10 results
        # offset parameter starts from 0 for the first page
        for page in range(start_page, end_page + 1):
            offset = (page - 1) * 10
            
            # Construct the query with exact terms if provided
            search_query = f'{query} in {exact_term}' if exact_term else query
            
            params = {
                "q": search_query,
                "offset": offset,
                "count": 10,  # Number of results per page
                "search_lang": "en"
            }
            
            response = requests.get(self.api_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error in Brave Search API: {response.status_code} - {response.text}")
                continue
                
            data = response.json()
            
            # Extract results in the same format as the original function
            for item in data.get("web", {}).get("results", []):
                all_results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("description", ""),
                    "url": item.get("url", "")
                })

        return all_results

# Load Brave API key
load_dotenv()
brave_api_key = os.getenv("BRAVE_API_KEY")
web_search = WebSearch(brave_api_key=brave_api_key)

@tool
def brave_web_search(query:str)->str:
    """performs web search and returns search results"""
    results=web_search.run(query=query)
    import html
    import time
    time.sleep(2)
    formatted = []
    for i, entry in enumerate(results, 1):
        title = entry['title']
        url = entry['url']
        snippet = html.unescape(entry['snippet']).replace('<strong>', '').replace('</strong>', '')
        formatted.append(f"{i}. {title}\nURL: {url}\nSnippet: {snippet}\n")

    formatted_string = "\n".join(formatted)
    return formatted_string

# Test
if __name__ == "__main__":
    query = "Larsen and Turbo contact email india"
    exact_term = ""
    results = web_search.run(query=query, exact_term=exact_term, start_page=1, end_page=1)
    from pprint import pprint
    pprint(results)
    
    query = "cognizant"
    exact_term = ""
    results=web_search.run(query = query,exact_term = exact_term,start_page=1,end_page=1)

    from pprint import pprint
    pprint(results)
    query = "vipro"
    exact_term = ""
    results=web_search.run(query = query,exact_term = exact_term,start_page=1,end_page=1)

    from pprint import pprint
    pprint(results)
    query = "deloitte"
    exact_term = ""
    results=web_search.run(query = query,exact_term = exact_term,start_page=1,end_page=1)

    from pprint import pprint
    pprint(results)