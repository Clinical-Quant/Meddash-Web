# Graph Memory & A2A Cross-Integration Documentation

## Overview

This document captures the complete context, design decisions, and implementation of the **Graph Memory** system for Agent Zero, including the A2A cross-integration strategy for COO agent coordination.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Architecture Design](#architecture-design)
3. [Implementation](#implementation)
4. [A2A Cross-Integration](#a2a-cross-integration)
5. [Installation Guide](#installation-guide)
6. [Usage Commands](#usage-commands)

---

## Problem Statement

### The Challenge

When building multiple projects in parallel (QSL, MedDash-CQ, Ceylon B2B), the user faced:

1. **Context Window Overflow**: Human memory can't track multiple parallel projects
2. **Session Continuity**: Each new AI session starts from zero context
3. **Positional Memory Loss**: Forgetting where you were in each workflow
4. **Linear Memory Failure**: Development is non-linear (bugs, features, side quests) but memory was linear
5. **No Spatial Awareness**: Can't see how work on one component affects others

### The Insight

> "We need a very strong waypoint system showing where we are in the main project and what side quests we are doing for what reason - more like a horizontal memory... a mosaic pattern like a human would."

### The Solution

A **Graph Memory** system that:
- Creates blockchain-like memory nodes for each work session
- Tracks artifacts (files, scripts, chats) per session
- Discovers connections between nodes automatically
- Provides "Where am I?" spatial awareness
- Works across all agents in the same A0 instance
- Can be queried remotely via A2A protocol for COO coordination

---

## Architecture Design

### Core Concepts

#### Memory Node
```
MEM_<PROJECT>_<TIMESTAMP>
Example: MEM_MEDDASH-CQ_20260421_061133

Each node contains:
- Summary of work done
- Artifacts created/modified (files, scripts, chats)
- Timestamp
- Status (active, paused, completed, blocked)
- Next action
- Blockers
- Connections to other nodes
```

#### Connection Graph
```
Graph Memory/
├── connection_graph.json    ← THE MOSAIC (shared by all agents)
├── artifact_index.json      ← File → Memory links
├── time_index.json          ← Chronological index
└── nodes/                   ← Individual memory nodes
    ├── MEM_PROJECT_20260421_143052.json
    └── ...
```

### The Blockchain Analogy

| Blockchain Concept | Graph Memory Equivalent |
|-------------------|------------------------|
| **Block** | Memory Node (each work session, decision, chat) |
| **Hash/ID** | Memory ID: `MEM_<project>_<timestamp>` |
| **Chain** | Connection Graph: `this connects to that` |
| **Consensus** | All agents see same unified graph |
| **Immutability** | Nodes are append-only (logs) |
| **Timestamps** | Every node has precise time marker |
| **Smart Contracts** | Connection discovery rules (LLM-powered) |

### Hybrid Architecture: File-Based + A2A

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID GRAPH MEMORY SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   INSTANCE A (A0 - Agent-CQ)                 INSTANCE B (OpenClaw COO)          │
│   ┌─────────────────────────────┐             ┌─────────────────────────────┐    │
│   │  File-Based Graph Memory    │             │  Remote COO Agent           │    │
│   │  /a0/CTO/Graph Memory/      │             │  (monitors via A2A)         │    │
│   │                             │             │                             │    │
│   │  connection_graph.json ◄─────┼─────────────┤ a2a_chat()                  │    │
│   │                             │  A2A        │  "What's new in MEDDASH-CQ?"│    │
│   │  All same-instance agents:   │  Protocol    │                             │    │
│   │  - Agent 0                   │             │  Receives:                  │    │
│   │  - Developer subordinate      │             │  - Latest checkpoints       │    │
│   │  - Researcher subordinate    │             │  - Blockers & issues        │    │
│   └─────────────────────────────┘             │  - Cross-project status     │    │
│                                               └─────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### Files Created

| Location | File | Purpose |
|----------|------|--------|
| `/a0/CTO/Graph Memory/` | `connection_graph.json` | THE MOSAIC - shared by all agents |
| `/a0/CTO/Graph Memory/` | `artifact_index.json` | File → Memory links |
| `/a0/CTO/Graph Memory/` | `time_index.json` | Chronological index |
| `/a0/CTO/Graph Memory/nodes/` | `MEM_*.json` | Individual memory nodes |
| `/a0/CTO/Graph Memory/skills/` | `graph-memory/` | Skill folder |
| `/a0/CTO/Graph Memory/skills/graph-memory/` | `SKILL.md` | Skill definition |
| `/a0/CTO/Graph Memory/skills/graph-memory/` | `graph_memory.py` | Core implementation |
| `/a0/CTO/Graph Memory/skills/graph-memory/` | `README.md` | Installation guide |

### Python Implementation Summary

The `graph_memory.py` implements:

```python
class GraphMemory:
    def __init__(self, project: str):
        """Initialize with ubiquitous path detection."""
        
    def checkpoint(self, summary, artifacts, status, next_action, blockers, connections):
        """Create memory node from current session."""
        
    def where(self) -> Dict:
        """Get current position in project."""
        
    def timeline(self, limit: int = 10) -> List[Dict]:
        """Get chronological timeline for project."""
        
    def files(self) -> Dict[str, List[Dict]]:
        """Get all files touched in project."""
        
    def map(self) -> Dict:
        """Get full connection graph for project."""
        
    def cross_project(self, other_project: str) -> Dict:
        """Find connections between projects."""
        
    def add_connection(self, node_a, relation, node_b) -> Dict:
        """Manually add connection between nodes."""
```

### Path Resolution (Ubiquitous)

The skill finds Graph Memory in this order:

1. Environment variable: `A0_GRAPH_MEMORY_ROOT`
2. Project root: `<project_root>/Graph Memory/`
3. Workdir: `<workdir>/Graph Memory/`
4. A0 root: `/a0/usr/Graph Memory/`

**Primary Location (Windows-accessible):**
```
Windows: C:\Users\email\.gemini\antigravity\CTO\Graph Memory\
Docker:  /a0/CTO/Graph Memory/
```

---

## A2A Cross-Integration

### Why A2A?

For cross-instance COO coordination, we need to query Graph Memory from other agent systems:
- OpenClaw COO agent
- Another A0 instance
- Any FastA2A-compatible agent

### FastA2A: Open Protocol

**FastA2A is NOT Agent Zero-specific!** It's an open protocol that any agent can implement.

| Agent System | FastA2A Compatible? |
|--------------|---------------------|
| Agent Zero | ✅ Built-in `a2a_chat` tool |
| OpenClaw | ✅ If it implements /a2a endpoint |
| LangGraph | ✅ Via FastA2A library |
| CrewAI | ✅ Via FastA2A library |
| Custom agents | ✅ Implement the protocol |

### A2A Query Example

```json
{
  "tool_name": "a2a_chat",
  "tool_args": {
    "agent_url": "http://agent-cq-instance:8000/a2a",
    "message": "state where MEDDASH-CQ",
    "reset": false
  }
}
```

### COO Dashboard Concept

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COO AGENT DASHBOARD                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   🏢 INSTANCE: Agent-CQ (A0)                                                    │
│   ├── MEDDASH-CQ: 🟢 Active - Graph Memory skill built                           │
│   ├── QSL: 🟡 Paused - Waiting for content engine                                │
│   └── Ceylon: 🔴 Blocked - Dependencies needed                                    │
│                                                                                 │
│   🏢 INSTANCE: Agent-QSL (A0)                                                   │
│   ├── Content Engine: 🟢 Active - 60% complete                                  │
│   └── LinkedIn Skill: ✅ Done - Deployed to production                           │
│                                                                                 │
│   📊 CROSS-INSTANCE CONNECTIONS                                                 │
│   ├── Content Engine → MedDash (shared dependency)                              │
│   ├── LinkedIn Skill → QSL, Ceylon (shared component)                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### A2A Commands for COO

| COO Query | Response |
|----------|----------|
| `state status all` | Summary of all projects across instances |
| `state blockers` | Any blockers requiring attention |
| `state timeline <project>` | Recent activity for a project |
| `state cross-project` | Dependencies between instances |

---

## Installation Guide

### On Any A0 Instance

```bash
# Copy skill folder
cp -r /a0/CTO/Graph Memory/skills/graph-memory/ /a0/usr/skills/

# Or clone from repo
git clone <repo>/graph-memory /a0/usr/skills/graph-memory
```

### First Use

```
You: state where MYPROJECT

Agent: 📍 No checkpoints found for project 'MYPROJECT'
       (System auto-creates directory structure)

You: state checkpoint MYPROJECT

✅ Checkpoint saved: MEM_MYPROJECT_...
```

### Environment Variable (Optional)

```bash
export A0_GRAPH_MEMORY_ROOT="/custom/path"
```

---

## Usage Commands

### Session Start: "Where Am I?"
```
You: state where MEDDASH-CQ

📍 WHERE AM I?

Project: MEDDASH-CQ
Latest Node: MEM_MEDDASH-CQ_20260421_061133
Timestamp: 2026-04-21T06:11:33

## Current Work
Built Graph Memory skill for Agent Zero - a unified memory mosaic...

## Status
🟢 Active

## Files Involved
- /a0/usr/skills/graph-memory/SKILL.md
- /a0/usr/skills/graph-memory/graph_memory.py
...

## Next Action
Test checkpoint commands and integrate with A0 memory system

## Blockers
None

## Recent Timeline
1. 2026-04-21T06:11 | Built Graph Memory skill... ← CURRENT
```

### Session End: Checkpoint
```
You: state checkpoint MEDDASH-CQ

✅ Checkpoint saved: MEM_MEDDASH-CQ_20260421_160000
- Timestamp: 2026-04-21T16:00:00
- Artifacts tracked: 3
- Connections found: 2
```

### Other Commands

| Command | Description |
|---------|-------------|
| `state timeline <project>` | Chronological progression |
| `state files <project>` | All files touched |
| `state map <project>` | Full connection graph |
| `state cross <proj_a> <proj_b>` | Cross-project connections |

---

## Integration with A0 Memory

Graph Memory integrates with Agent Zero's FAISS memory:

```python
# When checkpoint is created:
# 1. Saves to connection_graph.json (shared graph)
# 2. Saves to A0 FAISS memory (for semantic search)
# 3. Creates individual node JSON file
```

This enables:
- Semantic search via `memory_load`
- Cross-agent sharing via file-based graph
- Remote queries via A2A protocol

---

## First Checkpoint Created

```
MEM_MEDDASH-CQ_20260421_061133
Timestamp: 2026-04-21T06:11:33
Summary: Built Graph Memory skill for Agent Zero - a unified memory mosaic that creates blockchain-like memory nodes across all agents.
Files: SKILL.md, graph_memory.py, connection_graph.json, artifact_index.json, time_index.json
Status: Active
Next Action: Test checkpoint commands and integrate with A0 memory system
```

---

## References

- claude-obsidian: https://github.com/AgriciDaniel/claude-obsidian (inspiration for Hot Cache pattern)
- Mem0: https://github.com/mem0ai/mem0 (memory layer architecture)
- FastA2A: Open agent-to-agent protocol
- Andrej Karpathy's LLM Wiki Pattern: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

---

## License

MIT
