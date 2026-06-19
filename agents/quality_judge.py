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

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found")

groq_client = Groq(api_key=groq_api_key)

def judge_content_quality(news_title: str, news_content: str, 
                         generated_content: str, content_type: str,
                         matched_beliefs: list) -> dict:
    """
    Judge quality of generated content
    Returns: {
        "quality_score": 0.0-1.0,
        "approved": True/False,
        "issues": [list of problems],
        "strengths": [what's good],
        "suggestions": [how to improve]
    }
    """
    beliefs_summary = ", ".join([b['belief'] for b in matched_beliefs[:2]])
    
    prompt = f"""Evaluate the quality of this {content_type} post.

Original News:
{news_title}
{news_content[:300]}

User Beliefs: {beliefs_summary}

Generated {content_type.upper()} Post:
{generated_content}

Evaluate on these criteria (0-1.0 for each):
1. Coherence: Does it make sense and flow well?
2. Relevance: Does it relate to the original news?
3. Belief alignment: Does it reflect the user's values?
4. Engagement: Would people want to interact with this?
5. Grammar: Is it well-written?
6. Authenticity: Does it sound like a real person?

Return ONLY this JSON (no other text):
{{
  "coherence_score": <0.0-1.0>,
  "relevance_score": <0.0-1.0>,
  "belief_alignment_score": <0.0-1.0>,
  "engagement_score": <0.0-1.0>,
  "grammar_score": <0.0-1.0>,
  "authenticity_score": <0.0-1.0>,
  "overall_quality": <0.0-1.0>,
  "approved": <true/false - true if >= 0.65>,
  "issues": [<list of specific problems>],
  "strengths": [<what works well>],
  "suggestions": [<how to improve>]
}}"""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        response_text = message.choices[0].message.content.strip()
        result = _parse_llm_json(response_text)
        return result
    except Exception as e:
        print(f"❌ Quality judgment error: {e}")
        return {
            "overall_quality": 0.5,
            "approved": False,
            "issues": ["Quality check failed"],
            "strengths": [],
            "suggestions": []
        }

def display_quality_report(quality: dict, content_type: str):
    """Display quality judgment to user"""
    print(f"\n📊 Quality Report: {content_type}")
    print(f"   Overall Score: {quality['overall_quality']:.2f}/1.0")
    print(f"   Status: {'✅ APPROVED' if quality['approved'] else '❌ REJECTED'}")
    
    if quality.get('issues'):
        print(f"\n   Issues:")
        for issue in quality['issues'][:3]:
            print(f"      • {issue}")
    
    if quality.get('strengths'):
        print(f"\n   Strengths:")
        for strength in quality['strengths'][:2]:
            print(f"      • {strength}")
    
    if quality.get('suggestions') and not quality['approved']:
        print(f"\n   Suggestions:")
        for suggestion in quality['suggestions'][:2]:
            print(f"      • {suggestion}")
