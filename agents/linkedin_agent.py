from groq import Groq
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from db.database import get_persona
from services.style_memory import get_style_examples

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found")

groq_client = Groq(api_key=groq_api_key)

def generate_linkedin_post(user_id: int, news_title: str, news_content: str,
                          matched_beliefs: list, conviction_score: float, opinion: str = "") -> str:
    """Generate LinkedIn post using user persona and synthesized opinion"""
    persona = get_persona(user_id)

    if not persona:
        return None

    expertise_text = persona.get('expertise_areas', 'technology')
    opinion_section = f"\nYour synthesized opinion on this story:\n{opinion}\n" if opinion else ""

    # Pull style examples from ChromaDB
    style_examples = get_style_examples(user_id, 'linkedin', news_title, n=2)
    style_section = ""
    if style_examples:
        style_section = "\nHere are examples of your past approved LinkedIn posts — match this writing style exactly (rhythm, tone, structure), not the topic:\n"
        for i, ex in enumerate(style_examples, 1):
            style_section += f"\n--- Example {i} ---\n{ex[:500]}\n"
        style_section += "\n---\n"

    prompt = f"""You are {persona['full_name']}, a {persona['title']} with {persona['years_experience']} years experience.
Your audience: {persona['audience']}
Your tone: {persona['tone']}
Your expertise: {expertise_text}
{opinion_section}{style_section}
News: {news_title}
Content: {news_content[:300]}

Write a LinkedIn post that expresses the opinion above in your professional voice.

Requirements:
- 250-350 words
- Start with a strong hook that reflects your opinion
- Include 2-3 specific insights from your expertise
- End with 1-2 engagement questions
- Professional tone (no emojis, minimal hashtags)
- Call-to-action: invite discussion

Write the post directly, nothing else."""
    
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        return message.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ LinkedIn generation error: {e}")
        return None
