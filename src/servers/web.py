from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS
import trafilatura

mcp = FastMCP("PolymathWeb")

@mcp.tool()
def search_internet(query: str, max_results: int = 5) -> str:
    """Search the internet for up-to-date information."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        
        output = []
        for r in results:
            output.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}\n---")
        return "\n".join(output)
    except Exception as e:
        return f"Search error: {str(e)}"

@mcp.tool()
def fetch_page(url: str) -> str:
    """Fetch and extract main content from a URL."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return f"Error: Failed to fetch {url}"
            
        result = trafilatura.extract(downloaded)
        if not result:
            return "Error: Could not extract content from page."
            
        return result
    except Exception as e:
        return f"Fetch error: {str(e)}"

if __name__ == "__main__":
    mcp.run()