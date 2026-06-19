from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.align import Align
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
import os
import json
import time

from db.database import create_user, add_belief, get_db_connection, create_persona

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

console = Console()

INTERVIEW_QUESTIONS = [
    ("AI Safety", "Do you think major AI labs are genuinely prioritizing safety, or is it just PR?"),
    ("Open Source", "Should powerful AI models be fully open source, or is keeping them closed safer?"),
    ("Future of Work", "In 10 years, how do you think AI will change knowledge work — and is that good or bad?"),
    ("Trust", "Do you trust AI-generated content right now? Where do you personally draw the line?"),
    ("Regulation", "Should governments regulate AI development now, or would that stifle innovation?"),
    ("Power Concentration", "Is it a problem that AI capability is concentrated in a few companies like OpenAI, Anthropic, and Google?"),
    ("AGI", "Do you think AGI is coming in the next decade? Does that excite you or scare you?"),
    ("Your Industry", "What's the AI opportunity in your field that nobody is talking about yet?"),
    ("Biggest Risk", "What's your single biggest personal concern about AI right now?"),
    ("Your Line", "What would have to be true for you to fully trust an AI system to make important decisions?"),
]


def extract_belief_from_answer(question: str, category: str, answer: str) -> dict:
    """Use Groq to extract a structured belief from a natural language answer."""
    prompt = f"""You are extracting a person's belief from their answer to an interview question.

Question: {question}
Category: {category}
Their answer: {answer}

Extract:
1. A clear, first-person belief statement (1 sentence, starting with "I believe..." or similar)
2. How strongly they hold this belief (0.0-1.0, based on language like "strongly", "maybe", "definitely")
3. The best counter-argument to their view (1 sentence, steelman the opposing side)

Return ONLY this JSON:
{{
  "belief": "<their core belief as a clear statement>",
  "strength": <0.0-1.0>,
  "counter_argument": "<strongest counter-argument>"
}}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception:
        return {
            "belief": answer[:200],
            "strength": 0.7,
            "counter_argument": ""
        }


def run_onboarding():
    console.clear()

    # ── Welcome screen ────────────────────────────────────────────────────────
    console.print()
    welcome = Text()
    welcome.append("  👻  GHOST OS  ", style="bold white on black")
    console.print(Align.center(welcome))
    console.print(Align.center(Text("Belief-Aware AI Content Intelligence", style="dim")))
    console.print()
    console.print(Panel(
        "[bold]Ghost OS monitors AI news, matches it against your personal beliefs,\n"
        "and generates content in your voice — ready to publish with one click.[/bold]\n\n"
        "[dim]This setup takes about 5 minutes. You only do it once.[/dim]",
        border_style="bright_black",
        padding=(1, 4)
    ))
    console.print()

    # ── Step 1: Username ──────────────────────────────────────────────────────
    console.print(Rule("[bold]Step 1 of 3 — Account[/bold]", style="bright_black"))
    console.print()
    username = Prompt.ask("  [bold cyan]Choose a username[/bold cyan]").strip()
    user_id = create_user(username)
    console.print(f"  [green]✓[/green] Account created — welcome, [bold]{username}[/bold]!\n")

    # ── Step 2: Persona ───────────────────────────────────────────────────────
    console.print(Rule("[bold]Step 2 of 3 — Your Professional Persona[/bold]", style="bright_black"))
    console.print("  [dim]This shapes how Ghost OS writes in your voice.[/dim]\n")

    full_name      = Prompt.ask("  [cyan]Full name[/cyan]").strip()
    title          = Prompt.ask("  [cyan]Your title / role[/cyan]", default="AI Researcher").strip()
    company        = Prompt.ask("  [cyan]Company or 'Independent'[/cyan]", default="Independent").strip()
    industry       = Prompt.ask("  [cyan]Industry[/cyan]", default="Technology").strip()
    audience       = Prompt.ask("  [cyan]Who do you write for?[/cyan]", default="AI professionals and founders").strip()
    tone           = Prompt.ask("  [cyan]Your writing tone[/cyan]", default="thoughtful, direct").strip()
    expertise      = Prompt.ask("  [cyan]Expertise areas (comma-separated)[/cyan]", default="AI, machine learning").strip()
    try:
        years = IntPrompt.ask("  [cyan]Years of experience[/cyan]", default=2)
    except Exception:
        years = 2
    website        = Prompt.ask("  [cyan]Website (optional)[/cyan]", default="").strip() or None

    create_persona(user_id, full_name, title, industry, audience, tone, expertise, years, company, website)
    console.print(f"\n  [green]✓[/green] Persona saved for [bold]{full_name}[/bold]\n")

    # ── Step 3: Belief interview ──────────────────────────────────────────────
    console.print(Rule("[bold]Step 3 of 3 — Your Belief Graph[/bold]", style="bright_black"))
    console.print(
        "  [dim]Answer 10 questions in your own words. Ghost OS will extract your\n"
        "  beliefs automatically and use them to score every news story.[/dim]\n"
    )
    time.sleep(1)

    beliefs_saved = []

    for i, (category, question) in enumerate(INTERVIEW_QUESTIONS, 1):
        console.print(f"  [bold bright_cyan]Q{i}/10[/bold bright_cyan]  [dim]{category}[/dim]")
        console.print(f"  [bold]{question}[/bold]")
        answer = Prompt.ask("  [dim]Your answer[/dim]").strip()

        if not answer:
            console.print("  [dim]Skipped.[/dim]\n")
            continue

        with Progress(
            SpinnerColumn(),
            TextColumn("  [dim]Extracting belief...[/dim]"),
            transient=True,
            console=console
        ) as progress:
            progress.add_task("", total=None)
            extracted = extract_belief_from_answer(question, category, answer)
            time.sleep(0.5)

        belief_text    = extracted.get("belief", answer[:200])
        strength       = float(extracted.get("strength", 0.7))
        counter        = extracted.get("counter_argument", "")

        belief_id = add_belief(user_id, belief_text, category, strength)

        if counter and belief_id:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE beliefs SET counter_argument = %s WHERE id = %s", (counter, belief_id))
            conn.commit()
            cur.close()
            conn.close()

        beliefs_saved.append({
            "category": category,
            "belief": belief_text,
            "strength": strength,
            "counter": counter
        })

        console.print(f"  [green]✓[/green] [dim]Belief captured[/dim] · strength [bold]{strength:.0%}[/bold]\n")

    # ── Summary screen ────────────────────────────────────────────────────────
    console.print()
    console.print(Rule(style="bright_black"))
    console.print()
    console.print(Align.center(Text("✅  Setup Complete", style="bold green")))
    console.print()

    # Persona summary
    persona_table = Table(show_header=False, box=None, padding=(0, 2))
    persona_table.add_column(style="dim", width=18)
    persona_table.add_column(style="bold")
    persona_table.add_row("Name", full_name)
    persona_table.add_row("Role", f"{title} @ {company}")
    persona_table.add_row("Audience", audience)
    persona_table.add_row("Tone", tone)
    console.print(Panel(persona_table, title="[bold]Your Persona[/bold]", border_style="bright_black", padding=(1, 2)))

    # Beliefs summary
    beliefs_table = Table(show_header=True, header_style="bold dim", box=None, padding=(0, 2))
    beliefs_table.add_column("Category", style="cyan", width=18)
    beliefs_table.add_column("Belief", width=50)
    beliefs_table.add_column("Strength", justify="right", style="green")

    for b in beliefs_saved:
        short = b["belief"][:60] + "…" if len(b["belief"]) > 60 else b["belief"]
        beliefs_table.add_row(b["category"], short, f"{b['strength']:.0%}")

    console.print(Panel(
        beliefs_table,
        title=f"[bold]Your Belief Graph — {len(beliefs_saved)} beliefs[/bold]",
        border_style="bright_black",
        padding=(1, 2)
    ))

    console.print()
    console.print(Panel(
        f"  Run [bold cyan]python3 run_pipeline.py[/bold cyan] to fetch today's AI news\n"
        f"  and generate your first conviction-driven posts.\n\n"
        f"  Then open [bold cyan]http://localhost:5000[/bold cyan] to review and publish.",
        title="[bold]What's Next[/bold]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print()

    return user_id, beliefs_saved


if __name__ == "__main__":
    run_onboarding()
