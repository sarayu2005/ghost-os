from groq import Groq
import os
import json
import re
from dotenv import load_dotenv
from pathlib import Path
from db.database import get_user_beliefs, add_belief_match

def _parse_llm_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file")

groq_client = Groq(api_key=groq_api_key)

def match_beliefs_to_news(user_id: int, news_title: str, news_content: str, news_id: int = None) -> dict:
    """Match a news story against all of user's beliefs."""
    beliefs = get_user_beliefs(user_id)
    
    if not beliefs:
        return {
            "user_id": user_id,
            "news_id": news_id,
            "matched_beliefs": [],
            "overall_belief_score": 0.5
        }
    
    matched = []
    
    for belief in beliefs:
        match_score = score_single_belief(news_title, news_content, belief['belief_text'])
        
        if match_score > 0.3:
            matched.append({
                "belief": belief['belief_text'],
                "belief_id": belief['id'],
                "match_score": match_score,
                "strength": belief['strength'],
                "counter_argument": belief.get('counter_argument')
            })
            
            if news_id:
                add_belief_match(news_id, belief['id'], match_score)
    
    # Calculate weighted overall score - cap all values at 1.0
    if matched:
        scores = []
        for m in matched:
            strength = min(m['strength'], 1.0)  # Cap strength at 1.0
            scores.append(m['match_score'] * strength)
        overall_score = min(sum(scores) / len(matched), 1.0)  # Cap final score at 1.0
    else:
        overall_score = 0.3
    
    return {
        "user_id": user_id,
        "news_id": news_id,
        "matched_beliefs": matched,
        "overall_belief_score": overall_score
    }

def score_single_belief(news_title: str, news_content: str, belief: str) -> float:
    """Use Groq to evaluate if news matches a specific belief."""
    prompt = f"""Evaluate how relevant this news is to the following belief/value.

Belief: {belief}

News Title: {news_title}
News Content: {news_content[:300]}

Return ONLY a JSON object with:
{{"match_score": <0.0 to 1.0>, "reason": "<brief explanation>"}}

Score guidelines:
- 0.9-1.0: Directly aligns with or strongly supports this belief
- 0.7-0.9: Aligns well, relevant to the belief
- 0.5-0.7: Somewhat related to the belief
- 0.3-0.5: Tangentially related, minimal connection
- 0.0-0.3: Not related to this belief at all

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
        return float(result.get("match_score", 0.3))
    except Exception as e:
        print(f"❌ Belief matching error: {e}")
        return 0.3
