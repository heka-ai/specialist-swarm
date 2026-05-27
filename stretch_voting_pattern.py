"""
Stretch S9: The Voting Pattern.

For contentious legal calls (MFN, uncapped liability, IP assignment, audit
without notice, etc.), the coordinator can convene a three-person voting
panel — three parallel copies of the Legal Reviewer with different
judgement styles:

  - Legal Reviewer — Conservative  (risk-averse, "when in doubt, blocker")
  - Legal Reviewer — Balanced      (commercial-vs-legal trade-off)
  - Legal Reviewer — Aggressive    (deal-friendly, push to accept)

The coordinator then synthesises the three opinions into a single
position for the proposal's Contract Approach section.

This script:
  1. Creates the three voter agents.
  2. Adds them to the coordinator's roster.
  3. Patches the coordinator's system prompt to invoke the voting panel
     on contentious clauses.

Usage:
    python stretch_voting_pattern.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic


BASE_LEGAL_BRIEF = (
    "You are a Legal Reviewer voting member on a Deal Desk panel. You "
    "are called when there is a contentious clause in an inbound RFP "
    "where reasonable lawyers would disagree.\n\n"
    "Inputs you'll receive:\n"
    "- The RFP text\n"
    "- The specific clause(s) under debate\n"
    "- Our legal-checklist standard for context\n\n"
    "Your output format — keep it tight, you are one of three voters:\n"
    "VERDICT: ACCEPT / REJECT / COUNTER\n"
    "RATIONALE: 2–3 sentences in your voice\n"
    "COUNTER-LANGUAGE: one specific redline (only if COUNTER)\n\n"
)


VOTERS = [
    {
        "key": "legal_conservative",
        "name": "Legal Reviewer — Conservative",
        "model": "claude-sonnet-4-6",
        "system": BASE_LEGAL_BRIEF + (
            "# Your judgement style: CONSERVATIVE\n\n"
            "You are the risk-averse voice on the panel. Your default is "
            "to protect the firm. When in doubt, you vote REJECT and push "
            "the customer to take our standard position.\n\n"
            "You think about the worst case: the breach that triggers the "
            "uncapped liability, the customer that abuses the audit right, "
            "the IP assignment that hands a competitor our best work. "
            "These have happened to peers. You've seen the post-mortems.\n\n"
            "If you ever vote ACCEPT, it's because the clause is genuinely "
            "harmless. If you vote COUNTER, your redline pulls the language "
            "all the way back to our standard — not a compromise."
        ),
    },
    {
        "key": "legal_balanced",
        "name": "Legal Reviewer — Balanced",
        "model": "claude-sonnet-4-6",
        "system": BASE_LEGAL_BRIEF + (
            "# Your judgement style: BALANCED\n\n"
            "You hold the centre. You weigh the commercial value of the "
            "deal against the legal exposure of the clause. You look for "
            "the counter-position that a reasonable customer counsel will "
            "actually sign.\n\n"
            "You vote COUNTER most of the time, with redlines that meet "
            "the customer somewhere between their ask and our standard. "
            "You vote ACCEPT when the risk is small and the deal value is "
            "real. You vote REJECT only when the clause is genuinely "
            "uninsurable or strategically unacceptable.\n\n"
            "You think about precedent: what we agreed last time, what "
            "the market is doing, what our peers concede."
        ),
    },
    {
        "key": "legal_aggressive",
        "name": "Legal Reviewer — Aggressive",
        "model": "claude-sonnet-4-6",
        "system": BASE_LEGAL_BRIEF + (
            "# Your judgement style: AGGRESSIVE (deal-friendly)\n\n"
            "You are the voice that wants to win the deal. You start from "
            "the assumption that most contentious clauses are negotiating "
            "theatre, not real risk. Your default is ACCEPT or a light "
            "COUNTER.\n\n"
            "You vote REJECT only when a clause would actually bankrupt "
            "us or void our insurance. You don't fear paper risk that has "
            "never materialised in practice. You will absorb commercial "
            "concessions if it closes a strategic logo.\n\n"
            "When you vote COUNTER, your redline is the lightest-touch "
            "language the customer might accept — not our standard."
        ),
    },
]


VOTING_PROMPT_ADDITION = """

# Voting panel (contentious legal calls)

Some legal clauses don't have a single right answer — reasonable lawyers
disagree. For these, you have a three-person voting panel available:

- Legal Reviewer — Conservative  (risk-averse veto-leaner)
- Legal Reviewer — Balanced      (centre-of-the-road, commercial pragmatist)
- Legal Reviewer — Aggressive    (deal-friendly, push to accept)

# When to convene the panel

After the main Legal Reviewer returns its checklist sweep, identify the
ONE OR TWO most contentious clauses — typically the items flagged
BLOCKER or NEGOTIABLE where the call is genuinely a judgement, not a
mechanical rule. Examples from a typical RFP:
- Most Favoured Nation pricing clauses
- Uncapped liability for data breach
- IP assignment of work product
- Termination for convenience on short notice
- Audit rights without prior notice

# How to run the vote

Delegate to ALL THREE voters in a SINGLE assistant message — one tool
call per voter, emitted together. Each gets:
  - The full RFP
  - The specific clause text under debate
  - The instruction: "vote in your judgement style, ~150 words"

# How to synthesise

After all three votes return:
  1. Tally the verdicts (e.g., 2x COUNTER, 1x REJECT).
  2. If there is a clear majority, adopt that position.
  3. If the panel is split, side with the Balanced voter UNLESS the
     Conservative voter has flagged a genuinely uninsurable risk.
  4. Record the panel's vote in your Contract Approach section:
     "On clause X: panel voted [tally]. Our position: [synthesis].
     Rationale draws on [voter] who [argument]."

The panel is for judgement, not task parallelism. Use it sparingly —
two contentious clauses per deal is enough. Don't convene it for items
the checklist already resolves mechanically.
"""


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    coordinator_id = Path(".coordinator_id").read_text().strip()
    specialist_ids = json.loads(Path(".specialist_ids.json").read_text())

    # Reuse the legal-checklist skill that upload_skills.py already attached
    # to the main Legal Reviewer, so the voters reason from the same standard.
    legal_skill = None
    skill_ids_path = Path(".skill_ids.json")
    if skill_ids_path.exists():
        skill_ids = json.loads(skill_ids_path.read_text())
        if "legal-checklist" in skill_ids:
            legal_skill = {
                "type": "custom",
                "skill_id": skill_ids["legal-checklist"],
                "version": "latest",
            }

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # Create the three voters
    voter_ids = []
    for voter in VOTERS:
        if voter["key"] in specialist_ids:
            print(f"  {voter['name']:36s} already exists -> {specialist_ids[voter['key']]}")
            voter_ids.append(specialist_ids[voter["key"]])
            continue

        create_kwargs = dict(
            name=voter["name"],
            model=voter["model"],
            system=voter["system"],
            tools=[{"type": "agent_toolset_20260401"}],
            metadata={
                "hackathon": "partner-basecamp-2026",
                "track": "specialist-swarm",
                "role": "legal-voter",
                "judgement_style": voter["key"].replace("legal_", ""),
            },
        )
        if legal_skill:
            create_kwargs["skills"] = [legal_skill]

        agent = client.beta.agents.create(**create_kwargs)
        specialist_ids[voter["key"]] = agent.id
        voter_ids.append(agent.id)
        print(f"  Created {voter['name']:36s} -> {agent.id}")

    if legal_skill is None:
        print("\n  NOTE: .skill_ids.json missing or no legal-checklist entry — voters")
        print("        created without the checklist skill. Run upload_skills.py and")
        print("        re-run if you want them grounded in the same position library.")

    Path(".specialist_ids.json").write_text(json.dumps(specialist_ids, indent=2))

    # Update the coordinator's roster + system prompt
    coordinator = client.beta.agents.retrieve(coordinator_id)
    existing_ids = {a.id for a in coordinator.multiagent.agents}
    new_roster = list(coordinator.multiagent.agents) + [
        {"type": "agent", "id": vid}
        for vid in voter_ids
        if vid not in existing_ids
    ]

    if "Voting panel (contentious legal calls)" in coordinator.system:
        new_system = coordinator.system
        print("\nCoordinator already has the voting-panel instruction — refreshing roster only.")
    else:
        new_system = coordinator.system + VOTING_PROMPT_ADDITION

    client.beta.agents.update(
        coordinator_id,
        version=coordinator.version,
        system=new_system,
        multiagent={"type": "coordinator", "agents": new_roster},
    )

    print("\nCoordinator updated.")
    print(f"  Roster size: {len(new_roster)}")
    print(f"  Voting panel: {[v['name'] for v in VOTERS]}")
    print("\nRe-run dashboard_server.py (or run_deal_desk.py) and watch the")
    print("voting panel light up when the coordinator hits a contentious clause.")


if __name__ == "__main__":
    main()
