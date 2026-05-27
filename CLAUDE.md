# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A hackathon project (Partner Basecamp 2026) implementing a multi-agent "Deal Desk" swarm using the Claude Managed Agents API (beta: `managed-agents-2026-04-01`). A coordinator agent fans out work to 4 specialist sub-agents (Pricing, Legal, Technical Fit, Competitive Intel), each with domain-specific skills, to produce a proposal response from an inbound RFP.

## Setup & Run

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."

python setup_environment.py      # creates cloud environment (idempotent)
python create_specialists.py     # creates 4 sub-agents → .specialist_ids.json
python upload_skills.py          # uploads skills/ and attaches to specialists
python create_coordinator.py     # creates coordinator → .coordinator_id
python run_deal_desk.py          # runs the swarm, streams events, saves output to outputs/
```

Scripts must be run in this order. Each saves state to dotfiles (`.specialist_ids.json`, `.skill_ids.json`, `.coordinator_id`, `.environment_id`) that downstream scripts depend on.

## Architecture

- **Coordinator** (`claude-opus-4-7`): orchestrates specialists, synthesises outputs, produces final document
- **Specialists** (`claude-sonnet-4-6` / `claude-haiku-4-5`): narrow-scope agents with domain skills
- **Skills** (`skills/<name>/SKILL.md`): custom skill bundles uploaded via Skills API, one per specialist
- **Synthetic data** (`synthetic-data/`): RFP, past wins, product overview — inlined into the user message at runtime

All agents use `agent_toolset_20260401` (file ops, web search, web fetch, bash). The coordinator uses `multiagent: coordinator` config to list specialists in its callable roster.

## Key API Patterns

- Beta header: `anthropic-beta: managed-agents-2026-04-01`
- Session events are streamed via `client.beta.sessions.events.stream(session_id)`
- Skills are uploaded with `anthropic.lib.files_from_dir` and attached via `agents.update(skills=[...])`
- `upload_skills.py` is idempotent — detects existing skills by `display_title` and skips re-upload

## Stretch Goals

- `stretch_critic_subagent.py`: adds a critic agent that reviews the coordinator's draft
- `download_deliverable.py`: downloads files from a completed session
