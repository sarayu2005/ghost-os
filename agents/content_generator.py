from groq import Groq
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from services.style_memory import get_style_examples

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found")

groq_client = Groq(api_key=groq_api_key)

def generate_twitter_thread(news_title: str, news_content: str, matched_beliefs: list, opinion: str = "", user_id: int = None) -> list:
    """Generate a Twitter thread (3-5 tweets, viral tone)"""
    opinion_section = f"\nYour opinion on this story:\n{opinion}\n" if opinion else \
                      f"\nUser perspective: {', '.join([b['belief'] for b in matched_beliefs[:2]])}\n"

    style_section = ""
    if user_id:
        examples = get_style_examples(user_id, 'twitter', news_title, n=2)
        if examples:
            style_section = "\nYour past approved Twitter threads (match this style):\n"
            for i, ex in enumerate(examples, 1):
                style_section += f"\n--- Example {i} ---\n{ex[:300]}\n"
            style_section += "\n---\n"

    prompt = f"""Write a Twitter thread (3-5 tweets) about this news that's viral and punchy.

News: {news_title}
Content: {news_content[:400]}
{opinion_section}{style_section}

Requirements:
- Each tweet under 280 characters
- Conversational, punchy tone
- Use line breaks between tweets (TWEET SEPARATOR)
- NO hashtags
- NO emojis
- Start with a hook tweet
- Include 1 question or call-to-action in final tweet

Format (write ONLY the tweet text, no labels like "Tweet 1:"):
<tweet text>
TWEET SEPARATOR
<tweet text>
TWEET SEPARATOR
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
        print(f"Twitter generation error: {e}")
        return []

def generate_substack_article(news_title: str, news_content: str, matched_beliefs: list, conviction_score: float, opinion: str = "", user_id: int = None) -> str:
    """Generate a Substack article (800-1000 words, educational tone)"""
    opinion_section = f"\nAuthor's opinion on this story:\n{opinion}\n" if opinion else \
                      f"\nAuthor perspective: {', '.join([b['belief'] for b in matched_beliefs[:3]])}\n"

    style_section = ""
    if user_id:
        examples = get_style_examples(user_id, 'substack', news_title, n=2)
        if examples:
            style_section = "\nYour past approved Substack articles (match this writing style):\n"
            for i, ex in enumerate(examples, 1):
                style_section += f"\n--- Example {i} ---\n{ex[:500]}\n"
            style_section += "\n---\n"

    prompt = f"""Write a Substack article about this news story.

News: {news_title}
Content: {news_content[:600]}
{opinion_section}{style_section}

Requirements:
- 800-1000 words
- Educational, accessible tone
- Include 2-3 key takeaways
- Structure: Hook -> Context -> Implications -> Conclusion
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
        print(f"Substack generation error: {e}")
        return None
