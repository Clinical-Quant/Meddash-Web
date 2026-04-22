# Graph Memory Skill

## Purpose

Unified memory mosaic for Agent Zero. Creates a blockchain-like graph of memory nodes across all agents, enabling spatial awareness of work progress, file connections, and project state.

## Ubiquitous Design

This skill works on **any Agent Zero instance**. It auto-detects its location:

1. Project-relative: `<project_root>/Graph Memory/`
2. Workdir-relative: `<workdir>/Graph Memory/`
3. A0 root-relative: `/a0/usr/Graph Memory/`

If the Graph Memory folder doesn't exist, the skill creates it on first use.

---

## Core Concepts

### Memory Node
A memory node represents a unit of work or context:

```
MEM_<PROJECT>_<TIMESTAMP>
Example: MEM_QSL_20260421_143052
```

Each node contains:
- Summary of work done
- Artifacts created/modified (files, scripts, chats)
- Timestamp
- Status (active, paused, completed)
- Next action
- Blockers
- Connections to other nodes

### Connection Graph
A shared JSON file that all agents read/write:

```
Graph Memory/
├── connection_graph.json    ← THE MOSAIC (shared by all agents)
├── artifact_index.json      ← File → Memory links
├── time_index.json          ← Chronological index
└── nodes/                   ← Individual memory node details
```

---

## Commands

### `state checkpoint` or `state save`

Create a memory node from the current conversation.

**Usage:**
```
state checkpoint [project_name]
```

**What it does:**
1. Scans conversation for artifacts (files created/modified, scripts run)
2. Generates memory node ID
3. Saves to A0's FAISS memory with full metadata
4. Updates connection_graph.json
5. Updates artifact_index.json
6. Updates time_index.json
7. Discovers connections to previous nodes

**Example:**
```
You: state checkpoint QSL

Agent:
✅ Checkpoint saved: MEM_QSL_20260421_143052
- Summary: Working on LinkedIn skill integration
- Files tracked: linkedin-skill.md, oauth_flow.py
- Scripts tracked: 0
- Connections found: 3
  - Continues: MEM_QSL_20260420_091500
  - Uses: MEM_QSL_20260419_103022
  - For project: MedDash content automation
```

---

### `state where` or `state status`

Show current position in project - like a "You Are Here" marker.

**Usage:**
```
state where [project_name]
```

**What it returns:**
```
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

## Connections (Spatial Context)
├── Continues: MEM_QSL_20260420_091500 (Content engine scaffold)
├── Uses: MEM_QSL_20260419_103022 (OAuth module)
└── Will be used by: MedDash (content client)

## Recent Timeline
1. MEM_QSL_20260420_091500 - Content engine scaffold complete
2. MEM_QSL_20260421_143052 - LinkedIn skill integration (CURRENT)
```

---

### `state map`

Show the full connection graph for a project.

**Usage:**
```
state map [project_name]
```

**What it returns:**
A visual graph showing:
- All memory nodes
- Their connections
- Artifact links
- Status indicators

---

### `state connect`

Manually add a connection between two memory nodes.

**Usage:**
```
state connect <node_a> <relation> <node_b>
```

**Example:**
```
state connect MEM_QSL_20260421_143052 blocks MEM_QSL_20260421_160000
```

---

### `state timeline`

Show chronological progression of work.

**Usage:**
```
state timeline [project_name]
```

**What it returns:**
```
📅 TIMELINE - QSL

2026-04-19 10:30 | MEM_QSL_20260419_103022 | OAuth module created
2026-04-20 09:15 | MEM_QSL_20260420_091500 | Content engine scaffold
2026-04-21 14:30 | MEM_QSL_20260421_143052 | LinkedIn skill integration ← CURRENT
```

---

### `state files`

List all files touched in a project.

**Usage:**
```
state files [project_name]
```

**What it returns:**
```
📁 FILES - QSL

linkedin-skill.md
├── Created in: MEM_QSL_20260421_143052
└── Modified in: MEM_QSL_20260421_150000

oauth_flow.py
├── Created in: MEM_QSL_20260419_103022
└── Modified in: MEM_QSL_20260421_143052, MEM_QSL_20260421_160000
```

---

### `state cross`

Show connections between projects.

**Usage:**
```
state cross [project_a] [project_b]
```

**What it returns:**
```
🔗 CROSS-PROJECT CONNECTIONS

QSL ↔ MedDash:
- linkedin-skill.md (used by both)
- content-engine (QSL builds, MedDash consumes)

Shared nodes: 3
```

---

## Artifacts Tracked

When you run `state checkpoint`, the skill automatically detects:

| Artifact Type | Detection Method |
|--------------|------------------|
| **Files created** | Scan `text_editor:write` calls |
| **Files modified** | Scan `text_editor:patch` calls |
| **Scripts run** | Scan `code_execution_tool` calls |
| **Chats** | Current chat session path |
| **Memories used** | Memory IDs referenced in conversation |
| **Skills loaded** | Skills referenced in conversation |

---

## Integration with A0 Memory

This skill **integrates with** A0's existing FAISS memory:

1. **Memory Save**: Uses `memory_save` to store node in FAISS
2. **Memory Load**: Uses `memory_load` to retrieve nodes
3. **Metadata Enhancement**: Adds files, scripts, connections as metadata

**Example A0 Memory Entry:**
```json
{
  "id": "MEM_QSL_20260421_143052",
  "text": "Working on LinkedIn skill integration...",
  "area": "QSL",
  "timestamp": "2026-04-21T14:30:52",
  "files": ["linkedin-skill.md", "oauth_flow.py"],
  "status": "active",
  "next_action": "Test OAuth flow"
}
```

---

## File Structure

```
Graph Memory/
├── connection_graph.json    ← Primary mosaic (shared by all agents)
├── artifact_index.json      ← File → Memory mappings
├── time_index.json          ← Chronological index
└── nodes/                   ← Individual node details (optional)
    ├── MEM_QSL_20260421_143052.json
    └── ...
```

---

## Ubiquitous Path Resolution

The skill finds Graph Memory in this order:

1. Environment variable: `A0_GRAPH_MEMORY_ROOT`
2. Project root: `<project_root>/Graph Memory/`
3. Workdir: `<workdir>/Graph Memory/`
4. A0 root: `/a0/usr/Graph Memory/`

If not found, it creates the directory structure automatically.

---

## Shared Across Agents

**All agents share the same connection_graph.json.**

When Agent 0 creates a node, subordinate agents can see it.
When a subordinate creates a node, Agent 0 can see it.

This creates a **unified memory mosaic** across the entire agent ecosystem.

---

## Workflow Example

```markdown
# Start of session
You: state where QSL
Agent: Shows current position, recent work, blockers

# Do work
You: Work on LinkedIn skill integration
Agent: Creates files, writes code...

# End of session
You: state checkpoint QSL
Agent: Creates memory node, updates graph, discovers connections

# Next session (days later)
You: state where QSL
Agent: Shows exactly where you left off, with full context
```

---

## See Also

- `memory_save` - A0's FAISS memory system
- `memory_load` - Retrieve memories by query
- `skills_tool` - Load other skills
