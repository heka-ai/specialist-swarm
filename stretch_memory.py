"""
Stretch S3: Memory across deals.

Wire up the Memory tool to the coordinator so it remembers insights from
past deals — what positioning worked, pricing anchors, competitive dynamics.

Usage:
    python stretch_memory.py
"""

from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


MEMORY_PROMPT_ADDITION = (
    "\n\n# Memory\n\n"
    "You have access to memory across deals. After completing each deal:\n"
    "- Store key insights (what positioning worked, pricing anchors, competitive dynamics)\n"
    "- On future deals, recall relevant past insights and reference them explicitly\n"
    "- Example: 'In our Acme deal last month, we won on TCO positioning — same play applies here.'\n"
    "\nAlways check memory at the start of a new deal for relevant precedents."
)


def main() -> None:
    coordinator_id = Path(".coordinator_id").read_text().strip()

    client = Anthropic(
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # Retrieve the current coordinator agent
    coordinator = client.beta.agents.retrieve(coordinator_id)

    # Append memory instructions to the coordinator's system prompt.
    # The agent_toolset already includes file ops — the coordinator can
    # persist deal insights to files in the session container and read
    # them back in future sessions.
    new_system = coordinator.system + MEMORY_PROMPT_ADDITION

    # Update the coordinator
    client.beta.agents.update(
        coordinator_id,
        version=coordinator.version,
        system=new_system,
    )

    print("Memory tool added to coordinator.")
    print("The coordinator will now remember insights across deals.")


if __name__ == "__main__":
    main()
