"""Knowledge Graph Builder for target mapping and relationship tracking."""
import json
import logging
from datetime import datetime
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    DOMAIN = "domain"
    IP = "ip"
    ENDPOINT = "endpoint"
    SERVICE = "service"
    AUTH_METHOD = "auth_method"
    VULNERABILITY = "vulnerability"
    FILE = "file"
    CERTIFICATE = "certificate"
    TECHNOLOGY = "technology"
    USER = "user"
    CREDENTIAL = "credential"


class EdgeType(str, Enum):
    HAS = "has"
    USES = "uses"
    DEPENDS_ON = "depends_on"
    VULNERABLE_TO = "vulnerable_to"
    LEADS_TO = "leads_to"
    CONNECTS_TO = "connects_to"
    AUTHENTICATES_TO = "authenticates_to"
    UPLOADS_TO = "uploads_to"
    READS_FROM = "reads_from"
    CHAINABLE_TO = "chainable_to"


class KnowledgeGraph:
    """In-memory knowledge graph for tracking attack surface."""

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self.programs: dict[str, dict] = {}

    def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: dict[str, Any]
    ) -> dict:
        """Add a node to the graph."""
        if node_id in self.nodes:
            self.nodes[node_id]["properties"].update(properties)
        else:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "properties": properties,
                "created_at": datetime.utcnow().isoformat(),
                "tags": [],
                "risk_level": "unknown",
                "tested": False,
                "findings": []
            }
        return self.nodes[node_id]

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: dict[str, Any] | None = None
    ) -> dict:
        """Add an edge between nodes."""
        if source_id not in self.nodes:
            logger.warning(f"Source node {source_id} not found")
            return {}
        if target_id not in self.nodes:
            logger.warning(f"Target node {target_id} not found")
            return {}

        edge = {
            "source": source_id,
            "target": target_id,
            "type": edge_type,
            "properties": properties or {},
            "created_at": datetime.utcnow().isoformat()
        }

        self.edges.append(edge)
        return edge

    def get_node(self, node_id: str) -> dict | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(
        self,
        node_id: str,
        edge_type: str | None = None
    ) -> list[dict]:
        """Get neighboring nodes."""
        neighbors = []
        for edge in self.edges:
            if edge["source"] == node_id:
                neighbor = self.get_node(edge["target"])
                if neighbor and (edge_type is None or edge["type"] == edge_type):
                    neighbors.append({
                        "node": neighbor,
                        "edge_type": edge["type"],
                        "properties": edge.get("properties", {})
                    })
            elif edge["target"] == node_id:
                neighbor = self.get_node(edge["source"])
                if neighbor and (edge_type is None or edge["type"] == edge_type):
                    neighbors.append({
                        "node": neighbor,
                        "edge_type": edge["type"],
                        "direction": "incoming",
                        "properties": edge.get("properties", {})
                    })
        return neighbors

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> list[list[str]]:
        """Find all paths between two nodes."""
        paths = []
        
        def dfs(current: str, target: str, path: list[str], visited: set[str]):
            if len(path) > max_depth:
                return
            if current == target:
                paths.append(path.copy())
                return
            if current in visited:
                return
            
            visited.add(current)
            for edge in self.edges:
                if edge["source"] == current:
                    dfs(edge["target"], target, path + [edge["target"]], visited.copy())
                elif edge["target"] == current:
                    dfs(edge["source"], target, path + [edge["source"]], visited.copy())
        
        dfs(source_id, target_id, [source_id], set())
        return paths

    def find_attack_chains(self, start_node_id: str) -> list[dict]:
        """Find potential attack chains starting from a node."""
        chains = []
        
        def explore(node_id: str, chain: list[dict], visited: set[str]):
            if node_id in visited:
                return
            if len(chain) > 10:
                return
            
            visited.add(node_id)
            node = self.get_node(node_id)
            if not node:
                return
            
            chain.append({
                "node": node,
                "step": len(chain) + 1
            })
            
            for edge in self.edges:
                if edge["source"] == node_id:
                    next_node = self.get_node(edge["target"])
                    if next_node:
                        explore(
                            edge["target"],
                            chain.copy(),
                            visited.copy()
                        )
                elif edge["target"] == node_id and edge["type"] == EdgeType.CHAINABLE_TO.value:
                    next_node = self.get_node(edge["source"])
                    if next_node:
                        explore(
                            edge["source"],
                            chain.copy(),
                            visited.copy()
                        )
            
            if len(chain) > 1:
                chains.append({
                    "nodes": chain,
                    "length": len(chain),
                    "endpoints": [n["node"]["id"] for n in chain],
                    "technologies": list(set(
                        n["node"].get("properties", {}).get("technology", [])
                        for n in chain
                        if n["node"].get("properties", {}).get("technology")
                    ))
                })
        
        explore(start_node_id, [], set())
        return chains

    def mark_tested(self, node_id: str) -> None:
        """Mark a node as tested."""
        if node_id in self.nodes:
            self.nodes[node_id]["tested"] = True

    def add_finding(
        self,
        node_id: str,
        finding: dict
    ) -> None:
        """Add a finding to a node."""
        if node_id in self.nodes:
            if "findings" not in self.nodes[node_id]:
                self.nodes[node_id]["findings"] = []
            self.nodes[node_id]["findings"].append({
                **finding,
                "added_at": datetime.utcnow().isoformat()
            })
            self.nodes[node_id]["risk_level"] = finding.get("severity", "unknown")

    def get_attack_surface(self) -> dict:
        """Get the complete attack surface."""
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "stats": {
                "total_nodes": len(self.nodes),
                "by_type": self._count_by_type(),
                "by_risk": self._count_by_risk(),
                "tested": sum(1 for n in self.nodes.values() if n.get("tested")),
                "with_findings": sum(1 for n in self.nodes.values() if n.get("findings"))
            }
        }

    def _count_by_type(self) -> dict[str, int]:
        counts = {}
        for node in self.nodes.values():
            node_type = node.get("type", "unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def _count_by_risk(self) -> dict[str, int]:
        counts = {}
        for node in self.nodes.values():
            risk = node.get("risk_level", "unknown")
            counts[risk] = counts.get(risk, 0) + 1
        return counts

    def export_json(self) -> str:
        """Export graph as JSON."""
        return json.dumps({
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "programs": self.programs
        }, indent=2)

    def import_json(self, data: str) -> None:
        """Import graph from JSON."""
        try:
            parsed = json.loads(data)
            self.nodes = {n["id"]: n for n in parsed.get("nodes", [])}
            self.edges = parsed.get("edges", [])
            self.programs = parsed.get("programs", {})
        except Exception as e:
            logger.error(f"Failed to import graph: {e}")


class ProgramKnowledgeBuilder:
    """Build knowledge graphs for bug bounty programs."""

    def __init__(self):
        self.graphs: dict[str, KnowledgeGraph] = {}

    def create_graph(self, program_id: str, program_name: str) -> KnowledgeGraph:
        """Create a new knowledge graph for a program."""
        graph = KnowledgeGraph()
        graph.programs[program_id] = {
            "name": program_name,
            "created_at": datetime.utcnow().isoformat()
        }
        self.graphs[program_id] = graph
        return graph

    def get_graph(self, program_id: str) -> KnowledgeGraph | None:
        """Get the knowledge graph for a program."""
        return self.graphs.get(program_id)

    def build_from_analysis(
        self,
        program_id: str,
        analysis_data: dict
    ) -> KnowledgeGraph:
        """Build a knowledge graph from program analysis data."""
        graph = self.get_graph(program_id)
        if not graph:
            graph = self.create_graph(program_id, analysis_data.get("name", "Unknown"))

        targets = analysis_data.get("targets", [])
        
        for target in targets:
            target_id = f"target:{target.get('name', 'unknown')}"
            
            graph.add_node(
                node_id=target_id,
                node_type=NodeType.DOMAIN,
                properties={
                    "name": target.get("name"),
                    "type": target.get("type"),
                    "description": target.get("description"),
                    "domains": target.get("scope_domains", []),
                    "ips": target.get("scope_ips", [])
                }
            )

            for domain in target.get("scope_domains", []):
                domain_id = f"domain:{domain}"
                graph.add_node(
                    node_id=domain_id,
                    node_type=NodeType.DOMAIN,
                    properties={"domain": domain}
                )
                graph.add_edge(
                    source_id=target_id,
                    target_id=domain_id,
                    edge_type=EdgeType.HAS
                )

            for ip in target.get("scope_ips", []):
                ip_id = f"ip:{ip}"
                graph.add_node(
                    node_id=ip_id,
                    node_type=NodeType.IP,
                    properties={"ip": ip}
                )
                graph.add_edge(
                    source_id=target_id,
                    target_id=ip_id,
                    edge_type=EdgeType.HAS
                )

        for rule in analysis_data.get("rules", []):
            rule_id = f"rule:{hash(rule)}"
            graph.add_node(
                node_id=rule_id,
                node_type=NodeType.SERVICE,
                properties={
                    "rule": rule,
                    "type": "constraint"
                }
            )

        return graph

    def add_finding_to_graph(
        self,
        program_id: str,
        node_id: str,
        finding: dict
    ) -> None:
        """Add a finding to the program's graph."""
        graph = self.get_graph(program_id)
        if graph:
            graph.add_finding(node_id, finding)

            finding_node_id = f"finding:{hash(str(finding))}"
            graph.add_node(
                node_id=finding_node_id,
                node_type=NodeType.VULNERABILITY,
                properties=finding
            )
            graph.add_edge(
                source_id=node_id,
                target_id=finding_node_id,
                edge_type=EdgeType.VULNERABLE_TO
            )


knowledge_builder = ProgramKnowledgeBuilder()
