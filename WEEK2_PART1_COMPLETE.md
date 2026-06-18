# Ghost OS - Week 2 Part 1: Belief Graph + Personalization (Complete)

## 🎯 Week 2 Part 1 Mission
Build a **personalized belief system** that:
- Stores user beliefs in PostgreSQL
- Captures beliefs through onboarding interview
- Matches news to user beliefs using Groq LLM
- Calculates personalized conviction scores
- Supports multiple users with different beliefs

**Status:** ✅ **COMPLETE & WORKING**

---

## 📁 Final Project Structure (After Week 2 Part 1)

```
ghost-os/
├── .env                          # API keys (Tavily, Groq)
├── venv/                         # Python virtual environment
├── agents/
│   ├── graph.py                  # LangGraph pipeline (now with beliefs)
│   ├── scorers.py                # Groq-powered scoring
│   └── belief_matcher.py          # Belief matching engine (NEW)
├── services/
│   └── news.py                   # Tavily news fetching
├── db/
│   ├── schema.sql                # Database structure (NEW)
│   └── database.py               # Database operations (NEW)
├── onboarding.py                 # Belief interview flow (NEW)
├── manage_beliefs.py             # Edit beliefs anytime (NEW)
├── run_pipeline.py               # Multi-user launcher (NEW)
├── WEEK1_COMPLETE.md             # Week 1 recap
└── WEEK2_PART1_COMPLETE.md       # This file
```

---

## 🚀 Step-by-Step Week 2 Part 1 Journey

### **Step 1: PostgreSQL Setup**

**Check if PostgreSQL exists:**
```bash
postgres --version
# Output: postgres (PostgreSQL) 15.18 (Homebrew)
```

**Start PostgreSQL:**
```bash
brew services start postgresql@15
```

**Create database:**
```bash
createdb ghost_os
```

**Verify:**
```bash
psql -l | grep ghost_os
# Output: ghost_os  | sarayu | UTF8 | en_US.UTF-8 | en_US.UTF-8 |
```

**Status:** ✅ Database ready

---

### **Step 2: Design Database Schema**

**File: `db/schema.sql`**

Created 4 tables:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Beliefs table (user's values/beliefs)
CREATE TABLE beliefs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    belief_text TEXT NOT NULL,
    category VARCHAR(100),
    strength FLOAT DEFAULT 0.7,  -- How strongly user believes (0.0-1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- News stories cache
CREATE TABLE news_stories (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    source VARCHAR(255),
    relevance_score FLOAT,
    novelty_score FLOAT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Belief-to-news matches
CREATE TABLE belief_matches (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL REFERENCES news_stories(id),
    belief_id INTEGER NOT NULL REFERENCES beliefs(id),
    match_score FLOAT,  -- How well does this news match this belief
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_beliefs_user ON beliefs(user_id);
CREATE INDEX idx_belief_matches_news ON belief_matches(news_id);
CREATE INDEX idx_belief_matches_belief ON belief_matches(belief_id);
```

**Applied to database:**
```bash
psql ghost_os -f db/schema.sql
```

**Verified:**
```bash
psql ghost_os -c "\dt"
# Output: 4 tables (users, beliefs, news_stories, belief_matches)
```

**Status:** ✅ Schema deployed

---

### **Step 3: Create Database Operations Module**

**File: `db/database.py`**

Functions created:

1. **User Operations:**
   - `create_user(username)` — Create new user, return user_id
   - `get_user(username)` — Get user_id by username

2. **Belief Operations:**
   - `add_belief(user_id, belief_text, category, strength)` — Store belief
   - `get_user_beliefs(user_id)` — Retrieve all user's beliefs
   - `delete_belief(belief_id)` — Delete a belief

3. **News Operations:**
   - `store_news(title, content, url, source, relevance_score, novelty_score)` — Cache news
   - `get_belief_matches(news_id, user_id)` — Get matching beliefs for news

4. **Belief Matching:**
   - `add_belief_match(news_id, belief_id, match_score)` — Record a match

**Connection:**
```python
def get_db_connection():
    conn = psycopg2.connect(
        dbname="ghost_os",
        user="sarayu",
        host="localhost"
    )
    return conn
```

**Tested:**
```bash
python3 db/database.py
# Output: ✅ Database connected! Users in DB: 0
```

**Status:** ✅ Database module ready

---

### **Step 4: Create Onboarding Interview**

**File: `onboarding.py`**

Interactive flow:

```
🎯 Welcome to Ghost OS - Onboarding Interview
👤 Enter your username: sarayu
✅ Created user: sarayu (ID: 1)

📚 Let's capture your beliefs about tech & society...

🎯 Which topics matter to you?
  1. AI Safety
  2. Open Source
  3. Decentralization
  4. Privacy
  5. Education
  6. Climate
  7. Accessibility

Enter numbers: 1,2,4
```

**For each selected category:**
```
💭 AI Safety:
   What's your belief? → "AI safety is critical"
   How strongly (0.0-1.0)? → 0.9

✅ Added belief: AI safety is critical (ID: 2)
```

**Output:**
```
✅ Onboarding Complete!
   User: sarayu (ID: 1)
   Beliefs captured: 3
   1. AI safety is critical (0.9)
   2. Open source matters (0.8)
   3. Privacy is essential (0.85)
```

**Tested:**
```bash
python3 onboarding.py
# Successfully created user with 3 beliefs
```

**Status:** ✅ Onboarding working

---

### **Step 5: Create Belief Matching Engine**

**File: `agents/belief_matcher.py` (NEW)**

Core function: `match_beliefs_to_news(user_id, news_title, news_content, news_id)`

```python
def match_beliefs_to_news(user_id, news_title, news_content, news_id):
    # 1. Get user's beliefs from database
    beliefs = get_user_beliefs(user_id)
    
    # 2. For each belief, use Groq to evaluate match
    matched = []
    for belief in beliefs:
        match_score = score_single_belief(news_title, news_content, belief['belief_text'])
        
        if match_score > 0.3:  # Only meaningful matches
            matched.append({
                "belief": belief['belief_text'],
                "match_score": match_score,
                "strength": belief['strength']
            })
    
    # 3. Calculate weighted overall score
    if matched:
        overall_score = sum(m['match_score'] * min(m['strength'], 1.0) for m in matched) / len(matched)
        overall_score = min(overall_score, 1.0)  # Cap at 1.0
    else:
        overall_score = 0.3
    
    return {
        "matched_beliefs": matched,
        "overall_belief_score": overall_score
    }
```

**Groq LLM Prompt:**
```
Belief: "AI safety is critical"
News: "OpenAI releases GPT-5 with safety guardrails"

Return JSON: {"match_score": 0.85, "reason": "..."}
```

**Problem encountered:**
```
Belief Match Score: 18.29  # Way too high!
```

**Root cause:** User entered `107` as a strength value during onboarding

**Solution:** Cap all scores at 1.0
```python
strength = min(m['strength'], 1.0)  # Cap strength
overall_score = min(overall_score, 1.0)  # Cap final
```

**Status:** ✅ Belief matcher working

---

### **Step 6: Integrate Beliefs into Pipeline**

**Updated: `agents/graph.py`**

**Added to PipelineState:**
```python
class PipelineState(TypedDict):
    user_id: int
    # ... existing fields ...
    belief_score: float  # NEW
    matched_beliefs: List[dict]  # NEW
```

**New agent: `belief_matcher_agent`**
```python
def belief_matcher_agent(state: PipelineState) -> PipelineState:
    """Match news against user's personal beliefs"""
    result = match_beliefs_to_news(
        state['user_id'],
        state['news_story'],
        state['news_content'],
        state['news_id']
    )
    
    state["matched_beliefs"] = result['matched_beliefs']
    state["belief_score"] = result['overall_belief_score']
    return state
```

**New conviction formula (3-factor):**
```python
# Relevance 35% + Novelty 30% + Beliefs 35%
conviction_score = (
    relevance_score * 0.35 + 
    novelty_score * 0.30 + 
    belief_score * 0.35
)
```

**Pipeline flow:**
```
News → Filter Agent → Novelty Agent → Belief Matcher → Conviction Score → Gate
```

**Status:** ✅ Pipeline fully integrated

---

### **Step 7: Create Belief Management Tool**

**File: `manage_beliefs.py` (NEW)**

Interactive menu to edit beliefs anytime:

```
🎯 Belief Manager
Enter username: sarayu

💭 Options:
  1. View all beliefs
  2. Add new belief
  3. Delete belief
  4. Exit
```

**View beliefs:**
```
📝 Beliefs for sarayu:
   ID 1: AI safety is critical
      Category: AI Safety, Strength: 0.9
   ID 2: Open source matters
      Category: Open Source, Strength: 0.8
```

**Add belief:**
```
➕ Adding new belief...
   Belief: Privacy is fundamental
   Category: Privacy
   Strength: 0.85
✅ Belief added!
```

**Delete belief:**
```
Enter belief ID to delete: 1
✅ Belief deleted!
```

**Status:** ✅ Management tool ready

---

### **Step 8: Create Multi-User Launcher**

**File: `run_pipeline.py` (NEW)**

Allows any user to run the pipeline with their beliefs:

```bash
python3 run_pipeline.py
👤 Enter your username: sarayu
✅ Welcome sarayu!
📡 Fetching real news...
```

**Automatically:**
1. Finds user in database
2. Loads their beliefs
3. Fetches latest news
4. Runs pipeline with personalized beliefs
5. Shows conviction scores

**Status:** ✅ Multi-user launcher ready

---

## ✅ All Problems & Solutions

| # | Problem | Error | Solution |
|----|---------|-------|----------|
| 1 | PostgreSQL not started | `psycopg2.OperationalError: could not connect` | Run `brew services start postgresql@15` |
| 2 | Wrong PostgreSQL version | `brew services start postgresql` failed | Use `brew services start postgresql@15` |
| 3 | Database not created | `FATAL: database "ghost_os" does not exist` | Run `createdb ghost_os` |
| 4 | Belief scores too high | `Belief Match Score: 18.29` | User entered 107 as strength; capped at 1.0 |
| 5 | User already exists | `UNIQUE violation on username` | Handled gracefully, returns existing user_id |
| 6 | Duplicate news entries | `UNIQUE violation on url` | Handled gracefully, returns existing news_id |

---

## 🎯 Final Working Output

```
📡 Fetching real news...
============================================================
Processing Story 1: Latest AI News and Breakthroughs...
============================================================
🔍 Filter Agent: Scoring 'Latest AI News...'
   Relevance Score: 0.70

✨ Novelty Agent: Evaluating novelty...
   Novelty Score: 0.50

💭 Belief Matcher: Checking alignment with your values...
   Belief Match Score: 0.59
   Matched 3 of your beliefs:
      • privacy (0.50)
      • AI safety is critical (0.80)
      • AI safety is critical (0.70)

🎯 Final Conviction Score: 0.60
✅ FINAL CONVICTION SCORE: 0.60 ❌ (below 0.65 gate)

============================================================
Processing Story 2: 6 AI breakthroughs that will define 2026
============================================================
🔍 Filter Agent: Scoring '6 AI breakthroughs...'
   Relevance Score: 0.90

✨ Novelty Agent: Evaluating novelty...
   Novelty Score: 0.50

💭 Belief Matcher: Checking alignment with your values...
   Belief Match Score: 0.56
   Matched 3 of your beliefs:
      • privacy (0.50)
      • AI safety is critical (0.70)
      • AI safety is critical (0.70)

🎯 Final Conviction Score: 0.66
✅ FINAL CONVICTION SCORE: 0.66 ✅ (PASSES! Ready for content gen)

📝 Your beliefs matched:
   • privacy: 0.50 match
   • AI safety is critical: 0.70 match
   • AI safety is critical: 0.70 match
```

---

## 📊 Week 2 Part 1 Statistics

| Metric | Result |
|--------|--------|
| Files Created | 6 (schema.sql, database.py, belief_matcher.py, onboarding.py, manage_beliefs.py, run_pipeline.py) |
| Database Tables | 4 (users, beliefs, news_stories, belief_matches) |
| Lines of Code | ~800 |
| API Integrations | 2 (Tavily, Groq - now with belief matching) |
| Multi-User Support | ✅ Yes |
| Problems Solved | 6 |
| Time to Complete | ~3-4 hours |
| Status | ✅ COMPLETE & WORKING |

---

## 🎓 Key Learnings

### Architecture
- **Belief Graph:** Store user values in database with strength weights
- **Normalized Schema:** Separate tables for users, beliefs, news, matches
- **Foreign Keys:** Maintain data integrity across relationships

### Database Operations
- Connection pooling with psycopg2
- Transaction handling (commit/rollback)
- Graceful duplicate handling (UNIQUE constraints)
- RealDictCursor for readable results

### LLM Integration
- Groq evaluates individual beliefs against news
- Weighted scoring: match_score × belief_strength
- Cap all scores at 0.0-1.0 range
- Fallback to 0.3 on LLM errors

### User Experience
- Interactive onboarding (pick categories, rate beliefs)
- Anytime belief management (add/delete/view)
- Multi-user support (different beliefs per user)
- Clear conviction scoring feedback

---

## 🔄 The Pipeline Now Works Like This

```
User 1 (sarayu):
  Beliefs: [AI Safety 0.9, Privacy 0.85, Open Source 0.8]
  Story arrives → Matched beliefs → Conviction 0.66 ✅
  → Ready for content generation

User 2 (alice - if created):
  Beliefs: [Climate 0.9, Education 0.8]
  Story arrives → Different belief matches → Different conviction
  → Their own personalized results
```

---

## 📁 How to Use Week 2 Part 1

**First time setup:**
```bash
python3 onboarding.py        # Create profile + beliefs
```

**Manage beliefs anytime:**
```bash
python3 manage_beliefs.py    # View/add/delete beliefs
```

**Run personalized pipeline:**
```bash
python3 run_pipeline.py      # Process news with YOUR beliefs
```

---

## 🚀 What Week 2 Part 1 Enables

✅ **Personalized news filtering** (beyond generic AI relevance)  
✅ **User profiles** (multiple people can use Ghost OS)  
✅ **Belief-based conviction scores** (35% of final score)  
✅ **Persistent storage** (beliefs saved in PostgreSQL)  
✅ **Dynamic belief management** (update anytime)  
✅ **Foundation for content generation** (next: Week 2 Part 2)

---

## 📝 Files Summary

| File | Purpose | Status |
|------|---------|--------|
| `db/schema.sql` | Database structure definition | ✅ Deployed |
| `db/database.py` | All database operations | ✅ Working |
| `agents/belief_matcher.py` | Groq-powered belief matching | ✅ Working |
| `onboarding.py` | Interactive belief interview | ✅ Working |
| `manage_beliefs.py` | Belief management tool | ✅ Working |
| `run_pipeline.py` | Multi-user pipeline launcher | ✅ Working |
| `agents/graph.py` | Updated with belief matching | ✅ Working |

---

## 🎯 Next: Week 2 Part 2

Stories that pass the conviction gate (> 0.65) are ready for **content generation**:

- 📱 **LinkedIn Posts** (professional, 200-300 words)
- 🐦 **Twitter Threads** (viral, multi-tweet)
- 📰 **Substack Articles** (deep dives, 1000+ words)

Story 2 has conviction 0.66 → Ready to generate content!

---

**Status: Week 2 Part 1 ✅ COMPLETE**

**Date Completed:** June 19, 2026

**Next: Week 2 Part 2 — Content Generation**
