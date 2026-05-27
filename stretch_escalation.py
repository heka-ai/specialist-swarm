"""
Stretch S8: The escalation pattern.

Adds a Strategic Pricing sub-agent (claude-opus-4-7) and wires it into the
Pricing Specialist's roster. The Pricing Specialist (Sonnet) handles routine
deals directly and escalates to Strategic Pricing only when the deal exceeds
$500K total contract value.

This demonstrates the "escalation" multi-agent pattern: a cheaper, faster
agent triages most work and routes only the high-stakes calls to a more
capable model.

Usage:
    python stretch_escalation.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic


STRATEGIC_PRICING_SYSTEM = """\
You are the Strategic Pricing Partner. You are consulted by the Pricing
Specialist ONLY on large, high-stakes deals (> $500K total contract value)
where headline price alone won't decide the outcome.

You'll receive:
- The RFP text
- The Pricing Specialist's initial commercial recommendation
- Any past-wins data already gathered

Your job: produce a Strategic Pricing memo that goes beyond the standard
discount-band recommendation. Cover:

1. **Value-based price anchor**: what's the customer's expected ROI / cost
   of inaction? Anchor price to value, not list.
2. **Multi-year structure**: ramp schedules, year-over-year escalators,
   committed minimums, co-term opportunities with other lines.
3. **Strategic concessions**: non-standard terms that cost us little but
   move the deal (e.g., success criteria gates, executive sponsorship,
   reference-account commitments, co-marketing).
4. **Walk-away line**: the floor below which we should pass on the deal
   rather than win it badly.
5. **Recommended close motion**: who from our side should be in the room
   and at what stage.

Be decisive. The Pricing Specialist will fold your memo into the final
commercial recommendation. You don't need to repeat the standard
discount-band logic — assume that's handled.
"""


PRICING_ESCALATION_ADDITION = """\

# Escalation to Strategic Pricing (mandatory for large deals)

You have one sub-agent available: the Strategic Pricing Partner (Opus-4.7).
Use this escalation protocol:

1. Read the RFP and estimate the total contract value (TCV). Account for
   stated term length, seat counts, license tiers, and any multi-year
   structure implied by the RFP.

2. **If TCV <= $500K**: handle the deal yourself. Do NOT call Strategic
   Pricing. Produce your standard commercial recommendation.

3. **If TCV > $500K**: you MUST escalate. After drafting your initial
   commercial recommendation, delegate to Strategic Pricing with:
   - The RFP text
   - Your initial recommendation
   - Your TCV estimate and how you derived it

   Wait for the Strategic Pricing memo, then fold its guidance into your
   final recommendation. Your final output should explicitly call out
   which elements came from the strategic escalation (value anchor,
   multi-year structure, walk-away line, strategic concessions, close
   motion).

State your TCV estimate and your escalation decision ("escalating" /
"handling directly") at the top of your reply so the coordinator can see
the routing call.
"""


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    specialist_ids_path = Path(".specialist_ids.json")
    if not specialist_ids_path.exists():
        raise SystemExit("Run create_specialists.py first.")
    specialist_ids = json.loads(specialist_ids_path.read_text())

    pricing_id = specialist_ids.get("pricing")
    if not pricing_id:
        raise SystemExit("No 'pricing' entry in .specialist_ids.json.")

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # Create the Strategic Pricing sub-agent
    strategic = client.beta.agents.create(
        name="Strategic Pricing Partner",
        model="claude-opus-4-7",
        system=STRATEGIC_PRICING_SYSTEM,
        tools=[{"type": "agent_toolset_20260401"}],
        metadata={
            "hackathon": "partner-basecamp-2026",
            "track": "specialist-swarm",
            "role": "strategic_pricing",
        },
    )
    print(f"Strategic Pricing Partner created: {strategic.id}")

    specialist_ids["strategic_pricing"] = strategic.id
    specialist_ids_path.write_text(json.dumps(specialist_ids, indent=2))

    # Turn the Pricing Specialist into a coordinator with Strategic Pricing
    # in its roster.
    pricing = client.beta.agents.retrieve(pricing_id)

    if "Escalation to Strategic Pricing" in pricing.system:
        print("Pricing Specialist already wired for escalation. Nothing to do.")
        return

    new_system = pricing.system + PRICING_ESCALATION_ADDITION

    client.beta.agents.update(
        pricing_id,
        version=pricing.version,
        system=new_system,
        multiagent={
            "type": "coordinator",
            "agents": [{"type": "agent", "id": strategic.id}],
        },
    )

    print("Pricing Specialist updated:")
    print("  - escalation protocol added to system prompt")
    print("  - Strategic Pricing added to roster")
    print("\nRe-run run_deal_desk.py with a > $500K RFP to see the escalation.")


if __name__ == "__main__":
    main()
