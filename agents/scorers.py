from groq import Groq
import os
import json
import re
from dotenv import load_dotenv
from pathlib import Path

def _parse_llm_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file")

groq_client = Groq(api_key=groq_api_key)

def score_relevance(news_title: str, news_content: str) -> float:
    """
    Use Groq to evaluate how relevant the news is to AI/tech interests.
    Returns score 0.0-1.0
    """
    prompt = f"""Evaluate how relevant this news is to someone interested in AI, LLMs, and technology.

News Title: {news_title}
News Content: {news_content[:300]}

Return ONLY a JSON object with:
{{"relevance_score": <0.0 to 1.0>, "reason": "<brief explanation>"}}

Score guidelines:
- 0.9-1.0: Directly about AI breakthroughs, LLM releases, or major tech advances
- 0.7-0.9: Related to AI but not directly
- 0.5-0.7: Tangentially related
- 0.2-0.5: Barely related
- 0.0-0.2: Not relevant at all

Only return the JSON, nothing else."""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        response_text = message.choices[0].message.content.strip()
        result = _parse_llm_json(response_text)
        return float(result.get("relevance_score", 0.5))
    except Exception as e:
        print(f"❌ Relevance scoring error: {e}")
        return 0.5

def score_novelty(news_title: str, news_content: str) -> float:
    """
    Use Groq to evaluate how novel/fresh this topic is.
    Returns score 0.0-1.0
    """
    prompt = f"""Evaluate how novel and fresh this news is. Is it a rehash of old topics or genuinely new?

News Title: {news_title}
News Content: {news_content[:300]}

Return ONLY a JSON object with:
{{"novelty_score": <0.0 to 1.0>, "reason": "<brief explanation>"}}

Score guidelines:
- 0.9-1.0: Completely new, never seen before angle or breakthrough
- 0.7-0.9: Fresh take on established topic
- 0.5-0.7: Somewhat rehashed but with new details
- 0.2-0.5: Very familiar topic, minimal new info
- 0.0-0.2: Pure rehash of old news

Only return the JSON, nothing else."""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        response_text = message.choices[0].message.content.strip()
        result = _parse_llm_json(response_text)
        return float(result.get("novelty_score", 0.5))
    except Exception as e:
        print(f"❌ Novelty scoring error: {e}")
        return 0.5
