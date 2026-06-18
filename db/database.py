import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Database connection
def get_db_connection():
    """Get connection to ghost_os database"""
    conn = psycopg2.connect(
        dbname="ghost_os",
        user="sarayu",
        host="localhost"
    )
    return conn

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
        "SELECT id, belief_text, category, strength FROM beliefs WHERE user_id = %s",
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
