# Dashboard Quick Start Guide

## Launch the Dashboard

### Option 1: Using the launch script (recommended)
```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

### Option 2: Manual start
```bash
source .venv/bin/activate
pip install flask  # if not already installed
python dashboard_server.py
```

Then open http://localhost:5000 in your browser.

## What You'll See

### The Demo Moment
The most impressive visual happens when the coordinator delegates to all 4 specialists simultaneously:

1. All 4 specialist cards pulse with red glow animation
2. Animated arrows shoot from coordinator to each specialist
3. Event stream floods with "delegate" events
4. Active count jumps to 4 simultaneously

This showcases the **parallel execution** of the swarm.

### Visual States

**Agent Cards:**
- Grey border + grey icon = Idle (waiting)
- Red border + pulsing glow = Running (actively processing)
- Green border + glow = Completed (finished)

**Connection Lines:**
- Animated red arrows flow between agents during delegation/reply

**Event Stream (right sidebar):**
- Shows every event in real-time
- Color-coded by event type
- Auto-scrolls to latest events

**Timeline (bottom):**
- Progress bar showing elapsed time
- Estimates ~60 seconds for full execution

**Status Badge (top-right):**
- Shows overall swarm state
- Pulses when active

**Stats (header):**
- Active count: How many agents running now
- Completed count: How many agents finished

## Demo Tips

### For a Live Presentation

1. **Open the dashboard before the demo starts**
2. **Narrate as events happen:**
   - "The coordinator is reading the RFP..."
   - "Now it's delegating to all 4 specialists in parallel - watch them light up!"
   - "All specialists are running simultaneously - that's the power of the swarm"
   - "Specialists are sending back their analysis..."
   - "Coordinator is synthesizing the final proposal..."

3. **Point out the parallel execution:**
   - When all 4 cards turn red at once
   - The event stream showing rapid delegations
   - The active count jumping to 4

4. **Show the outputs afterward:**
   - Check `outputs/` folder for generated files
   - Show the coordinator transcript
   - Display any Word docs or structured outputs

### For a Recorded Demo

- Use a large monitor (1920x1080 or higher)
- Full-screen the browser
- Screen recording at 60fps captures the animations smoothly
- Consider zooming into specific sections:
  - Coordinator card during initial analysis
  - All 4 specialists during parallel execution
  - Event stream during peak activity
  - Timeline as it progresses

## Architecture Overview

```
User opens browser → http://localhost:5000
                          ↓
                   dashboard_server.py
                          ↓
              Creates Anthropic session
                          ↓
         Streams events via SSE to frontend
                          ↓
                   index.html (browser)
                          ↓
         Real-time visualization updates
```

## Event Flow

```
1. User message sent → Coordinator receives RFP
2. thread_created → Coordinator thread spawned
3. thread_running → Coordinator analyzing
4. message_sent (x4) → Delegating to all specialists
5. thread_created (x4) → All specialist threads spawn
6. thread_running (x4) → All specialists active (THE DEMO MOMENT)
7. message_received (x4) → Specialists reply back
8. thread_running → Coordinator synthesizing
9. status_idle → Swarm finished
```

## Agents in the Swarm

### Coordinator (Center/Top)
- Orchestrates the entire process
- Delegates to specialists
- Synthesizes final proposal
- Icon: 🎯

### Pricing Specialist
- Analyzes commercial terms
- Recommends pricing structure
- Assesses margin risks
- Icon: 💰

### Legal Reviewer
- Reviews contract clauses
- Flags conflicts with standards
- Recommends counter-positions
- Icon: ⚖️

### Technical Fit Specialist
- Assesses product capabilities
- Maps RFP requirements to features
- Identifies gaps and risks
- Icon: 🔧

### Competitive Intel Analyst
- Identifies likely competitors
- Recommends positioning strategy
- Highlights differentiation angles
- Icon: 🎯

## Troubleshooting

### Dashboard doesn't load
- Check that Flask is installed: `pip install flask`
- Verify port 5000 is not in use: `lsof -i :5000`
- Check console for errors: Browser DevTools → Console

### No events appearing
- Verify `.coordinator_id` and `.environment_id` exist
- Check `ANTHROPIC_API_KEY` in `.env` file
- Look at server console output for errors

### Agents don't light up
- Check browser console for JavaScript errors
- Verify agent name mapping matches server output
- Refresh the page to restart

### Connection error
- Ensure all setup scripts were run successfully
- Check API key is valid
- Verify network connection

## Customization

### Change Colors
Edit the CSS in `dashboard/index.html`:
```css
/* Sia Partners brand colors */
#E4002B - Primary red
#1A1A2E - Dark navy
#0D0D1A - Very dark background
```

### Add More Agents
1. Add HTML node in specialists-row
2. Update agentMapping in JavaScript
3. Adjust grid-template-columns for layout

### Modify Animations
Edit keyframes in CSS:
- `@keyframes pulse` - Running state glow
- `@keyframes flow` - Connection line animation
- `@keyframes slideIn` - Event stream entry

### Change Timeline Estimate
Update in JavaScript:
```javascript
const estimatedTotal = 60000; // milliseconds
```

## Files Created

```
dashboard/
├── index.html          # Main dashboard (self-contained)
└── README.md           # Dashboard documentation

dashboard_server.py     # Flask server + SSE streaming
run_dashboard.sh        # Quick launch script
DASHBOARD_GUIDE.md      # This file
```

## Next Steps

After the dashboard demo, you can:

1. **Check outputs:**
   ```bash
   ls outputs/
   cat outputs/coordinator-transcript.txt
   ```

2. **View full session on platform:**
   The server prints a URL to see all threads and sub-agents

3. **Run again with different RFP:**
   - Replace `synthetic-data/rfp-acme-corp.md`
   - Restart the dashboard server
   - Refresh browser

4. **Export recording:**
   - Use OBS or QuickTime to record the screen
   - Show in presentations or documentation

## Support

For issues or questions:
- Check the main README.md
- Review dashboard/README.md for detailed docs
- Check server console logs for errors
- Verify all setup scripts completed successfully
