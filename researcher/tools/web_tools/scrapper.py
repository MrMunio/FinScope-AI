from newspaper import Article,Config
from typing import Union, List
from langchain_core.tools import tool

# Langchain tool for scraping URLs in batch and extracting main article content using newspaper3k library
@tool
def scrape_urls(urls: Union[str, List[str]]) -> str:
    """Scrapes and extracts the main article content from one or more URLs using the newspaper3k library."""
    if isinstance(urls, str):
        urls = [urls]

    config = Config()
    config.request_timeout = 20  # increase timeout in seconds

    results = []
    for url in urls:
        try:
            article = Article(url, config=config)
            article.download()
            article.parse()
            content = article.text.strip()
            results.append(f"URL: {url}\nContent:\n{content}\n{'-'*80}")
        except Exception as e:
            results.append(f"URL: {url}\nError: {str(e)}\n{'-'*80}")

    return "\n\n".join(results)


if __name__=="__main__":
    # Sample URLs to test
    test_urls = [
        "https://www.larsentoubro.com/", 
        "https://www.larsentoubro.com/corporate/contact-us/"
    ]

    # Call the tool
    result = scrape_urls.invoke({"urls": test_urls})

    # Print the result
    print(result)