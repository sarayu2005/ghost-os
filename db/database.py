import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Database connection
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url)
    return psycopg2.connect(dbname="ghost_os", user="sarayu", host="localhost")

# USER OPERATIONS
def create_user(username: str) -> int:
    """Create a new user, return user_id"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO users (username) VALUES (%s) RETURNING id",
            (username,)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Created user: {username} (ID: {user_id})")
        return user_id
    except psycopg2.IntegrityError:
        conn.rollback()
        print(f"⚠️ User {username} already exists")
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()

def get_user(username: str) -> int:
    """Get user_id by username"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return result[0] if result else None

# BELIEF OPERATIONS
def add_belief(user_id: int, belief_text: str, category: str = "general", strength: float = 0.7) -> int:
    """Add a belief for a user, return belief_id"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO beliefs (user_id, belief_text, category, strength) VALUES (%s, %s, %s, %s) RETURNING id",
        (user_id, belief_text, category, strength)
    )
    belief_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Added belief: {belief_text} (ID: {belief_id})")
    return belief_id

def get_user_beliefs(user_id: int) -> list:
    """Get all beliefs for a user"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute(
        "SELECT id, belief_text, category, strength, counter_argument FROM beliefs WHERE user_id = %s",
        (user_id,)
    )
    beliefs = cur.fetchall()
    cur.close()
    conn.close()
    
    return beliefs

# NEWS OPERATIONS
def store_news(title: str, content: str, url: str, source: str, relevance_score: float, novelty_score: float) -> int:
    """Store a news story in the database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """INSERT INTO news_stories (title, content, url, source, relevance_score, novelty_score) 
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (title, content, url, source, relevance_score, novelty_score)
        )
        news_id = cur.fetchone()[0]
        conn.commit()
        return news_id
    except psycopg2.IntegrityError:
        conn.rollback()
        # News already exists, get its ID
        cur.execute("SELECT id FROM news_stories WHERE url = %s", (url,))
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()

# BELIEF MATCHING
def add_belief_match(news_id: int, belief_id: int, match_score: float):
    """Record that a news story matches a belief"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO belief_matches (news_id, belief_id, match_score) VALUES (%s, %s, %s)",
        (news_id, belief_id, match_score)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_belief_matches(news_id: int, user_id: int) -> list:
    """Get all matched beliefs for a news story"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute(
        """SELECT b.belief_text, bm.match_score, b.strength 
           FROM belief_matches bm
           JOIN beliefs b ON bm.belief_id = b.id
           WHERE bm.news_id = %s AND b.user_id = %s
           ORDER BY bm.match_score DESC""",
        (news_id, user_id)
    )
    matches = cur.fetchall()
    cur.close()
    conn.close()
    
    return matches

if __name__ == "__main__":
    # Test the database connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    print(f"✅ Database connected! Users in DB: {count}")

def delete_belief(belief_id: int) -> bool:
    """Delete a belief by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM belief_matches WHERE belief_id = %s", (belief_id,))
        cur.execute("DELETE FROM beliefs WHERE id = %s", (belief_id,))
        conn.commit()
        print(f"✅ Belief deleted!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# PERSONA OPERATIONS
def create_persona(user_id: int, full_name: str, title: str, industry: str, 
                  audience: str, tone: str, expertise_areas: str, 
                  years_experience: int, company: str, website: str = None) -> int:
    """Create or update user persona"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO user_personas 
            (user_id, full_name, title, industry, audience, tone, expertise_areas, years_experience, company, website)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                title = EXCLUDED.title,
                industry = EXCLUDED.industry,
                audience = EXCLUDED.audience,
                tone = EXCLUDED.tone,
                expertise_areas = EXCLUDED.expertise_areas,
                years_experience = EXCLUDED.years_experience,
                company = EXCLUDED.company,
                website = EXCLUDED.website
            RETURNING id
        """, (user_id, full_name, title, industry, audience, tone, expertise_areas, years_experience, company, website))
        
        persona_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Persona created/updated for user {user_id}")
        return persona_id
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

def get_persona(user_id: int) -> dict:
    """Get user persona"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT full_name, title, industry, audience, tone, expertise_areas, 
               years_experience, company, website
        FROM user_personas WHERE user_id = %s
    """, (user_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return dict(result) if result else None



def save_linkedin_token(user_id: int, access_token: str, person_urn: str, expiry):
    """Store LinkedIn OAuth token for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET linkedin_access_token = %s, linkedin_person_urn = %s, linkedin_token_expiry = %s
        WHERE id = %s
    """, (access_token, person_urn, expiry, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_linkedin_token(user_id: int) -> dict:
    """Get LinkedIn token for a user"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT linkedin_access_token, linkedin_person_urn, linkedin_token_expiry
        FROM users WHERE id = %s
    """, (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return dict(result) if result else None

def store_pending_content(user_id, news_title, news_content, content_type, generated_text, quality_score, conviction_score=None, matched_beliefs=None):
    """Store generated content for HITL review"""
    import json
    conn = get_db_connection()
    cur = conn.cursor()

    beliefs_json = json.dumps(matched_beliefs) if matched_beliefs else None

    try:
        cur.execute("""
            INSERT INTO pending_content
            (user_id, news_title, news_content, content_type, generated_text, quality_score, conviction_score, matched_beliefs_json, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """, (user_id, news_title, news_content, content_type, generated_text, quality_score, conviction_score, beliefs_json))
        
        conn.commit()
        print(f"✅ Saved {content_type} to dashboard for review")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error saving content: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False
