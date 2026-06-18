from groq import Groq
import os
import json
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file")

groq_client = Groq(api_key=groq_api_key)

def generate_linkedin_post(news_title: str, news_content: str, matched_beliefs: list, conviction_score: float) -> str:
    """Generate a LinkedIn post (200-300 words, professional tone)"""
    beliefs_text = "\n".join([f"- {b['belief']}" for b in matched_beliefs[:3]])
    
    prompt = f"""Write a LinkedIn post about this news story. Make it professional, thought-provoking, and tie it to these user values:

News: {news_title}
Content: {news_content[:400]}

User Values:
{beliefs_text}

Requirements:
- 200-300 words
- Professional but conversational tone
- Include 1-2 questions to engage
- NO hashtags
- NO emojis
- Start with a hook/observation

Write the post directly, nothing else."""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        return message.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ LinkedIn generation error: {e}")
        return None

def generate_twitter_thread(news_title: str, news_content: str, matched_beliefs: list) -> list:
    """Generate a Twitter thread (3-5 tweets, viral tone)"""
    beliefs_text = ", ".join([b['belief'] for b in matched_beliefs[:2]])
    
    prompt = f"""Write a Twitter thread (3-5 tweets) about this news that's viral and punchy.

News: {news_title}
Content: {news_content[:400]}

User perspective: {beliefs_text}

Requirements:
- Each tweet under 280 characters
- Conversational, punchy tone
- Use line breaks between tweets (TWEET SEPARATOR)
- NO hashtags
- NO emojis
- Start with a hook tweet
- Include 1 question or call-to-action in final tweet

Format:
Tweet 1...
TWEET SEPARATOR
Tweet 2...
etc."""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500
        )
        
        text = message.choices[0].message.content.strip()
        tweets = [t.strip() for t in text.split("TWEET SEPARATOR") if t.strip()]
        return tweets
    except Exception as e:
        print(f"❌ Twitter generation error: {e}")
        return []

def generate_substack_article(news_title: str, news_content: str, matched_beliefs: list, conviction_score: float) -> str:
    """Generate a Substack article (800-1000 words, educational tone)"""
    beliefs_text = ", ".join([b['belief'] for b in matched_beliefs[:3]])
    
    prompt = f"""Write a Substack article about this news story. Make it educational and tie to reader values.

News: {news_title}
Content: {news_content[:600]}

Author perspective: {beliefs_text}

Requirements:
- 800-1000 words
- Educational, accessible tone
- Include 2-3 key takeaways
- Structure: Hook → Context → Implications → Conclusion
- Include 1-2 thought-provoking questions
- Conversational but substantive
- NO hashtags

Write the article directly."""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        return message.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Substack generation error: {e}")
        return None
