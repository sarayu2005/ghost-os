from agents.graph import graph
from services.news import fetch_ai_news
from db.database import get_user, store_news
import time

def display_content(content_outputs):
    """Display generated content"""
    if not content_outputs:
        return
    
    linkedin = content_outputs.get("linkedin")
    twitter = content_outputs.get("twitter")
    substack = content_outputs.get("substack")
    
    if linkedin:
        print("\n" + "="*60)
        print("📱 LINKEDIN POST")
        print("="*60)
        print(linkedin)
    
    if twitter:
        print("\n" + "="*60)
        print("🐦 TWITTER THREAD")
        print("="*60)
        for i, tweet in enumerate(twitter, 1):
            print(f"Tweet {i}: {tweet}\n")
    
    if substack:
        print("\n" + "="*60)
        print("📰 SUBSTACK ARTICLE")
        print("="*60)
        print(substack)

def run_pipeline():
    username = input("👤 Enter your username: ").strip()
    user_id = get_user(username)

    if not user_id:
        print(f"❌ User '{username}' not found. Run onboarding.py first.")
        return

    print(f"✅ Welcome {username}!")
    print("📡 Fetching real news...")

    news_list = fetch_ai_news("latest AI model release LLM 2026", max_results=3)

    if not news_list:
        print("❌ No news found")
        return

    for i, news in enumerate(news_list, 1):
        print(f"\n{'='*60}")
        print(f"Processing Story {i}: {news['title'][:50]}...")
        print(f"{'='*60}")

        news_id = store_news(
            news["title"],
            news["content"],
            news["url"],
            news["source"],
            0.0, 0.0
        )

        initial_state = {
            "user_id": user_id,
            "news_story": news["title"],
            "news_content": news["content"],
            "news_url": news["url"],
            "news_source": news["source"],
            "news_id": news_id,
            "relevance_score": 0.0,
            "novelty_score": 0.0,
            "belief_score": 0.0,
            "conviction_score": 0.0,
            "matched_beliefs": [],
            "opinion": "",
            "content_outputs": {},
            "user_approved": False
        }

        result = graph.invoke(initial_state)
        print(f"\n✅ FINAL CONVICTION SCORE: {result['conviction_score']:.2f}")

        if result["content_outputs"]:
            display_content(result["content_outputs"])
        else:
            print("\n❌ Story did not pass conviction gate. No content generated.")

        if result['matched_beliefs']:
            print(f"\n📝 Your beliefs matched:")
            for belief in result['matched_beliefs']:
                print(f"   • {belief['belief']}: {belief['match_score']:.2f} match")

        if i < len(news_list):
            print("\n⏳ Waiting 30s before next story (Groq rate limit)...")
            time.sleep(30)

if __name__ == "__main__":
    run_pipeline()

