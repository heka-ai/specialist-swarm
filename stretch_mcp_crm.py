"""
Stretch Goal S5: Attach the synthetic CRM MCP server to the pricing specialist.

Since the Managed Agents API doesn't support MCP as a direct tool type,
we configure the MCP server at the environment level so it's available
to agents running in that environment.

Usage:
    python stretch_mcp_crm.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    env_path = Path(".environment_id")
    if not env_path.exists():
        raise SystemExit(".environment_id not found. Run setup_environment.py first.")

    environment_id = env_path.read_text().strip()

    ids_path = Path(".specialist_ids.json")
    if not ids_path.exists():
        raise SystemExit(".specialist_ids.json not found. Run create_specialists.py first.")

    specialist_ids = json.loads(ids_path.read_text())
    pricing_id = specialist_ids.get("pricing")
    if not pricing_id:
        raise SystemExit("No 'pricing' key in .specialist_ids.json")

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # Update the pricing specialist's system prompt to instruct it to use
    # the CRM tools that are available in the environment
    agent = client.beta.agents.retrieve(agent_id=pricing_id)
    print(f"Retrieved pricing specialist: {agent.id} ({agent.name})")

    crm_instructions = (
        "\n\n# CRM Access\n\n"
        "You have access to a CRM system with past deal data. Use your bash "
        "tool to query it by running:\n"
        "  python mcp_crm_server.py --query <search_term>\n\n"
        "Available queries:\n"
        "- `python mcp_crm_server.py --search <term>` — search deals by customer/industry\n"
        "- `python mcp_crm_server.py --deal <id>` — get deal details (deal-001, deal-002, etc.)\n"
        "- `python mcp_crm_server.py --industry <industry>` — filter by industry\n"
        "- `python mcp_crm_server.py --stats` — win rate summary\n\n"
        "Always query the CRM for comparable deals before making pricing recommendations. "
        "Cite specific deal IDs and customer names."
    )

    new_system = agent.system + crm_instructions

    client.beta.agents.update(
        pricing_id,
        version=agent.version,
        system=new_system,
    )
    print("Updated pricing specialist with CRM query instructions.")
    print("The specialist will use bash to query the CRM server during deals.")


if __name__ == "__main__":
    main()
