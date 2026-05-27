"""
Run the Deal Desk swarm against the synthetic RFP.

Inlines the RFP + past-wins + product-overview into the user message (simpler
than Files API for hackathon-scale content). Streams events as they come in so
you can watch the parallel thread fan-out — this is the demo, narrate it live.

Saves the final transcript to outputs/.

Usage:
    python run_deal_desk.py
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

# ── ANSI colours ────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
MAGENTA= "\033[35m"
RED    = "\033[31m"
BLUE   = "\033[34m"
WHITE  = "\033[37m"

# Agent name → colour so threads are visually distinct
_AGENT_COLOURS = [CYAN, GREEN, YELLOW, MAGENTA, BLUE]
_agent_colour_map: dict[str, str] = {}

def _agent_colour(name: str | None) -> str:
    if not name:
        return WHITE
    if name not in _agent_colour_map:
        idx = len(_agent_colour_map) % len(_AGENT_COLOURS)
        _agent_colour_map[name] = _AGENT_COLOURS[idx]
    return _agent_colour_map[name]

_start_time: float = 0.0

def _ts() -> str:
    """Elapsed seconds since session start, e.g. '+12.3s'."""
    elapsed = time.time() - _start_time
    return f"{DIM}+{elapsed:5.1f}s{RESET}"

def _preview(content: list, max_chars: int = 120) -> str:
    """Extract a short text preview from a content block list."""
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    combined = " ".join(parts).replace("\n", " ")
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "…"
    return combined

def _tool_summary(name: str, inp: dict) -> str:
    """Return the most readable snippet from a tool's input dict."""
    keys_of_interest = ["command", "query", "url", "path", "filename", "content", "prompt", "text", "code"]
    for key in keys_of_interest:
        val = inp.get(key)
        if val and isinstance(val, str):
            snippet = val.replace("\n", " ")[:100]
            if len(val) > 100:
                snippet += "…"
            return f"{DIM}{key}={snippet}{RESET}"
    # Fall back to first key
    if inp:
        k, v = next(iter(inp.items()))
        snippet = str(v).replace("\n", " ")[:100]
        return f"{DIM}{k}={snippet}{RESET}"
    return ""


RFP_PATH = Path("synthetic-data/rfp-acme-corp.md")
SUPPORTING_FILES = [
    Path("synthetic-data/past-wins.json"),
    Path("synthetic-data/product-overview.md"),
]
OUTPUT_DIR = Path("outputs")


def load_inputs_as_context() -> str:
    blocks = []
    for path in [RFP_PATH, *SUPPORTING_FILES]:
        if not path.exists():
            print(f"  WARNING: {path} missing — skipping")
            continue
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    if not Path(".coordinator_id").exists() or not Path(".environment_id").exists():
        raise SystemExit(
            "Missing .coordinator_id or .environment_id. Run "
            "create_specialists.py, upload_skills.py, then create_coordinator.py first."
        )

    coordinator_id = Path(".coordinator_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()

    client = Anthropic()

    print("Loading RFP + supporting docs...")
    context = load_inputs_as_context()

    print(f"\nStarting session against coordinator {coordinator_id}...")
    session = client.beta.sessions.create(
        agent=coordinator_id,
        environment_id=environment_id,
        title="Deal Desk — Acme Corp RFP",
    )
    Path(".last_session_id").write_text(session.id)

    user_message = (
        "An RFP has just landed. Please run the standard Deal Desk process:\n"
        "1. Read the RFP yourself.\n"
        "2. Delegate to all four specialists in parallel.\n"
        "3. Synthesise their replies.\n"
        "4. Produce BOTH deliverables — the full written proposal as a "
        "branded .docx AND a 5-slide executive pitch deck as a .pptx. "
        "Both files must be saved to the session container.\n\n"
        "Specialists have their own skills attached for their respective "
        "domains. Move fast — the RFP deadline is real.\n\n"
        f"{context}"
    )

    # Stream the events — this is the demo. Watch for parallel thread spawns.
    global _start_time
    _start_time = time.time()
    print(f"\n{BOLD}{'─'*60}{RESET}")
    print(f"{BOLD}  DEAL DESK SWARM — LIVE EVENT STREAM{RESET}")
    print(f"{BOLD}{'─'*60}{RESET}\n")
    final_text_parts: list[str] = []
    thinking_count: dict[str, int] = {}

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": user_message}],
                }
            ],
        )
        for event in stream:
            t = event.type

            # ── Thread lifecycle ─────────────────────────────────────────
            if t == "session.thread_created":
                c = _agent_colour(event.agent_name)
                print(f"{_ts()}  {c}{BOLD}SPAWN{RESET}   {c}{event.agent_name}{RESET}  {DIM}(thread {event.session_thread_id}){RESET}", flush=True)

            elif t == "session.thread_status_running":
                name = getattr(event, "agent_name", "?")
                c = _agent_colour(name)
                print(f"{_ts()}  {c}▶ RUNNING{RESET}  {c}{name}{RESET}", flush=True)

            elif t == "session.thread_status_idle":
                name = getattr(event, "agent_name", "?")
                c = _agent_colour(name)
                print(f"{_ts()}  {c}■ IDLE{RESET}     {c}{name}{RESET}", flush=True)

            # ── Agent-to-agent messages ──────────────────────────────────
            elif t == "agent.thread_message_sent":
                to = event.to_agent_name or "primary"
                c  = _agent_colour(to)
                preview = _preview(event.content)
                print(f"{_ts()}  {YELLOW}→ DELEGATE{RESET}  to {c}{to}{RESET}  {DIM}{preview}{RESET}", flush=True)

            elif t == "agent.thread_message_received":
                frm = event.from_agent_name or "primary"
                c   = _agent_colour(frm)
                preview = _preview(event.content)
                print(f"{_ts()}  {GREEN}← REPLY{RESET}     from {c}{frm}{RESET}  {DIM}{preview}{RESET}", flush=True)

            # ── Thinking ────────────────────────────────────────────────
            elif t == "agent.thinking":
                # Don't flood — just tick a dot per burst
                key = "thinking"
                thinking_count[key] = thinking_count.get(key, 0) + 1
                if thinking_count[key] == 1:
                    print(f"{_ts()}  {MAGENTA}💭 THINKING{RESET} ", end="", flush=True)
                else:
                    print(".", end="", flush=True)

            # ── Tool use ────────────────────────────────────────────────
            elif t == "agent.tool_use":
                if thinking_count.pop("thinking", 0):
                    print()  # close the thinking dots line
                name_str = event.name
                summary  = _tool_summary(name_str, event.input)
                print(f"\n{_ts()}  {CYAN}⚙  TOOL{RESET}    {BOLD}{name_str}{RESET}  {summary}", flush=True)

            elif t == "agent.mcp_tool_use":
                if thinking_count.pop("thinking", 0):
                    print()
                name_str = f"{event.mcp_server_name}.{event.name}"
                summary  = _tool_summary(event.name, event.input)
                print(f"\n{_ts()}  {CYAN}⚙  MCP{RESET}     {BOLD}{name_str}{RESET}  {summary}", flush=True)

            elif t == "agent.tool_result":
                is_err = getattr(event, "is_error", False)
                marker = f"{RED}✗ ERROR{RESET}" if is_err else f"{GREEN}✓ done{RESET}"
                preview = _preview(event.content or [])
                print(f"{_ts()}       {marker}  {DIM}{preview}{RESET}", flush=True)

            elif t == "agent.mcp_tool_result":
                is_err = getattr(event, "is_error", False)
                marker = f"{RED}✗ ERROR{RESET}" if is_err else f"{GREEN}✓ done{RESET}"
                preview = _preview(getattr(event, "content", []) or [])
                print(f"{_ts()}       {marker}  {DIM}{preview}{RESET}", flush=True)

            # ── Final coordinator message ────────────────────────────────
            elif t == "agent.message":
                if thinking_count.pop("thinking", 0):
                    print()
                print(f"\n{BOLD}{'─'*60}{RESET}")
                print(f"{BOLD}  COORDINATOR RESPONSE{RESET}")
                print(f"{BOLD}{'─'*60}{RESET}\n")
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        final_text_parts.append(block.text)
                        print(block.text, end="", flush=True)

            # ── Session done ─────────────────────────────────────────────
            elif t == "session.status_idle":
                print(f"\n\n{BOLD}{GREEN}✔  SWARM COMPLETE{RESET}", flush=True)
                break

            elif t == "session.error":
                print(f"\n{RED}{BOLD}✗  ERROR: {getattr(event, 'message', event)}{RESET}", flush=True)

    OUTPUT_DIR.mkdir(exist_ok=True)
    transcript_path = OUTPUT_DIR / "coordinator-transcript.txt"
    transcript_path.write_text("".join(final_text_parts))
    print(f"\nCoordinator transcript saved to {transcript_path}")

    # Pull every file the agents produced in the container
    print("\nDownloading deliverables from the session container...")
    files = client.beta.files.list(
        scope_id=session.id,
        betas=["managed-agents-2026-04-01"],
    )
    file_count = 0
    for f in files.data:
        out_path = OUTPUT_DIR / f.filename
        print(f"  {f.filename}  ->  {out_path}")
        content = client.beta.files.download(f.id)
        content.write_to_file(str(out_path))
        file_count += 1

    if file_count == 0:
        print("  (no files found — agents may have produced text-only output)")
    else:
        print(f"\nDownloaded {file_count} file(s) to {OUTPUT_DIR}/")

    print(f"\nView the full session (including all sub-agent threads) at:")
    print(f"  https://platform.claude.com/sessions/{session.id}")


if __name__ == "__main__":
    main()
