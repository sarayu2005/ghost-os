import os
from dotenv import load_dotenv
from tavily import TavilyClient

# 1. ALWAYS load the environment variables first!
load_dotenv()

# 2. NOW initialize the client after the key is loaded into the system memory
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def fetch_ai_news(query: str = "AI news latest", max_results: int = 5):
    """Fetch latest AI news"""
    results = tavily_client.search(
        query=query,
        include_answer=True,
        max_results=max_results
    )
    
    news_stories = []
    for result in results.get("results", []):
        news_stories.append({
            "title": result.get("title"),
            "content": result.get("content"),
            "url": result.get("url"),
            "source": result.get("source")
        })
    
    return news_stories

# 3. Add a quick test runner block to see results print out
if __name__ == "__main__":
    print("📡 Fetching news from Tavily...")
    stories = fetch_ai_news(max_results=2)
    for s in stories:
        print(f"\n📰 Title: {s['title']}\n🔗 Link: {s['url']}")