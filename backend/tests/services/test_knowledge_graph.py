"""Tests for Knowledge Graph service."""
import pytest
import sys
sys.path.insert(0, '/home/xtx/Desktop/bugbounty-automater/backend')

from app.services.knowledge_graph import (
    KnowledgeGraph,
    ProgramKnowledgeBuilder,
    NodeType,
    EdgeType,
)


class TestKnowledgeGraph:
    """Test suite for KnowledgeGraph."""

    def setup_method(self):
        """Set up test fixtures."""
        self.graph = KnowledgeGraph()

    def test_add_node(self):
        """Test adding a node to the graph."""
        node = self.graph.add_node(
            node_id="test_domain",
            node_type=NodeType.DOMAIN.value,
            properties={"domain": "example.com"}
        )

        assert node["id"] == "test_domain"
        assert node["type"] == NodeType.DOMAIN.value
        assert node["properties"]["domain"] == "example.com"
        assert node["tested"] == False

    def test_add_duplicate_node_updates_properties(self):
        """Test that adding a node with existing ID updates properties."""
        self.graph.add_node("test", NodeType.DOMAIN.value, {"key": "value1"})
        self.graph.add_node("test", NodeType.DOMAIN.value, {"key": "value2", "new": "data"})

        node = self.graph.get_node("test")
        assert node["properties"]["key"] == "value2"
        assert node["properties"]["new"] == "data"

    def test_add_edge(self):
        """Test adding an edge between nodes."""
        self.graph.add_node("node1", NodeType.DOMAIN.value, {})
        self.graph.add_node("node2", NodeType.IP.value, {})

        edge = self.graph.add_edge("node1", "node2", EdgeType.HAS.value)

        assert edge["source"] == "node1"
        assert edge["target"] == "node2"
        assert edge["type"] == EdgeType.HAS.value

    def test_add_edge_missing_source_node(self):
        """Test adding edge with missing source returns empty."""
        self.graph.add_node("target", NodeType.DOMAIN.value, {})
        edge = self.graph.add_edge("missing", "target", EdgeType.HAS.value)
        assert edge == {}

    def test_get_neighbors(self):
        """Test getting neighboring nodes."""
        self.graph.add_node("domain", NodeType.DOMAIN.value, {})
        self.graph.add_node("ip1", NodeType.IP.value, {})
        self.graph.add_node("ip2", NodeType.IP.value, {})

        self.graph.add_edge("domain", "ip1", EdgeType.HAS.value)
        self.graph.add_edge("domain", "ip2", EdgeType.HAS.value)

        neighbors = self.graph.get_neighbors("domain")
        assert len(neighbors) == 2

    def test_get_neighbors_with_edge_type_filter(self):
        """Test filtering neighbors by edge type."""
        self.graph.add_node("node1", NodeType.DOMAIN.value, {})
        self.graph.add_node("node2", NodeType.SERVICE.value, {})

        self.graph.add_edge("node1", "node2", EdgeType.USES.value)

        all_neighbors = self.graph.get_neighbors("node1")
        filtered_neighbors = self.graph.get_neighbors("node1", EdgeType.USES.value)

        assert len(all_neighbors) == 1
        assert filtered_neighbors[0]["edge_type"] == EdgeType.USES.value

    def test_mark_tested(self):
        """Test marking a node as tested."""
        self.graph.add_node("test", NodeType.DOMAIN.value, {})
        assert self.graph.get_node("test")["tested"] == False

        self.graph.mark_tested("test")
        assert self.graph.get_node("test")["tested"] == True

    def test_add_finding(self):
        """Test adding a finding to a node."""
        self.graph.add_node("test", NodeType.DOMAIN.value, {})

        finding = {
            "name": "SQL Injection",
            "severity": "high",
            "location": "/api/users"
        }

        self.graph.add_finding("test", finding)
        node = self.graph.get_node("test")

        assert len(node["findings"]) == 1
        assert node["findings"][0]["name"] == "SQL Injection"
        assert node["risk_level"] == "high"

    def test_find_paths(self):
        """Test finding paths between nodes."""
        self.graph.add_node("a", NodeType.DOMAIN.value, {})
        self.graph.add_node("b", NodeType.SERVICE.value, {})
        self.graph.add_node("c", NodeType.ENDPOINT.value, {})
        self.graph.add_node("d", NodeType.IP.value, {})

        self.graph.add_edge("a", "b", EdgeType.HAS.value)
        self.graph.add_edge("b", "c", EdgeType.HAS.value)
        self.graph.add_edge("c", "d", EdgeType.HAS.value)

        paths = self.graph.find_paths("a", "d")
        assert len(paths) >= 1
        assert "a" in paths[0]
        assert "d" in paths[0]

    def test_find_attack_chains(self):
        """Test finding attack chains."""
        self.graph.add_node("sqli", NodeType.VULNERABILITY.value, {"type": "sql_injection"})
        self.graph.add_node("upload", NodeType.VULNERABILITY.value, {"type": "file_upload"})
        self.graph.add_node("rce", NodeType.VULNERABILITY.value, {"type": "rce"})

        self.graph.add_edge("sqli", "upload", EdgeType.CHAINABLE_TO.value)
        self.graph.add_edge("upload", "rce", EdgeType.CHAINABLE_TO.value)

        chains = self.graph.find_attack_chains("sqli")
        assert len(chains) > 0

    def test_get_attack_surface(self):
        """Test getting complete attack surface."""
        self.graph.add_node("d1", NodeType.DOMAIN.value, {})
        self.graph.add_node("d2", NodeType.DOMAIN.value, {})
        self.graph.add_node("ip1", NodeType.IP.value, {})
        self.graph.add_node("vuln1", NodeType.VULNERABILITY.value, {})

        self.graph.add_node("vuln1", NodeType.VULNERABILITY.value, {})
        self.graph.add_finding("vuln1", {"name": "XSS", "severity": "medium"})

        surface = self.graph.get_attack_surface()

        assert surface["stats"]["total_nodes"] == 4
        assert surface["stats"]["by_type"]["domain"] == 2
        assert surface["stats"]["with_findings"] == 1

    def test_export_import_json(self):
        """Test exporting and importing graph as JSON."""
        self.graph.add_node("test", NodeType.DOMAIN.value, {"domain": "test.com"})
        self.graph.add_edge("test", "test", EdgeType.HAS.value)

        exported = self.graph.export_json()
        assert "test" in exported
        assert "domain" in exported

        new_graph = KnowledgeGraph()
        new_graph.import_json(exported)
        assert new_graph.get_node("test") is not None


class TestProgramKnowledgeBuilder:
    """Test suite for ProgramKnowledgeBuilder."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = ProgramKnowledgeBuilder()

    def test_create_graph(self):
        """Test creating a new program graph."""
        graph = self.builder.create_graph("prog1", "Test Program")

        assert graph is not None
        assert "prog1" in graph.programs

    def test_get_graph(self):
        """Test getting a program graph."""
        self.builder.create_graph("prog1", "Test")
        graph = self.builder.get_graph("prog1")

        assert graph is not None

    def test_get_nonexistent_graph(self):
        """Test getting a nonexistent graph returns None."""
        graph = self.builder.get_graph("nonexistent")
        assert graph is None

    def test_build_from_analysis(self):
        """Test building graph from program analysis."""
        analysis = {
            "name": "Test Program",
            "targets": [
                {
                    "name": "Main App",
                    "type": "webapp",
                    "scope_domains": ["example.com", "api.example.com"],
                    "scope_ips": ["192.168.1.1"]
                }
            ],
            "rules": ["No DoS testing"]
        }

        graph = self.builder.build_from_analysis("prog1", analysis)

        assert graph.get_node("target:Main App") is not None
        assert graph.get_node("domain:example.com") is not None
        assert graph.get_node("domain:api.example.com") is not None
        assert graph.get_node("ip:192.168.1.1") is not None

    def test_build_from_analysis_empty_targets(self):
        """Test building graph with no targets."""
        analysis = {
            "name": "Empty Program",
            "targets": []
        }

        graph = self.builder.build_from_analysis("prog1", analysis)
        assert len(graph.nodes) == 0

    def test_add_finding_to_graph(self):
        """Test adding finding to program graph."""
        self.builder.create_graph("prog1", "Test")
        graph = self.builder.get_graph("prog1")
        graph.add_node("domain:test", NodeType.DOMAIN.value, {})

        finding = {
            "name": "SQL Injection",
            "severity": "critical"
        }

        self.builder.add_finding_to_graph("prog1", "domain:test", finding)

        node = graph.get_node("domain:test")
        assert len(node["findings"]) == 1


class TestNodeAndEdgeTypes:
    """Test NodeType and EdgeType enums."""

    def test_node_types(self):
        """Test all node types are defined."""
        expected_types = [
            "domain", "ip", "endpoint", "service", "auth_method",
            "vulnerability", "file", "certificate", "technology",
            "user", "credential"
        ]

        for et in expected_types:
            assert hasattr(NodeType, et.upper())

    def test_edge_types(self):
        """Test all edge types are defined."""
        expected_edges = [
            "has", "uses", "depends_on", "vulnerable_to", "leads_to",
            "connects_to", "authenticates_to", "uploads_to", "reads_from",
            "chainable_to"
        ]

        for et in expected_edges:
            assert hasattr(EdgeType, et.upper())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
