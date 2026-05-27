"""
Test mode for the dashboard - simulates swarm events without calling the API.
Useful for testing the visualization and animations quickly.

Usage:
    python dashboard_test.py

Then open http://localhost:5051/test.html
"""

import json
import time
import threading
from pathlib import Path

from flask import Flask, Response, send_from_directory

OUTPUT_DIR = Path("outputs")

SAMPLE_PROPOSAL = """# Proposal Response — Acme Corp RFP

## Executive Summary

- **Full technical fit** across all 12 stated requirements
- **$594K Year-1 ACV** at 17.5% discount (5-yr TCV ~$3.15M)
- **24-week implementation** with phased rollout across 3 regions

## Our Understanding

Acme Corp is a $1.4B industrial IoT manufacturer seeking to consolidate \
280TB of operational data across Azure and on-prem sources. The current \
Teradata + Informatica stack cannot scale to 80K events/sec or support \
the real-time ML pipeline your R&D team needs.

## Why Sia Partners + BTS-Synthetic

We bring transformation consulting + a proven data platform. Our Initech \
win (same industry, same scale) delivered 40% cost reduction in 6 months. \
Fabric can't match our streaming throughput; Databricks can't match our TCO.

## Commercial Proposal

| Item | Value |
|------|-------|
| Year 1 ACV | $594,000 |
| Discount | 17.5% from list |
| Term | 5 years |
| Payment | Net 45 |

## Next Steps

1. Technical deep-dive (Week of June 2)
2. Commercial negotiation (June 9)
3. Contract execution (June 20)
"""

app = Flask(__name__)


def generate_test_events():
    """Generate a realistic sequence of test events."""
    # Simulate the event sequence
    events = [
        # User message and coordinator start
        {"type": "session.thread_created", "agent_name": "Coordinator"},
        {"type": "session.thread_status_running", "agent_name": "Coordinator"},

        # Coordinator delegates to all specialists (parallel)
        {"type": "agent.thread_message_sent", "to_agent_name": "Pricing Specialist"},
        {"type": "agent.thread_message_sent", "to_agent_name": "Legal Reviewer"},
        {"type": "agent.thread_message_sent", "to_agent_name": "Technical Fit Specialist"},
        {"type": "agent.thread_message_sent", "to_agent_name": "Competitive Intel Analyst"},

        # All specialists spawn
        {"type": "session.thread_created", "agent_name": "Pricing Specialist"},
        {"type": "session.thread_created", "agent_name": "Legal Reviewer"},
        {"type": "session.thread_created", "agent_name": "Technical Fit Specialist"},
        {"type": "session.thread_created", "agent_name": "Competitive Intel Analyst"},

        # All specialists start running (THE DEMO MOMENT)
        {"type": "session.thread_status_running", "agent_name": "Pricing Specialist"},
        {"type": "session.thread_status_running", "agent_name": "Legal Reviewer"},
        {"type": "session.thread_status_running", "agent_name": "Technical Fit Specialist"},
        {"type": "session.thread_status_running", "agent_name": "Competitive Intel Analyst"},

        # Some tool uses
        {"type": "agent.tool_use", "name": "pricing-playbook"},
        {"type": "agent.tool_use", "name": "legal-checklist"},
        {"type": "agent.tool_use", "name": "web-search"},

        # Specialists reply back (staggered)
        {"type": "agent.thread_message_received", "from_agent_name": "Technical Fit Specialist"},
        {"type": "agent.thread_message_received", "from_agent_name": "Pricing Specialist"},
        {"type": "agent.thread_message_received", "from_agent_name": "Competitive Intel Analyst"},
        {"type": "agent.thread_message_received", "from_agent_name": "Legal Reviewer"},

        # Coordinator synthesizes
        {"type": "session.thread_status_running", "agent_name": "Coordinator"},
        {"type": "agent.tool_use", "name": "file-write"},

        # Finished
        {"type": "session.status_idle"},
    ]

    return events


@app.route('/')
def index():
    """Serve the dashboard HTML."""
    return send_from_directory('dashboard', 'index.html')


@app.route('/stream')
def stream():
    """Server-Sent Events endpoint with simulated events."""
    def generate():
        print("\n" + "=" * 60)
        print("TEST MODE - Simulating swarm events")
        print("=" * 60 + "\n")

        events = generate_test_events()

        for i, event in enumerate(events):
            # Simulate realistic timing
            if event["type"] == "session.thread_status_running":
                time.sleep(1.5)  # Agents take time to start
            elif event["type"] == "agent.thread_message_sent":
                time.sleep(0.3)  # Quick delegation
            elif event["type"] == "session.thread_created":
                time.sleep(0.2)  # Threads spawn quickly
            elif event["type"] == "agent.thread_message_received":
                time.sleep(2.0)  # Specialists take time to reply
            else:
                time.sleep(0.5)

            print(f"  [{i+1}/{len(events)}] Sending: {event['type']}")
            yield f"data: {json.dumps(event)}\n\n"

        print("\n" + "=" * 60)
        print("Test sequence complete!")
        print("=" * 60 + "\n")

        # Save simulated output to disk
        OUTPUT_DIR.mkdir(exist_ok=True)
        transcript_path = OUTPUT_DIR / "coordinator-transcript.txt"
        transcript_path.write_text(SAMPLE_PROPOSAL)
        print(f"Simulated transcript saved to {transcript_path}")

        # Send a done event so the frontend closes the EventSource
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/output')
def output():
    """Return the proposal output — from disk if saved, otherwise the sample."""
    transcript_path = OUTPUT_DIR / "coordinator-transcript.txt"
    if transcript_path.exists():
        return {"status": "ready", "content": transcript_path.read_text()}
    return {"status": "pending", "content": None}


@app.route('/status')
def status():
    """Health check endpoint."""
    return {
        "status": "test_mode",
        "mode": "simulation",
        "api_required": False
    }


def main():
    print("=" * 60)
    print("Deal Desk Swarm Dashboard - TEST MODE")
    print("=" * 60)
    print("\nThis is a test mode that simulates swarm events without")
    print("calling the Anthropic API. Use this to test the dashboard")
    print("visualization and animations quickly.\n")
    print("Starting server on http://localhost:5051")
    print("Open your browser and navigate to: http://localhost:5051\n")
    print("The simulated swarm will run automatically.")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=5051, debug=False, threaded=True)


if __name__ == "__main__":
    main()
