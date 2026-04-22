#!/usr/bin/env python3
"""
Graph Memory Skill - Unified Memory Mosaic for Agent Zero

This skill creates a blockchain-like graph of memory nodes across all agents,
enabling spatial awareness of work progress, file connections, and project state.

Ubiquitous Design:
- Auto-detects Graph Memory location
- Works on any Agent Zero instance
- Creates directory structure on first use
- Integrates with A0's existing FAISS memory
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


class GraphMemory:
    """Manages the unified memory mosaic across all agents."""
    
    def __init__(self, project: str = "default"):
        """Initialize Graph Memory with ubiquitous path detection."""
        self.project = project
        self.root = self._find_or_create_root()
        self.connection_graph_path = self.root / "connection_graph.json"
        self.artifact_index_path = self.root / "artifact_index.json"
        self.time_index_path = self.root / "time_index.json"
        self.nodes_dir = self.root / "nodes"
        
        # Ensure all files exist
        self._ensure_structure()
        
    def _find_or_create_root(self) -> Path:
        """Find or create Graph Memory location - works on any A0 instance."""
        # Priority order for location detection
        locations = [
            # 1. Environment variable
            os.environ.get("A0_GRAPH_MEMORY_ROOT"),
            # 2. Project-relative
            os.environ.get("A0_PROJECT_ROOT"),
            # 3. Workdir-relative
            os.environ.get("A0_WORKDIR"),
            # 4. A0 root-relative (fallback)
            "/a0/usr",
        ]
        
        for base in locations:
            if base:
                path = Path(base) / "Graph Memory"
                if path.exists():
                    return path
        
        # Create at first available location
        for base in locations:
            if base:
                path = Path(base) / "Graph Memory"
                path.mkdir(parents=True, exist_ok=True)
                return path
        
        # Ultimate fallback
        path = Path("/a0/usr/Graph Memory")
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _ensure_structure(self):
        """Create all required files if they don't exist."""
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create connection_graph.json if missing
        if not self.connection_graph_path.exists():
            self._write_json(self.connection_graph_path, {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "projects": [],
                "nodes": {},
                "index": {
                    "by_project": {},
                    "by_artifact": {},
                    "by_time": []
                }
            })
        
        # Create artifact_index.json if missing
        if not self.artifact_index_path.exists():
            self._write_json(self.artifact_index_path, {
                "version": "1.0",
                "artifacts": {
                    "files": {},
                    "scripts": {},
                    "chats": {}
                }
            })
        
        # Create time_index.json if missing
        if not self.time_index_path.exists():
            self._write_json(self.time_index_path, {
                "version": "1.0",
                "timeline": []
            })
    
    def _read_json(self, path: Path) -> dict:
        """Read JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_json(self, path: Path, data: dict):
        """Write JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_node_id(self) -> str:
        """Generate unique memory node ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"MEM_{self.project}_{timestamp}"
    
    def checkpoint(self, 
                   summary: str,
                   artifacts: Dict[str, List[str]],
                   status: str = "active",
                   next_action: str = "",
                   blockers: List[str] = None,
                   connections: List[Dict] = None) -> Dict:
        """
        Create a memory node from current session.
        
        Args:
            summary: Description of work done
            artifacts: Dict with 'files', 'scripts', 'chats' keys
            status: 'active', 'paused', 'completed', or 'blocked'
            next_action: What to do next
            blockers: List of blocking issues
            connections: Discovered connections to other nodes
            
        Returns:
            Dict with node_id and status info
        """
        node_id = self._generate_node_id()
        timestamp = datetime.now().isoformat()
        
        if blockers is None:
            blockers = []
        if connections is None:
            connections = []
        
        # Load current graphs
        graph = self._read_json(self.connection_graph_path)
        artifacts_idx = self._read_json(self.artifact_index_path)
        time_idx = self._read_json(self.time_index_path)
        
        # Create node entry
        node = {
            "id": node_id,
            "timestamp": timestamp,
            "project": self.project,
            "summary": summary,
            "artifacts": artifacts,
            "status": status,
            "next_action": next_action,
            "blockers": blockers,
            "connections": connections
        }
        
        # Update connection graph
        graph["nodes"][node_id] = node
        graph["last_updated"] = timestamp
        
        # Add project to list if new
        if self.project not in graph["projects"]:
            graph["projects"].append(self.project)
        
        # Update indexes
        # By project
        if self.project not in graph["index"]["by_project"]:
            graph["index"]["by_project"][self.project] = []
        graph["index"]["by_project"][self.project].append(node_id)
        
        # By artifact
        for artifact_type in ["files", "scripts", "chats"]:
            for artifact_path in artifacts.get(artifact_type, []):
                if artifact_path not in graph["index"]["by_artifact"]:
                    graph["index"]["by_artifact"][artifact_path] = []
                graph["index"]["by_artifact"][artifact_path].append(node_id)
        
        # By time
        graph["index"]["by_time"].append(node_id)
        
        # Update artifact index
        for artifact_type in ["files", "scripts", "chats"]:
            for artifact_path in artifacts.get(artifact_type, []):
                if artifact_path not in artifacts_idx["artifacts"][artifact_type]:
                    artifacts_idx["artifacts"][artifact_type][artifact_path] = []
                artifacts_idx["artifacts"][artifact_type][artifact_path].append(node_id)
        
        # Update time index
        time_idx["timeline"].append({
            "node_id": node_id,
            "timestamp": timestamp,
            "project": self.project,
            "summary": summary
        })
        
        # Save all
        self._write_json(self.connection_graph_path, graph)
        self._write_json(self.artifact_index_path, artifacts_idx)
        self._write_json(self.time_index_path, time_idx)
        
        # Save individual node file
        node_path = self.nodes_dir / f"{node_id}.json"
        self._write_json(node_path, node)
        
        return {
            "node_id": node_id,
            "timestamp": timestamp,
            "artifacts_count": sum(len(v) for v in artifacts.values()),
            "connections_count": len(connections)
        }
    
    def where(self) -> Dict:
        """
        Get current position in project.
        
        Returns:
            Dict with latest node, status, and context
        """
        graph = self._read_json(self.connection_graph_path)
        time_idx = self._read_json(self.time_index_path)
        
        # Get latest node for this project
        project_nodes = graph["index"]["by_project"].get(self.project, [])
        
        if not project_nodes:
            return {
                "found": False,
                "project": self.project,
                "message": f"No checkpoints found for project '{self.project}'"
            }
        
        latest_node_id = project_nodes[-1]
        node = graph["nodes"].get(latest_node_id)
        
        if not node:
            return {
                "found": False,
                "project": self.project,
                "message": f"Node {latest_node_id} not found"
            }
        
        # Get recent timeline
        recent = time_idx["timeline"][-5:] if len(time_idx["timeline"]) >= 5 else time_idx["timeline"]
        
        return {
            "found": True,
            "project": self.project,
            "node_id": latest_node_id,
            "timestamp": node.get("timestamp"),
            "summary": node.get("summary"),
            "status": node.get("status"),
            "next_action": node.get("next_action"),
            "blockers": node.get("blockers", []),
            "artifacts": node.get("artifacts", {}),
            "connections": node.get("connections", []),
            "recent_timeline": recent
        }
    
    def timeline(self, limit: int = 10) -> List[Dict]:
        """Get chronological timeline for project."""
        time_idx = self._read_json(self.time_index_path)
        
        # Filter by project
        project_timeline = [
            entry for entry in time_idx["timeline"]
            if entry.get("project") == self.project
        ]
        
        return project_timeline[-limit:] if limit else project_timeline
    
    def files(self) -> Dict[str, List[Dict]]:
        """Get all files touched in project."""
        graph = self._read_json(self.connection_graph_path)
        artifacts_idx = self._read_json(self.artifact_index_path)
        
        result = {}
        
        for file_path, node_ids in artifacts_idx["artifacts"]["files"].items():
            # Check if any node is from this project
            project_nodes = [
                nid for nid in node_ids 
                if nid.startswith(f"MEM_{self.project}_")
            ]
            if project_nodes:
                result[file_path] = [
                    {
                        "node_id": nid,
                        "summary": graph["nodes"].get(nid, {}).get("summary", "")
                    }
                    for nid in project_nodes
                ]
        
        return result
    
    def map(self) -> Dict:
        """Get full connection graph for project."""
        graph = self._read_json(self.connection_graph_path)
        
        # Get all nodes for this project
        project_nodes = {
            nid: node for nid, node in graph["nodes"].items()
            if node.get("project") == self.project
        }
        
        return {
            "project": self.project,
            "nodes": project_nodes,
            "node_count": len(project_nodes),
            "projects": graph.get("projects", [])
        }
    
    def cross_project(self, other_project: str) -> Dict:
        """Find connections between this project and another."""
        graph = self._read_json(self.connection_graph_path)
        artifacts_idx = self._read_json(self.artifact_index_path)
        
        # Find shared artifacts
        shared_files = []
        
        for file_path, node_ids in artifacts_idx["artifacts"]["files"].items():
            this_project_nodes = [
                nid for nid in node_ids 
                if nid.startswith(f"MEM_{self.project}_")
            ]
            other_project_nodes = [
                nid for nid in node_ids 
                if nid.startswith(f"MEM_{other_project}_")
            ]
            
            if this_project_nodes and other_project_nodes:
                shared_files.append({
                    "file": file_path,
                    "this_project": this_project_nodes,
                    "other_project": other_project_nodes
                })
        
        return {
            "project_a": self.project,
            "project_b": other_project,
            "shared_files": shared_files,
            "shared_count": len(shared_files)
        }
    
    def add_connection(self, 
                       node_a: str, 
                       relation: str, 
                       node_b: str) -> Dict:
        """Manually add a connection between two nodes."""
        graph = self._read_json(self.connection_graph_path)
        
        if node_a not in graph["nodes"]:
            return {"success": False, "error": f"Node {node_a} not found"}
        if node_b not in graph["nodes"]:
            return {"success": False, "error": f"Node {node_b} not found"}
        
        # Add connection to node_a
        if "connections" not in graph["nodes"][node_a]:
            graph["nodes"][node_a]["connections"] = []
        
        graph["nodes"][node_a]["connections"].append({
            "to": node_b,
            "relation": relation
        })
        
        self._write_json(self.connection_graph_path, graph)
        
        return {
            "success": True,
            "node_a": node_a,
            "relation": relation,
            "node_b": node_b
        }


def format_where_output(data: Dict) -> str:
    """Format 'state where' output for display."""
    if not data.get("found"):
        return f"📍 No checkpoints found for project '{data.get('project', 'unknown')}'"
    
    status_emoji = {
        "active": "🟢",
        "paused": "🟡",
        "completed": "✅",
        "blocked": "🔴"
    }
    
    emoji = status_emoji.get(data.get("status", "active"), "🟢")
    
    output = f"""📍 WHERE AM I?

Project: {data.get('project', 'Unknown')}
Latest Node: {data.get('node_id', 'N/A')}
Timestamp: {data.get('timestamp', 'N/A')}

## Current Work
{data.get('summary', 'No summary available')}

## Status
{emoji} {data.get('status', 'active').title()}

## Files Involved
"""
    
    files = data.get("artifacts", {}).get("files", [])
    if files:
        for f in files:
            output += f"- {f}\n"
    else:
        output += "None\n"
    
    output += f"\n## Next Action\n{data.get('next_action', 'None specified')}\n"
    
    blockers = data.get("blockers", [])
    if blockers:
        output += f"\n## Blockers\n"
        for b in blockers:
            output += f"- {b}\n"
    else:
        output += "\n## Blockers\nNone\n"
    
    connections = data.get("connections", [])
    if connections:
        output += f"\n## Connections\n"
        for c in connections:
            output += f"├── {c.get('relation', 'related to')}: {c.get('to', 'unknown')}\n"
    
    recent = data.get("recent_timeline", [])
    if recent:
        output += f"\n## Recent Timeline\n"
        for i, entry in enumerate(reversed(recent)):
            marker = " ← CURRENT" if entry.get("node_id") == data.get("node_id") else ""
            output += f"{i+1}. {entry.get('timestamp', 'N/A')[:16]} | {entry.get('summary', 'N/A')[:50]}{marker}\n"
    
    return output


def format_checkpoint_output(data: Dict) -> str:
    """Format 'state checkpoint' output for display."""
    return f"""✅ Checkpoint saved: {data.get('node_id', 'Unknown')}
- Timestamp: {data.get('timestamp', 'N/A')}
- Artifacts tracked: {data.get('artifacts_count', 0)}
- Connections found: {data.get('connections_count', 0)}
"""


def format_timeline_output(timeline: List[Dict]) -> str:
    """Format 'state timeline' output for display."""
    if not timeline:
        return "📅 No timeline entries found"
    
    output = "📅 TIMELINE\n\n"
    for entry in reversed(timeline):
        ts = entry.get("timestamp", "N/A")[:16]
        summary = entry.get("summary", "No summary")[:60]
        node_id = entry.get("node_id", "N/A")
        output += f"{ts} | {node_id} | {summary}\n"
    
    return output


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python graph_memory.py <command> <project> [args...]")
        print("Commands: checkpoint, where, timeline, files, map, cross")
        sys.exit(1)
    
    command = sys.argv[1]
    project = sys.argv[2]
    
    gm = GraphMemory(project)
    
    if command == "where":
        result = gm.where()
        print(format_where_output(result))
    
    elif command == "timeline":
        result = gm.timeline()
        print(format_timeline_output(result))
    
    elif command == "map":
        result = gm.map()
        print(json.dumps(result, indent=2))
    
    elif command == "files":
        result = gm.files()
        print(json.dumps(result, indent=2))
    
    elif command == "cross":
        if len(sys.argv) < 4:
            print("Usage: python graph_memory.py cross <project> <other_project>")
            sys.exit(1)
        other = sys.argv[3]
        result = gm.cross_project(other)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
