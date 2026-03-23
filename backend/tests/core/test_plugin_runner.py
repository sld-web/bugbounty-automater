"""Tests for plugin isolation and security features."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.plugin_runner import (
    PluginRunner,
    PluginIsolationConfig,
    ResourceLimits,
)
from app.models.plugin_run import PermissionLevel


class TestIsolationConfig:
    """Tests for isolation configuration."""

    def test_safe_isolation_has_no_network(self):
        """SAFE plugins should have network disabled."""
        config = ResourceLimits.SAFE
        assert config.network_mode == "none"
        assert config.mem_limit == "256m"

    def test_limited_isolation_has_bridge_network(self):
        """LIMITED plugins should have bridge network."""
        config = ResourceLimits.LIMITED
        assert config.network_mode == "bridge"
        assert config.mem_limit == "512m"

    def test_dangerous_isolation_has_bridge_network(self):
        """DANGEROUS plugins should have bridge network."""
        config = ResourceLimits.DANGEROUS
        assert config.network_mode == "bridge"
        assert config.mem_limit == "1g"

    def test_all_configs_drop_all_capabilities(self):
        """All configs should drop all capabilities."""
        for config in [ResourceLimits.SAFE, ResourceLimits.LIMITED, ResourceLimits.DANGEROUS]:
            assert "ALL" in config.cap_drop
            assert "no-new-privileges" in config.security_opt

    def test_all_configs_are_read_only(self):
        """All configs should use read-only root filesystem."""
        for config in [ResourceLimits.SAFE, ResourceLimits.LIMITED, ResourceLimits.DANGEROUS]:
            assert config.read_only is True


class TestPluginRunner:
    """Tests for plugin runner functionality."""

    @pytest.fixture
    def runner(self):
        """Create plugin runner with mocked Docker."""
        with patch('app.core.plugin_runner.docker.DockerClient') as mock_client:
            mock_client.return_value.ping.return_value = True
            runner = PluginRunner()
            runner.docker_client = None
            return runner

    def test_get_isolation_config_safe(self, runner):
        """Test SAFE isolation config retrieval."""
        config = runner._get_isolation_config(PermissionLevel.SAFE)
        assert config.network_mode == "none"
        assert config.mem_limit == "256m"

    def test_get_isolation_config_limited(self, runner):
        """Test LIMITED isolation config retrieval."""
        config = runner._get_isolation_config(PermissionLevel.LIMITED)
        assert config.network_mode == "bridge"
        assert config.mem_limit == "512m"

    def test_get_isolation_config_dangerous(self, runner):
        """Test DANGEROUS isolation config retrieval."""
        config = runner._get_isolation_config(PermissionLevel.DANGEROUS)
        assert config.network_mode == "bridge"
        assert config.mem_limit == "1g"

    def test_get_isolation_config_invalid_string_defaults_to_safe(self, runner):
        """Invalid string permission level should default to SAFE."""
        config = runner._get_isolation_config("INVALID")
        assert config.network_mode == "none"

    def test_get_plugin_image_name(self, runner):
        """Test plugin image naming."""
        image = runner._get_plugin_image("subfinder")
        assert image == "bugbounty-subfinder:latest"

    def test_list_available_plugins_returns_list(self, runner):
        """Test plugin listing."""
        plugins = runner.list_available_plugins()
        assert isinstance(plugins, list)

    def test_parse_plugin_output_valid_json(self, runner):
        """Test parsing valid JSON output."""
        stdout = '{"subdomains": ["a.com", "b.com"]}'
        result = runner._parse_plugin_output(stdout)
        assert result["subdomains"] == ["a.com", "b.com"]

    def test_parse_plugin_output_invalid_json(self, runner):
        """Test parsing invalid JSON falls back to raw."""
        stdout = "Some text output\nwith multiple lines"
        result = runner._parse_plugin_output(stdout)
        assert "raw_output" in result

    def test_parse_plugin_output_empty(self, runner):
        """Test parsing empty output."""
        result = runner._parse_plugin_output("")
        assert "raw_output" in result


class TestPluginIsolationVerification:
    """Tests to verify isolation features are properly configured."""

    def test_safe_network_isolation(self):
        """Verify SAFE plugins cannot access network."""
        config = ResourceLimits.SAFE
        assert config.network_mode == "none"

    def test_safe_memory_limit(self):
        """Verify SAFE plugins have memory limits."""
        config = ResourceLimits.SAFE
        assert config.mem_limit == "256m"

    def test_safe_cpu_limit(self):
        """Verify SAFE plugins have CPU limits."""
        config = ResourceLimits.SAFE
        assert config.cpu_quota == 50000

    def test_limited_memory_limit(self):
        """Verify LIMITED plugins have appropriate memory."""
        config = ResourceLimits.LIMITED
        assert config.mem_limit == "512m"

    def test_limited_cpu_limit(self):
        """Verify LIMITED plugins have appropriate CPU."""
        config = ResourceLimits.LIMITED
        assert config.cpu_quota == 100000

    def test_dangerous_memory_limit(self):
        """Verify DANGEROUS plugins have higher memory for heavy tools."""
        config = ResourceLimits.DANGEROUS
        assert config.mem_limit == "1g"

    def test_dangerous_cpu_limit(self):
        """Verify DANGEROUS plugins have higher CPU quota."""
        config = ResourceLimits.DANGEROUS
        assert config.cpu_quota == 200000

    def test_timeout_configuration(self):
        """Verify timeout configurations are appropriate."""
        assert ResourceLimits.SAFE.timeout_seconds == 300
        assert ResourceLimits.LIMITED.timeout_seconds == 600
        assert ResourceLimits.DANGEROUS.timeout_seconds == 3600

    def test_capabilities_dropped(self):
        """Verify all capabilities are dropped for security."""
        for config in [ResourceLimits.SAFE, ResourceLimits.LIMITED, ResourceLimits.DANGEROUS]:
            assert config.cap_drop == ["ALL"]

    def test_no_new_privileges(self):
        """Verify no-new-privileges is set."""
        for config in [ResourceLimits.SAFE, ResourceLimits.LIMITED, ResourceLimits.DANGEROUS]:
            assert "no-new-privileges" in config.security_opt


class TestMockResults:
    """Tests for mock result generation."""

    @pytest.fixture
    def runner(self):
        """Create plugin runner."""
        with patch('app.core.plugin_runner.docker.DockerClient') as mock_client:
            mock_client.return_value.ping.return_value = True
            runner = PluginRunner()
            runner.docker_client = None
            return runner

    def test_mock_subfinder_results(self, runner):
        """Test mock results for subfinder."""
        results = runner._get_mock_results("subfinder", "example.com", {})
        assert "subdomains" in results
        assert len(results["subdomains"]) > 0
        assert results["status"] == "completed"

    def test_mock_nmap_results(self, runner):
        """Test mock results for nmap."""
        results = runner._get_mock_results("nmap", "192.168.1.1", {})
        assert "ports" in results
        assert results["status"] == "completed"

    def test_mock_httpx_results(self, runner):
        """Test mock results for httpx."""
        results = runner._get_mock_results("httpx", "example.com", {})
        assert "endpoints" in results
        assert results["status"] == "completed"

    def test_mock_nuclei_results(self, runner):
        """Test mock results for nuclei."""
        results = runner._get_mock_results("nuclei", "example.com", {})
        assert "findings" in results
        assert results["status"] == "completed"

    def test_mock_unknown_plugin(self, runner):
        """Test mock results for unknown plugin."""
        results = runner._get_mock_results("unknown_plugin", "example.com", {})
        assert "subdomains" in results
        assert results["status"] == "completed"
