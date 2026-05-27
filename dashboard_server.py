"""
Dashboard server for the Deal Desk swarm visualization.

Serves the HTML dashboard and streams events from the swarm via Server-Sent Events (SSE).
Reuses the logic from run_deal_desk.py to execute the swarm.

Usage:
    python dashboard_server.py

Then open http://localhost:5050 in your browser.
"""

import os
import json
import queue
import threading
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, Response, send_from_directory
from anthropic import Anthropic


app = Flask(__name__)

# Global event queue for SSE
event_queue = queue.Queue()

# Configuration
RFP_PATH = Path("synthetic-data/rfp-acme-corp.md")
SUPPORTING_FILES = [
    Path("synthetic-data/past-wins.json"),
    Path("synthetic-data/product-overview.md"),
]
OUTPUT_DIR = Path("outputs")


def _extract_text_snippet(event, max_chars: int = 280) -> str | None:
    """Pull the first text block out of a message event, if present.

    The event shape varies across SDK versions; be defensive.
    """
    content = getattr(event, "content", None)
    if not content:
        message = getattr(event, "message", None)
        content = getattr(message, "content", None) if message else None
    if not content:
        return None
    for block in content:
        text = getattr(block, "text", None)
        if text:
            text = text.strip()
            return text[:max_chars] + ("…" if len(text) > max_chars else "")
    return None


def _extract_verdict(snippet: str) -> str | None:
    """Find a 'VERDICT: ACCEPT/REJECT/COUNTER' line in a voter's reply."""
    for line in snippet.splitlines():
        line = line.strip().upper()
        if line.startswith("VERDICT:"):
            tail = line.split(":", 1)[1].strip()
            for word in ("ACCEPT", "REJECT", "COUNTER"):
                if word in tail:
                    return word
    return None


def load_inputs_as_context() -> str:
    """Load RFP and supporting documents as context."""
    blocks = []
    for path in [RFP_PATH, *SUPPORTING_FILES]:
        if not path.exists():
            print(f"  WARNING: {path} missing — skipping")
            continue
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def run_swarm():
    """Execute the Deal Desk swarm and emit events to the queue."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        event_queue.put({
            "type": "error",
            "message": "ANTHROPIC_API_KEY not set"
        })
        return

    if not Path(".coordinator_id").exists() or not Path(".environment_id").exists():
        event_queue.put({
            "type": "error",
            "message": "Missing .coordinator_id or .environment_id. Run setup scripts first."
        })
        return

    coordinator_id = Path(".coordinator_id").read_text().strip()
    environment_id = Path(".environment_id").read_text().strip()

    client = Anthropic()

    print("Loading RFP + supporting docs...")
    context = load_inputs_as_context()

    print(f"\nStarting session against coordinator {coordinator_id}...")
    session = client.beta.sessions.create(
        agent=coordinator_id,
        environment_id=environment_id,
        title="Deal Desk — Acme Corp RFP (Dashboard)",
    )
    Path(".last_session_id").write_text(session.id)

    user_message = (
        "An RFP has just landed. Please run the standard Deal Desk process:\n"
        "1. Read the RFP yourself.\n"
        "2. Delegate to all four specialists in parallel.\n"
        "3. Synthesise their replies.\n"
        "4. Produce the final proposal response as a branded Word document "
        "if you have access to a docx skill; otherwise output the response "
        "as a structured markdown document.\n\n"
        "Specialists have their own skills attached for their respective "
        "domains. Move fast — the RFP deadline is real.\n\n"
        f"{context}"
    )

    # Stream the events
    print("\n=== Streaming events to dashboard ===\n")
    final_text_parts = []

    try:
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

                # Build event data for frontend
                event_data = {"type": t}

                if t == "session.thread_created":
                    event_data["agent_name"] = event.agent_name
                    print(f"  [thread spawned]   {event.agent_name}", flush=True)

                elif t == "session.thread_status_running":
                    event_data["agent_name"] = getattr(event, "agent_name", "?")
                    print(f"  [thread running]   {event_data['agent_name']}", flush=True)

                elif t == "agent.thread_message_received":
                    event_data["from_agent_name"] = event.from_agent_name
                    # Capture a short verdict snippet from voting panel replies
                    # so the dashboard can show each voter's call inline.
                    snippet = _extract_text_snippet(event)
                    if snippet:
                        event_data["snippet"] = snippet
                        verdict = _extract_verdict(snippet)
                        if verdict:
                            event_data["verdict"] = verdict
                    print(f"  [reply ←]          {event.from_agent_name}", flush=True)

                elif t == "agent.thread_message_sent":
                    event_data["to_agent_name"] = event.to_agent_name
                    print(f"  [delegate →]       {event.to_agent_name}", flush=True)

                elif t == "agent.message":
                    for block in event.content:
                        if getattr(block, "type", None) == "text":
                            final_text_parts.append(block.text)
                            print(block.text, end="", flush=True)
                    # Don't send agent.message events to frontend (too verbose)
                    continue

                elif t == "agent.tool_use":
                    event_data["name"] = getattr(event, "name", "?")
                    print(f"\n  [tool: {event_data['name']}]", flush=True)

                elif t == "session.status_idle":
                    print("\n\n[swarm finished]")
                    event_queue.put(event_data)
                    break

                # Push event to queue for SSE
                event_queue.put(event_data)

        # Save outputs
        OUTPUT_DIR.mkdir(exist_ok=True)
        transcript_path = OUTPUT_DIR / "coordinator-transcript.txt"
        transcript_path.write_text("".join(final_text_parts))
        print(f"\nCoordinator transcript saved to {transcript_path}")

        # Download deliverables
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

    except Exception as e:
        print(f"Error in swarm execution: {e}")
        event_queue.put({
            "type": "error",
            "message": str(e)
        })


@app.route('/')
def index():
    """Serve the dashboard HTML."""
    return send_from_directory('dashboard', 'index.html')


@app.route('/stream')
def stream():
    """Server-Sent Events endpoint for streaming swarm events."""
    def generate():
        # Start the swarm in a background thread
        swarm_thread = threading.Thread(target=run_swarm, daemon=True)
        swarm_thread.start()

        # Stream events from the queue
        while True:
            try:
                event = event_queue.get(timeout=1)
                yield f"data: {json.dumps(event)}\n\n"

                # Stop streaming after swarm finishes
                if event.get("type") == "session.status_idle" or event.get("type") == "error":
                    break
            except queue.Empty:
                # Send keepalive
                yield ": keepalive\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/output')
def output():
    """Return the final proposal transcript if available."""
    transcript_path = OUTPUT_DIR / "coordinator-transcript.txt"
    if transcript_path.exists():
        return {"status": "ready", "content": transcript_path.read_text()}
    return {"status": "pending", "content": None}


@app.route('/status')
def status():
    """Health check endpoint."""
    return {
        "status": "ok",
        "coordinator_id": Path(".coordinator_id").read_text().strip() if Path(".coordinator_id").exists() else None,
        "environment_id": Path(".environment_id").read_text().strip() if Path(".environment_id").exists() else None,
    }


def main():
    print("=" * 60)
    print("Deal Desk Swarm Dashboard Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5050")
    print("Open your browser and navigate to: http://localhost:5050\n")
    print("The swarm will start automatically when you open the dashboard.")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)


if __name__ == "__main__":
    main()
