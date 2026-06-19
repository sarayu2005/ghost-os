from db.database import create_persona, get_persona
from groq import Groq
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def synthesize_opinion(user_id: int, news_title: str, news_content: str,
                       matched_beliefs: list, conviction_score: float) -> str:
    """Generate a unified first-person opinion on the news story before content agents run."""
    persona = get_persona(user_id)
    if not persona:
        return ""

    beliefs_text = ""
    for b in matched_beliefs[:3]:
        line = f"- {b['belief']} (relevance: {b['match_score']:.2f})"
        if b.get('counter_argument'):
            line += f"\n  Counter: {b['counter_argument']}"
        beliefs_text += line + "\n"

    prompt = f"""You are {persona['full_name']}, a {persona['title']} with {persona['years_experience']} years experience in {persona['industry']}.
Your audience: {persona['audience']}
Your tone: {persona['tone']}

You just read this news story:
Title: {news_title}
Content: {news_content[:500]}

Your relevant beliefs on this topic:
{beliefs_text}

Write YOUR specific opinion on this story in 2-3 short paragraphs:
1. Your core reaction and take on what this means
2. Why it matters given your beliefs and expertise
3. The key insight or angle you'd lead with publicly — acknowledge complexity where counter-arguments exist, don't be one-sided

This is an internal thinking document — not a post. Be direct, opinionated, nuanced. Write in first person.
This opinion will be shared across LinkedIn, Twitter, and Substack posts so they all reflect one coherent voice.

Write the opinion directly, no headers or labels."""

    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        return message.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Opinion synthesis error: {e}")
        fallback_belief = matched_beliefs[0]['belief'] if matched_beliefs else "AI must be developed responsibly"
        return f"This news connects directly to my conviction that {fallback_belief}. As someone working in {persona.get('industry', 'technology')}, I see this as a pivotal moment worth addressing publicly."

def run_persona_interview(user_id: int) -> dict:
    """Interactive interview to build user persona"""
    print("\n" + "="*60)
    print("👤 Persona Setup - Tell us about yourself")
    print("="*60)
    
    full_name = input("\nFull name: ").strip()
    title = input("Your title/role (e.g., 'AI Safety Researcher'): ").strip()
    company = input("Company (or 'Freelance'/'Independent'): ").strip()
    industry = input("Industry (e.g., 'Technology', 'Healthcare'): ").strip()
    
    print("\n📢 Audience & Voice")
    audience = input("Who do you speak to? (e.g., 'AI professionals, policymakers'): ").strip()
    tone = input("Your writing tone (e.g., 'thoughtful', 'conversational', 'formal'): ").strip()
    
    expertise_areas = input("Your expertise areas (comma-separated): ").strip()
    
    try:
        years = int(input("Years of experience in field: ").strip())
    except:
        years = 0
    
    website = input("Website/portfolio (optional): ").strip() or None
    
    # Store in database
    create_persona(
        user_id,
        full_name,
        title,
        industry,
        audience,
        tone,
        expertise_areas,
        years,
        company,
        website
    )
    
    # Return persona dict
    persona = {
        "full_name": full_name,
        "title": title,
        "company": company,
        "industry": industry,
        "audience": audience,
        "tone": tone,
        "expertise_areas": expertise_areas,
        "years_experience": years,
        "website": website
    }
    
    print("\n" + "="*60)
    print("✅ Persona Created!")
    print("="*60)
    print(f"Name: {full_name}")
    print(f"Role: {title} @ {company}")
    print(f"Audience: {audience}")
    print(f"Tone: {tone}")
    
    return persona

def get_or_create_persona(user_id: int) -> dict:
    """Get existing persona or prompt to create"""
    persona = get_persona(user_id)
    
    if persona:
        print(f"\n✅ Found existing persona: {persona['full_name']}")
        return persona
    else:
        print("\n⚠️ No persona found. Let's create one!")
        return run_persona_interview(user_id)
