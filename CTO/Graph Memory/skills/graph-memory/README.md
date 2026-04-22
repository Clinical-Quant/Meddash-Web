# Graph Memory Skill

## One-Line Summary
Unified memory mosaic for Agent Zero - creates blockchain-like memory nodes across all agents for spatial awareness of work progress and project state.

---

## Quick Install

### On Any A0 Instance:

```bash
# Copy to your A0 skills folder
cp -r graph-memory/ /a0/usr/skills/

# Or clone from your repo
git clone <your-repo>/graph-memory /a0/usr/skills/graph-memory
```

### First Use:

```
You: state where MYPROJECT

Agent: 📍 No checkpoints found for project 'MYPROJECT'
       (The system auto-creates its folder structure)

You: state checkpoint MYPROJECT

Agent: ✅ Checkpoint saved: MEM_MYPROJECT_...
```

---

## Installation on Other A0 Instances

This skill is **ubiquitous** - it auto-detects its location:

| Priority | Location |
|----------|----------|
| 1 | `$A0_GRAPH_MEMORY_ROOT/Graph Memory/` (env var) |
| 2 | `<project_root>/Graph Memory/` |
| 3 | `<workdir>/Graph Memory/` |
| 4 | `/a0/usr/Graph Memory/` (fallback) |

### Docker Path (Your Setup):
```
/a0/usr/Graph Memory/
```

### Windows Path:
```
C:\Users\email\agent-zero\agent-CQ\usr\Graph Memory\
```

---

## Commands

| Command | Description |
|---------|-------------|
| `state where <project>` | Show current position in project |
| `state checkpoint <project>` | Create memory node from current session |
| `state timeline <project>` | Show chronological progression |
| `state files <project>` | List all files touched |
| `state map <project>` | Show full connection graph |
| `state cross <proj_a> <proj_b>` | Find connections between projects |

---

## File Structure Created

```
Graph Memory/
├── connection_graph.json    ← THE MOSAIC (shared by all agents)
├── artifact_index.json      ← File → Memory links
├── time_index.json          ← Chronological index
└── nodes/                   ← Individual memory nodes
    ├── MEM_PROJECT_20260421_143052.json
    └── ...
```

---

## Usage Example

```markdown
# Start of session
You: state where QSL

📍 WHERE AM I?

Project: QSL
Latest Node: MEM_QSL_20260421_143052
Timestamp: 2026-04-21 14:30:52

## Current Work
Working on LinkedIn skill integration for content automation.

## Status
🟢 Active

## Files Involved
- linkedin-skill.md (created)
- oauth_flow.py (modified)

## Next Action
Test OAuth flow

## Blockers
None

# Do work...
You: Continue building the LinkedIn skill
Agent: [creates files, writes code...]

# End of session
You: state checkpoint QSL

✅ Checkpoint saved: MEM_QSL_20260421_160000
- Artifacts tracked: 2
- Connections found: 3

# Days later...
You: state where QSL
Agent: [Shows exactly where you left off with full context]
```

---

## Cross-Agent Sharing

**All agents share the same connection_graph.json.**

- Agent 0 creates node → Subordinates can see it
- Developer agent creates node → Agent 0 can see it
- Research agent creates node → All agents see it

This creates a **unified memory mosaic** across your entire agent ecosystem.

---

## Integration with A0 Memory

The skill integrates with Agent Zero's FAISS memory:

```python
# When you checkpoint, it saves to both:
# 1. connection_graph.json (shared graph)
# 2. A0 FAISS memory (for semantic search)
```

---

## Files Included

| File | Description |
|------|-------------|
| `SKILL.md` | Skill definition and instructions |
| `graph_memory.py` | Core implementation |
| `README.md` | This file |

---

## License

MIT
