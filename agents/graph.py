from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Any, List
from pydantic import BaseModel
from services.news import fetch_ai_news
from agents.scorers import score_relevance, score_novelty
from agents.content_generator import generate_linkedin_post, generate_twitter_thread, generate_substack_article
from agents.belief_matcher import match_beliefs_to_news
from db.database import store_news

class PipelineState(TypedDict):
    user_id: int
    news_story: str
    news_content: str
    news_url: str
    news_source: str
    news_id: int
    relevance_score: float
    novelty_score: float
    belief_score: float
    conviction_score: float
    matched_beliefs: List[dict]
    opinion: str
    content_outputs: dict
    user_approved: bool


def content_generator_agent(state: PipelineState) -> PipelineState:
    """Generate content for stories that pass the conviction gate"""
    if state["conviction_score"] < 0.65:
        print("\n❌ Story did not pass conviction gate (< 0.65)")
        print("   No content generated.")
        return state
    
    print("\n✨ Generating content for passing story...")
    
    print("\n📱 Generating LinkedIn post...")
    linkedin = generate_linkedin_post(
        state['news_story'],
        state['news_content'],
        state['matched_beliefs'],
        state['conviction_score']
    )
    
    print("🐦 Generating Twitter thread...")
    twitter = generate_twitter_thread(
        state['news_story'],
        state['news_content'],
        state['matched_beliefs']
    )
    
    print("📰 Generating Substack article...")
    substack = generate_substack_article(
        state['news_story'],
        state['news_content'],
        state['matched_beliefs'],
        state['conviction_score']
    )
    
    state["content_outputs"] = {
        "linkedin": linkedin,
        "twitter": twitter,
        "substack": substack
    }
    
    return state

workflow = StateGraph(PipelineState)

def filter_agent(state: PipelineState) -> PipelineState:
    """Filter news by relevance to user interests"""
    print(f"\n🔍 Filter Agent: Scoring '{state['news_story'][:50]}...'")
    relevance = score_relevance(state['news_story'], state['news_content'])
    state["relevance_score"] = relevance
    print(f"   Relevance Score: {relevance:.2f}")
    return state

def novelty_agent(state: PipelineState) -> PipelineState:
    """Check if topic is already saturated"""
    print(f"✨ Novelty Agent: Evaluating novelty...")
    novelty = score_novelty(state['news_story'], state['news_content'])
    state["novelty_score"] = novelty
    print(f"   Novelty Score: {novelty:.2f}")
    return state

def belief_matcher_agent(state: PipelineState) -> PipelineState:
    """Match news against user's personal beliefs"""
    print(f"💭 Belief Matcher: Checking alignment with your values...")
    
    # Match beliefs to news
    result = match_beliefs_to_news(
        state['user_id'],
        state['news_story'],
        state['news_content'],
        state['news_id']
    )
    
    state["matched_beliefs"] = result['matched_beliefs']
    state["belief_score"] = result['overall_belief_score']
    print(f"   Belief Match Score: {result['overall_belief_score']:.2f}")
    
    if state["matched_beliefs"]:
        print(f"   Matched {len(state['matched_beliefs'])} of your beliefs:")
        for belief in state["matched_beliefs"][:3]:  # Show top 3
            print(f"      • {belief['belief'][:50]}... ({belief['match_score']:.2f})")
    
    return state

def conviction_scorer(state: PipelineState) -> PipelineState:
    """Calculate final conviction score (combo of relevance, novelty, beliefs)"""
    # Weight: Relevance 35%, Novelty 30%, Beliefs 35%
    score = (
        state["relevance_score"] * 0.35 + 
        state["novelty_score"] * 0.30 + 
        state["belief_score"] * 0.35
    )
    state["conviction_score"] = score
    print(f"🎯 Final Conviction Score: {score:.2f}")
    return state

# Wire everything together
workflow.add_node("filter_agent", filter_agent)
workflow.add_node("novelty_agent", novelty_agent)
workflow.add_node("belief_matcher_agent", belief_matcher_agent)
workflow.add_node("conviction_scorer", conviction_scorer)
workflow.add_node("content_generator_agent", content_generator_agent)

workflow.add_edge(START, "filter_agent")
workflow.add_edge("filter_agent", "novelty_agent")
workflow.add_edge("novelty_agent", "belief_matcher_agent")
workflow.add_edge("belief_matcher_agent", "conviction_scorer")

def should_continue(state: PipelineState):
    return "continue" if state["conviction_score"] >= 0.60 else "stop"

workflow.add_conditional_edges(
    "conviction_scorer",
    should_continue,
    {"continue": "content_generator_agent", "stop": END}
)
workflow.add_edge("content_generator_agent", END)

graph = workflow.compile()

if __name__ == "__main__":
    print("📡 Fetching real news...")
    news_list = fetch_ai_news("AI breakthroughs", max_results=2)
    
    if not news_list:
        print("❌ No news found")
    else:
        # Use the user we created in onboarding (user_id = 1)
        user_id = 1
        
        for i, news in enumerate(news_list, 1):
            print(f"\n{'='*60}")
            print(f"Processing Story {i}: {news['title'][:50]}...")
            print(f"{'='*60}")
            
            # Store news in database and get ID
            news_id = store_news(
                news["title"],
                news["content"],
                news["url"],
                news["source"],
                0.0,  # Will be filled by filter agent
                0.0   # Will be filled by novelty agent
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
            
            if result['matched_beliefs']:
                print(f"\n📝 Your beliefs matched:")
                for belief in result['matched_beliefs']:
                    print(f"   • {belief['belief']}: {belief['match_score']:.2f} match")
