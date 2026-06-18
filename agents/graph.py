from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Any
from pydantic import BaseModel

# Define your shared state object
class PipelineState(TypedDict):
    news_story: str
    relevance_score: float
    novelty_score: float
    conviction_score: float
    matched_beliefs: list
    opinion: str
    content_outputs: dict
    user_approved: bool

# Create the graph
workflow = StateGraph(PipelineState)

# Add nodes (just stubs for now)
def filter_agent(state: PipelineState) -> PipelineState:
    """Filter news by relevance to user interests"""
    print("🔍 Filter Agent: Checking relevance...")
    state["relevance_score"] = 0.8  # Placeholder
    return state

def novelty_agent(state: PipelineState) -> PipelineState:
    """Check if topic is already saturated"""
    print("✨ Novelty Agent: Checking novelty...")
    state["novelty_score"] = 0.7  # Placeholder
    return state

def conviction_scorer(state: PipelineState) -> PipelineState:
    """Gate: Should we continue?"""
    score = (state["relevance_score"] * 0.35) + (state["novelty_score"] * 0.30) + 0.35
    state["conviction_score"] = score
    print(f"🎯 Conviction Score: {score}")
    return state

# Add nodes to graph
workflow.add_node("filter_agent", filter_agent)
workflow.add_node("novelty_agent", novelty_agent)
workflow.add_node("conviction_scorer", conviction_scorer)

# Define edges (the routing logic)
workflow.add_edge(START, "filter_agent")
workflow.add_edge("filter_agent", "novelty_agent")
workflow.add_edge("novelty_agent", "conviction_scorer")

# Conditional routing: if conviction score is high, continue; else stop
# Conditional routing: if conviction score is high, continue; else stop
def should_continue(state: PipelineState):
    return "continue" if state["conviction_score"] >= 0.65 else "stop"

workflow.add_conditional_edges(
    "conviction_scorer",
    should_continue,
    {"continue": END, "stop": END}
)



# Compile the graph
graph = workflow.compile()

if __name__ == "__main__":
    # Test run
    initial_state = {
        "news_story": "OpenAI releases GPT-5 with multimodal reasoning",
        "relevance_score": 0.0,
        "novelty_score": 0.0,
        "conviction_score": 0.0,
        "matched_beliefs": [],
        "opinion": "",
        "content_outputs": {},
        "user_approved": False
    }
    
    result = graph.invoke(initial_state)
    print("\n✅ Pipeline completed!")
    print(f"Final conviction score: {result['conviction_score']}")