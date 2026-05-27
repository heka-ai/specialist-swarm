# Deal Desk Swarm - Live Dashboard

An impressive real-time visualization of the multi-agent swarm executing in parallel. Perfect for hackathon demos on a big screen.

## Features

### Visual Elements

1. **Agent Nodes** - 5 cards showing the coordinator and 4 specialists
   - Coordinator (center/top): Deal Desk Orchestrator
   - Pricing Specialist: Commercial terms analysis
   - Legal Reviewer: Contract compliance
   - Technical Fit Specialist: Capability assessment
   - Competitive Intel Analyst: Market positioning

2. **Status Indicators**
   - **Idle** (grey): Agent waiting to start
   - **Running** (red pulse): Agent actively processing
   - **Completed** (green): Agent finished its task

3. **Connection Lines** - Animated arrows showing:
   - Delegation: Coordinator → Specialist (blue arrow)
   - Reply: Specialist → Coordinator (green arrow)

4. **Event Stream** - Real-time sidebar showing:
   - Thread spawns
   - Agent status changes
   - Delegations and replies
   - Tool executions
   - Completion status

5. **Timeline** - Visual progress bar at the bottom

6. **Status Badge** - Top-right indicator showing overall swarm state

## Demo Highlights

The dashboard is designed to showcase **parallel execution**. When the coordinator delegates to all 4 specialists:

- All 4 specialist cards light up simultaneously with red pulse animation
- Connection arrows fan out from coordinator to all specialists
- Event stream shows rapid-fire "delegate" events
- This is the key demo moment - the parallel execution is visually obvious

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure swarm is set up:**
   ```bash
   python setup_environment.py
   python create_specialists.py
   python upload_skills.py
   python create_coordinator.py
   ```

3. **Start the dashboard server:**
   ```bash
   python dashboard_server.py
   ```

4. **Open in browser:**
   ```
   http://localhost:5000
   ```

The swarm execution starts automatically when you load the page.

## Brand Colors (Sia Partners)

- Primary: #E4002B (Sia red)
- Secondary: #1A1A2E (dark navy)
- Accent: #FFFFFF (white)
- Background: #0D0D1A (very dark)
- Text: #F5F5F5 (off-white)
- Success: #00D084 (green)

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS (no build step)
- **Backend**: Flask (Python)
- **Event Streaming**: Server-Sent Events (SSE)
- **Agent Framework**: Anthropic Managed Agents API

## Event Types

The dashboard handles these event types from the swarm:

- `session.thread_created` → New agent thread spawned
- `session.thread_status_running` → Agent started processing
- `agent.thread_message_sent` → Coordinator delegating to specialist
- `agent.thread_message_received` → Specialist replying to coordinator
- `agent.tool_use` → Agent using a tool (file ops, web search, etc.)
- `session.status_idle` → Swarm finished

## Architecture

```
dashboard_server.py
├── Loads RFP + supporting docs
├── Creates session with coordinator agent
├── Streams events via SSE to frontend
└── Saves deliverables to outputs/

index.html
├── Connects to /stream endpoint
├── Renders agent nodes with status
├── Animates connections between agents
├── Updates event stream in real-time
└── Shows execution timeline
```

## Tips for Demo

1. **Use a large screen** - The parallel execution is more impressive on a big display
2. **Explain the setup first** - "4 specialists will light up simultaneously when delegated to"
3. **Watch for the parallel delegation** - That's the key moment
4. **Show the event stream** - It moves fast during parallel execution
5. **Zoom in on completed agents** - They turn green with a glow effect

## Troubleshooting

**"Connection Error" in status badge:**
- Check that `ANTHROPIC_API_KEY` is set in `.env`
- Verify `.coordinator_id` and `.environment_id` files exist

**No events appearing:**
- Check console logs in browser DevTools
- Verify SSE connection at `/stream` endpoint
- Ensure swarm setup was completed successfully

**Agents not lighting up:**
- Check agent name mapping in JavaScript
- Verify event types match between backend and frontend
- Look for errors in server console

## Customization

To modify the dashboard:

1. **Change colors**: Edit CSS variables in `<style>` section
2. **Add more agents**: Add new agent nodes in HTML + update mapping in JS
3. **Adjust layout**: Modify grid layout in `.specialists-row`
4. **Change animations**: Edit keyframe animations in CSS
