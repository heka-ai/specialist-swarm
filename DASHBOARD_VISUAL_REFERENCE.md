# Dashboard Visual Reference

This document describes what the dashboard looks like so you can visualize it before running.

## Overall Layout

```
┌─────────────────────────────────────────────────────────────────────┬──────────────────┐
│                                                                     │                  │
│                      Deal Desk Swarm                                │  Event Stream    │
│              Real-Time Multi-Agent Orchestration                    │                  │
│                                                                     │  ┌────────────┐  │
│              [0 Active]  [0 Completed]                              │  │ 🚀 Thread  │  │
│                                                                     │  │ spawned    │  │
│  ┌─────────────────────────────────────────────────────────┐      │  └────────────┘  │
│  │                                                           │      │                  │
│  │                    ┌──────────────┐                      │      │  ┌────────────┐  │
│  │                    │   🎯         │                      │      │  │ ⚡ Running  │  │
│  │                    │ Coordinator  │                      │      │  │ agent      │  │
│  │                    │ Orchestrator │                      │      │  └────────────┘  │
│  │                    │   [Status]   │                      │      │                  │
│  │                    └──────────────┘                      │      │  ┌────────────┐  │
│  │                                                           │      │  │ ➡️ Delegate │  │
│  │                                                           │      │  │ to agent   │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │      │  └────────────┘  │
│  │  │  💰     │  │  ⚖️     │  │  🔧     │  │  🎯     │   │      │                  │
│  │  │ Pricing │  │ Legal   │  │Technical│  │Competi- │   │      │  ┌────────────┐  │
│  │  │ Special │  │ Reviewer│  │  Fit    │  │  tive   │   │      │  │ ⬅️ Reply    │  │
│  │  │  [Idle] │  │  [Idle] │  │ [Idle]  │  │ [Idle]  │   │      │  │ from agent │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │      │  └────────────┘  │
│  │                                                           │      │                  │
│  └─────────────────────────────────────────────────────────┘      │                  │
│                                                                     │  ┌────────────┐  │
│  ┌─────────────────────────────────────────────────────────┐      │  │ ✅ Swarm   │  │
│  │ Execution Timeline                                        │      │  │ finished   │  │
│  │ [████████░░░░░░░░░░░░░░░░░░░░░░░] 40%                    │      │  └────────────┘  │
│  └─────────────────────────────────────────────────────────┘      │                  │
│                                                                     │   125 events     │
└─────────────────────────────────────────────────────────────────────┴──────────────────┘
```

## Color Scheme (Sia Partners)

### Dark Theme
- **Background**: `#0D0D1A` - Very dark blue-black
- **Cards**: `#1A1A2E` - Dark navy
- **Borders**: `#2A2A3E` - Medium grey

### Status Colors
- **Primary (Sia Red)**: `#E4002B` - Running state, connections, accents
- **Success Green**: `#00D084` - Completed state
- **Idle Grey**: `#666` - Waiting state
- **Text**: `#F5F5F5` - Off-white for readability

## Agent Card States

### Idle State (Grey)
```
┌─────────────┐
│   💰        │  ← Icon in grey (#3A3A4E)
│   Pricing   │
│  Specialist │
│             │
│   [Idle]    │  ← Grey text (#666)
└─────────────┘
   ↑ Grey border (#2A2A3E)
```

### Running State (Red with Pulse)
```
┌═════════════┐  ← Red border (#E4002B)
║   💰        ║  ← Icon in red, pulsing
║   Pricing   ║     Glow effect around card
║  Specialist ║
║             ║
║  [Running]  ║  ← Red text
└═════════════┘
   ↑ Pulsing shadow (animated)
```

### Completed State (Green)
```
┌─────────────┐  ← Green border (#00D084)
│   💰        │  ← Icon in green
│   Pricing   │     Subtle glow
│  Specialist │
│             │
│ [Completed] │  ← Green text
└─────────────┘
```

## Animation Sequences

### 1. Initial Load
```
All agents: [Idle] grey
No connections visible
Event stream: "Waiting for swarm to start..."
Timeline: 0%
```

### 2. Coordinator Starts
```
Coordinator: [Idle] → [Running] (pulse animation)
Connection lines: None yet
Event stream: "🚀 Thread spawned: Coordinator"
              "⚡ Running: Coordinator"
Timeline: 5%
```

### 3. Parallel Delegation (THE DEMO MOMENT)
```
Coordinator: [Running] (pulsing)
   ↓ Red arrow animates (bezier curve)
   ↓ Red arrow animates
   ↓ Red arrow animates
   ↓ Red arrow animates
   ↓
All 4 specialists: [Idle] → [Running] SIMULTANEOUSLY
   - All 4 cards pulse red at once
   - 4 animated arrows flow from coordinator to each specialist
   - Glow effects on all cards

Event stream floods:
"➡️ Delegate to: Pricing Specialist"
"➡️ Delegate to: Legal Reviewer"
"➡️ Delegate to: Technical Fit Specialist"
"➡️ Delegate to: Competitive Intel Analyst"
"🚀 Thread spawned: Pricing Specialist"
[... more events ...]

Stats update:
[4 Active] [0 Completed]

Timeline: 20%
```

### 4. Specialists Complete (Staggered)
```
First specialist finishes:
   Technical Fit: [Running] → [Completed] (green)
   Green arrow animates back to Coordinator
   Event: "⬅️ Reply from: Technical Fit Specialist"
   Stats: [3 Active] [1 Completed]

Second specialist:
   Pricing: [Running] → [Completed] (green)
   Green arrow back
   Stats: [2 Active] [2 Completed]

Third, fourth specialists follow...
   Stats: [0 Active] [4 Completed]

Timeline: 70%
```

### 5. Coordinator Synthesis
```
Coordinator: [Running] (still pulsing)
Event: "⚡ Running: Coordinator"
Event: "🔧 Tool: file-write"
Timeline: 90%
```

### 6. Finished
```
Coordinator: [Running] → [Completed] (green)
All specialists: [Completed] (green)
Event: "✅ Swarm finished"
Status badge: "Completed" (green)
Timeline: 100%
Stats: [0 Active] [5 Completed]
```

## Connection Lines

### Delegate Line (Coordinator → Specialist)
```
Coordinator
    ↓
    ↓  ← Red curved line (#E4002B)
    ↓     Animated stroke-dashoffset
    ↓     Bezier curve (smooth)
    ↓     Arrowhead at end
    ↓
Specialist
```

Animation:
- Starts invisible
- Stroke dashoffset animates from 1000 to 0
- Takes 1.5 seconds
- Fades out after completion

### Reply Line (Specialist → Coordinator)
```
Specialist
    ↑
    ↑  ← Green curved line (#00D084)
    ↑     Animated upward
    ↑     Bezier curve
    ↑     Arrowhead at top
    ↑
Coordinator
```

Same animation pattern, green color.

## Event Stream Sidebar

### Header
```
┌──────────────────┐
│ Event Stream     │
│ 47 events        │  ← Counter updates in real-time
└──────────────────┘
```

### Event Items (Color-coded)
```
┌─────────────────────────────────┐
│ │ 14:32:45 🚀 Thread spawned:   │  ← Red left border
│ │            Pricing Specialist │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ │ 14:32:46 ⚡ Running: Legal    │  ← Orange left border
│ │            Reviewer            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ │ 14:32:48 ➡️ Delegate to:      │  ← Blue left border
│ │            Technical Fit       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ │ 14:32:52 ⬅️ Reply from:        │  ← Green left border
│ │            Competitive Intel   │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ │ 14:32:55 🔧 Tool: web-search  │  ← Purple left border
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ▓ 14:32:58 ✅ Swarm finished    │  ← Green background
└─────────────────────────────────┘
```

Events auto-scroll, newest at top.

## Status Badge (Top-Right)

### States
```
[Initializing...]     ← Grey, no glow
[Connected]           ← Red, pulsing glow
[Running]             ← Red, pulsing glow
[Completed]           ← Green, steady glow
[Connection Error]    ← Grey, no glow
```

## Timeline Bar (Bottom)

```
Execution Timeline
┌────────────────────────────────────────────┐
│████████████████████░░░░░░░░░░░░░░░░░░░░░░░│ 45%
└────────────────────────────────────────────┘
  ↑                    ↑                     ↑
  0s                   30s                   60s

Red gradient fill (#E4002B → #FF6B35)
Smooth animation, updates every second
```

## Responsive Behavior

### On Large Screens (1920x1080+)
- Specialists in 4-column grid
- Large card sizes
- Ample spacing
- Full visibility of all elements

### On Medium Screens (1366x768)
- Slightly smaller cards
- Tighter spacing
- Event stream remains at 400px width
- Still fully functional

### On Small Screens (<1280px)
- Optimized for demo viewing
- May need zoom adjustment
- Dashboard designed for large screen demos

## Typography

- **Headings**: System fonts (-apple-system, Segoe UI, etc.)
- **H1**: 2.5rem (40px), bold, white
- **Subtitle**: 1.1rem (17.6px), Sia red
- **Agent names**: 1.2rem (19.2px), semibold
- **Status text**: 0.85rem (13.6px), uppercase, tracking
- **Event text**: 0.9rem (14.4px)

## Icons (Emoji)

- Coordinator: 🎯 (target)
- Pricing: 💰 (money bag)
- Legal: ⚖️ (balance scale)
- Technical: 🔧 (wrench)
- Competitive: 🎯 (target)

Event types:
- Thread spawned: 🚀
- Running: ⚡
- Delegate: ➡️
- Reply: ⬅️
- Tool: 🔧
- Finished: ✅

## Performance Details

- **60fps animations**: CSS transforms and opacity only
- **Hardware accelerated**: GPU-based rendering
- **Smooth transitions**: 0.3s ease timing
- **No jank**: Efficient DOM updates
- **Low memory**: Events capped at 100 items

## Accessibility Notes

- High contrast (WCAG AAA compliant)
- Large text sizes
- Clear status indicators
- Color + shape + text for states (not just color)
- Keyboard navigation support
- Screen reader friendly event messages

## Print/Screenshot View

If you need to capture the dashboard:
- Take screenshot at peak parallel execution (all 4 specialists running)
- Shows: 4 red pulsing cards, animated lines, event stream active
- Best demonstrates the parallel architecture
- Use full screen (F11) for clean capture

## Demo Best Practices

1. **Full screen the browser** (F11) - removes browser chrome
2. **Dark mode environment** - room lighting low for screen visibility
3. **Large display** - 50"+ TV or projector ideal
4. **Pre-test** - run `dashboard_test.py` to verify animations work
5. **Narrate live** - talk through what's happening as you see it
6. **Point at cards** - physically gesture to running agents
7. **Pause on parallel** - let the audience absorb the simultaneous execution

This visual reference should help you understand what you'll see when you run the dashboard!
