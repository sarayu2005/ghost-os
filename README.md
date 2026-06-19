# 👻 Ghost OS

An agentic AI system that reads today's AI news, runs it through a multi-step reasoning pipeline, and writes LinkedIn posts, Twitter threads, and Substack articles in your voice — which you approve before anything goes live.

The twist: it only writes when the news actually connects to something you believe. No match, no content.

built around one question: can a system understand what you actually think, not just how you write?

---

## The core idea

Most AI writing tools summarize news. Ghost OS starts from what you think.

You answer 10 questions when you sign up — your real opinions on AI safety, open source models, regulation, the future of work. Ghost OS stores those as your **Belief Graph**: structured convictions with strength scores and counter-arguments.

Every story that comes in gets scored against your beliefs. A piece about open source LLMs scores high if you care about AI democratization. A generic "AI is changing everything" listicle gets dropped. Only stories that genuinely connect to your worldview make it through the pipeline — and when they do, the system writes from your perspective, not a neutral summary.

---

## The agentic pipeline

Six AI agents run in sequence, each feeding into the next:

```
News fetch (Tavily)
      ↓
Filter Agent       →  is this relevant to AI/tech?
      ↓
Novelty Agent      →  is this actually new or just recycled?
      ↓
Belief Matcher     →  does this connect to YOUR beliefs?
      ↓
Conviction Scorer  →  0.35 × relevance + 0.30 × novelty + 0.35 × belief match
      ↓
   < 0.30 → dropped. nothing generated.
      ↓
Persona Agent      →  synthesizes YOUR take on this story
      ↓
Content Generator  →  LinkedIn post + Twitter thread + Substack article
      ↓
Quality Judge      →  scores each piece before it hits your dashboard
      ↓
Dashboard          →  you approve, edit, or reject
      ↓
LinkedIn API       →  auto-publishes on approval
```

LangGraph orchestrates the whole thing as a state machine — every agent reads from and writes to a shared state object. Stories that fail the conviction gate never reach content generation.

---

## Features

- **Belief Graph** — built from a 10-question interview. An LLM extracts your belief, how strongly you hold it, and the strongest counter-argument to your view.
- **Conviction scoring** — weighted formula across relevance, novelty, and belief alignment. Anything below 0.30 gets dropped automatically.
- **Persona Agent** — forms your unified opinion on the story before writing starts. LinkedIn, Twitter, and Substack all express the same take, not three incoherent ones.
- **Style memory (ChromaDB)** — every post you approve gets stored as an embedding. Future content pulls semantically similar past posts to match your writing voice over time.
- **HITL dashboard** — each card shows which beliefs triggered it, conviction score, and quality score. Edit inline before approving.
- **LinkedIn auto-publish** — OAuth 2.0 integration. Approve → posted. No copy-paste.

---

## Tech Stack

| | |
|--|--|
| LLM inference | Groq — llama-3.1-8b-instant |
| News fetching | Tavily API |
| Agent orchestration | LangGraph (StateGraph) |
| Database | PostgreSQL |
| Vector / style memory | ChromaDB |
| Dashboard | Flask + vanilla JS |
| Publishing | LinkedIn API v2 (ugcPosts) |
| CLI onboarding | Rich |
| Deployment | Railway |

---

## Setup

**Requirements**: Python 3.11+, PostgreSQL, Groq API key, Tavily API key, LinkedIn Developer app

```bash
git clone https://github.com/sarayu2005/ghost-os
cd ghost-os
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
GROQ_API_KEY=
TAVILY_API_KEY=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_REDIRECT_URI=http://localhost:5000/auth/callback
FLASK_SECRET_KEY=
```

Set up the database:
```bash
psql -U postgres -c "CREATE DATABASE ghost_os;"
psql -U postgres -d ghost_os < db/schema.sql
```

Run onboarding once:
```bash
python3 onboarding.py
```

Start the dashboard:
```bash
python3 app.py
# → http://localhost:5000
```

Run the pipeline:
```bash
python3 run_pipeline.py
```

Takes ~3 minutes. Refresh the dashboard when done.

---

## Project Structure

```
ghost-os/
├── agents/
│   ├── graph.py              # LangGraph pipeline — all 6 agents wired here
│   ├── scorers.py            # relevance + novelty scoring
│   ├── belief_matcher.py     # matches news against your beliefs
│   ├── persona_agent.py      # synthesizes your opinion before writing
│   ├── linkedin_agent.py     # LinkedIn post generation
│   ├── content_generator.py  # Twitter + Substack generation
│   └── quality_judge.py      # scores generated content
├── db/
│   ├── database.py           # all DB operations
│   └── schema.sql            # PostgreSQL schema
├── services/
│   ├── news.py               # Tavily news fetching
│   └── style_memory.py       # ChromaDB embeddings interface
├── templates/
│   └── dashboard.html        # HITL review dashboard
├── app.py                    # Flask server + LinkedIn OAuth
├── onboarding.py             # belief graph interview
├── run_pipeline.py           # pipeline entry point
└── manage_beliefs.py         # add / edit / delete beliefs
```

---


