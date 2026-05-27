"""
Synthetic CRM MCP Server — exposes past-wins data as queryable tools.

Runs on stdio transport. Used by the pricing specialist via MCP tool config.

Usage:
    python mcp_crm_server.py
"""

import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent / "synthetic-data" / "past-wins.json"
_raw = json.loads(DATA_PATH.read_text())
DEALS: list[dict] = _raw["comparable_deals"]

# Assign stable IDs based on index
for idx, deal in enumerate(DEALS):
    deal["deal_id"] = f"deal-{idx + 1:03d}"

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

server = FastMCP("CRM Past Wins")


@server.tool()
def search_past_wins(query: str) -> str:
    """Fuzzy search across deals by customer name, industry, or deal size.

    Args:
        query: Search term to match against customer name, industry, notes,
               won_on, lost_on fields. Case-insensitive.
    """
    query_lower = query.lower()
    results = []
    for deal in DEALS:
        searchable = " ".join(
            str(v) for v in [
                deal.get("customer", ""),
                deal.get("industry", ""),
                deal.get("notes", ""),
                deal.get("won_on", ""),
                deal.get("lost_on", ""),
                deal.get("tier", ""),
                str(deal.get("deal_size_annual_usd", "")),
            ]
        ).lower()
        if query_lower in searchable:
            results.append(deal)

    if not results:
        return json.dumps({"matches": [], "message": f"No deals matched '{query}'"})
    return json.dumps({"matches": results, "count": len(results)}, indent=2)


@server.tool()
def get_deal_details(deal_id: str) -> str:
    """Get full details of a specific past deal.

    Args:
        deal_id: The deal identifier, e.g. 'deal-001'.
    """
    for deal in DEALS:
        if deal["deal_id"] == deal_id:
            return json.dumps(deal, indent=2)
    return json.dumps({"error": f"Deal '{deal_id}' not found. Valid IDs: {[d['deal_id'] for d in DEALS]}"})


@server.tool()
def list_wins_by_industry(industry: str) -> str:
    """Filter past wins by industry. Case-insensitive partial match.

    Args:
        industry: Industry name or partial match, e.g. 'manufacturing', 'defence'.
    """
    industry_lower = industry.lower()
    results = [
        deal for deal in DEALS
        if industry_lower in deal.get("industry", "").lower()
    ]
    if not results:
        industries = sorted(set(d.get("industry", "") for d in DEALS))
        return json.dumps({
            "matches": [],
            "message": f"No deals in industry '{industry}'.",
            "available_industries": industries,
        })
    return json.dumps({"matches": results, "count": len(results)}, indent=2)


@server.tool()
def get_win_rate_stats() -> str:
    """Get summary statistics across all past deals: win rate, avg deal size, avg discount, industries covered."""
    wins = [d for d in DEALS if d.get("won_on")]
    losses = [d for d in DEALS if d.get("lost_on")]
    total = len(DEALS)

    win_sizes = [d["deal_size_annual_usd"] for d in wins]
    win_discounts = [d["discount_from_list"] for d in wins]
    win_terms = [d["term_years"] for d in wins]

    stats = {
        "total_deals": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / total, 2) if total else 0,
        "avg_deal_size_usd": round(sum(win_sizes) / len(win_sizes)) if win_sizes else 0,
        "avg_discount_from_list": round(sum(win_discounts) / len(win_discounts), 3) if win_discounts else 0,
        "avg_term_years": round(sum(win_terms) / len(win_terms), 1) if win_terms else 0,
        "industries": sorted(set(d.get("industry", "") for d in DEALS)),
        "competitors_seen": sorted(set(
            c for d in DEALS for c in d.get("primary_competitors", [])
        )),
    }
    return json.dumps(stats, indent=2)


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    # CLI mode: allow direct queries without MCP transport
    if args and args[0].startswith("--"):
        cmd = args[0]
        val = args[1] if len(args) > 1 else ""

        if cmd == "--search":
            print(search_past_wins(val))
        elif cmd == "--deal":
            print(get_deal_details(val))
        elif cmd == "--industry":
            print(list_wins_by_industry(val))
        elif cmd == "--stats":
            print(get_win_rate_stats())
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: --search <term> | --deal <id> | --industry <name> | --stats")
            sys.exit(1)
    else:
        server.run(transport="stdio")
