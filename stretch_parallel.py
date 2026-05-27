"""
Stretch S4: Explicit parallel fan-out.

Patches the coordinator's system prompt to require delegating to all four
specialists in a SINGLE message, with no waiting between them. When the
session events stream, all four sub-agent threads should spawn within
seconds of each other — the visible parallelism story.

Usage:
    python stretch_parallel.py
"""

from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


PARALLEL_PROMPT_ADDITION = (
    "\n\n# Parallel fan-out (mandatory)\n\n"
    "When you delegate the initial brief to the specialists, you MUST issue "
    "all four delegations in a SINGLE assistant message — one tool call per "
    "specialist, emitted together. Do NOT wait for one specialist to reply "
    "before delegating to the next.\n\n"
    "- Correct: one message containing four parallel sub-agent invocations.\n"
    "- Wrong: delegate to Pricing, wait for its reply, then delegate to Legal, etc.\n\n"
    "The only time sequential delegation is acceptable is for genuine "
    "follow-ups after all four initial briefs have returned."
)


def main() -> None:
    coordinator_id = Path(".coordinator_id").read_text().strip()

    client = Anthropic(
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    coordinator = client.beta.agents.retrieve(coordinator_id)

    if "Parallel fan-out (mandatory)" in coordinator.system:
        print("Coordinator already has the parallel fan-out instruction. Nothing to do.")
        return

    new_system = coordinator.system + PARALLEL_PROMPT_ADDITION

    client.beta.agents.update(
        coordinator_id,
        version=coordinator.version,
        system=new_system,
    )

    print("Parallel fan-out instruction added to coordinator.")
    print("Re-run run_deal_desk.py — all four specialists should spawn together.")


if __name__ == "__main__":
    main()
