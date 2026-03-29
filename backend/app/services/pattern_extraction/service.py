"""Service for extracting patterns from confirmed findings to improve future hypothesis generation."""
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from app.models.target import Target
from app.models.finding import Finding
from app.models.plugin_run import PluginRun
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PatternExtractionService:
    """Extract patterns from confirmed findings to improve future testing."""
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        
        # Pattern storage
        self.endpoint_patterns: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'success_rate': 0.0,
            'common_parameters': Counter(),
            'common_payloads': Counter(),
            'common_methods': Counter(),
            'last_seen': None
        })
        
        self.parameter_patterns: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'success_rate': 0.0,
            'common_values': Counter(),
            'common_payloads': Counter(),
            'last_seen': None
        })
        
        self.vulnerability_patterns: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'success_rate': 0.0,
            'common_endpoints': Counter(),
            'common_parameters': Counter(),
            'last_seen': None
        })
    
    def _is_recent(self, timestamp: datetime) -> bool:
        """Check if a timestamp is within the lookback period."""
        if not timestamp:
            return False
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        return timestamp >= cutoff
    
    def _extract_parameters_from_url(self, url: str) -> List[str]:
        """Extract parameter names from a URL."""
        # Simple extraction - in practice would use proper URL parsing
        params = []
        if '?' in url:
            query_part = url.split('?', 1)[1]
            for pair in query_part.split('&'):
                if '=' in pair:
                    param = pair.split('=')[0]
                    params.append(param)
        return params
    
    def _extract_payload_from_plugin_run(self, plugin_run: PluginRun) -> str:
        """Extract the payload used from a plugin run."""
        # Try to extract from stdout/stderr or params
        stdout = plugin_run.stdout or ""
        stderr = plugin_run.stderr or ""
        combined = stdout + stderr
        
        # Look for common payload patterns
        payload_patterns = [
            r'payload[:\s]+([^\s]+)',
            r'data[:\s]+([^\s]+)',
            r'--data[=\s]+([^\s]+)',
            r'-d[=\s]+([^\s]+)',
        ]
        
        for pattern in payload_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # If we have params, try to extract from there
        if plugin_run.params:
            # Look for common payload keys
            for key in ['data', 'payload', 'query', 'cmd', 'command']:
                if key in plugin_run.params:
                    return str(plugin_run.params[key])
        
        return ""
    
    def _extract_endpoint_from_plugin_run(self, plugin_run: PluginRun) -> str:
        """Extract endpoint from a plugin run."""
        # The target_id in plugin_run is actually the target ID, not endpoint
        # For now, we'll use a placeholder - in practice this should be enhanced
        # to store the specific endpoint tested
        return f"/endpoint/{plugin_run.target_id}"
    
    def add_confirmed_finding(self, finding: Finding) -> None:
        """
        Add a confirmed finding to the pattern database.
        
        Args:
            finding: A confirmed finding (status = CONFIRMED)
        """
        if finding.status != 'CONFIRMED':
            return
            
        if not self._is_recent(finding.created_at):
            return
        
        # Extract relevant information
        vuln_type = getattr(finding, 'vuln_type', '')
        endpoint = getattr(finding, 'affected_url', '') or getattr(finding, 'affected_parameter', '')
        parameter = getattr(finding, 'affected_parameter', '')
        
        # Update vulnerability patterns
        if vuln_type:
            self.vulnerability_patterns[vuln_type]['count'] += 1
            self.vulnerability_patterns[vuln_type]['last_seen'] = finding.created_at
            if endpoint:
                self.vulnerability_patterns[vuln_type]['common_endpoints'][endpoint] += 1
            if parameter:
                self.vulnerability_patterns[vuln_type]['common_parameters'][parameter] += 1
        
        # Update endpoint patterns
        if endpoint:
            self.endpoint_patterns[endpoint]['count'] += 1
            self.endpoint_patterns[endpoint]['last_seen'] = finding.created_at
            if parameter:
                self.endpoint_patterns[endpoint]['common_parameters'][parameter] += 1
            
            # Try to get payload from associated plugin runs (would need to query)
            # For now, we'll skip this as it requires joining with plugin_run table
        
        # Update parameter patterns
        if parameter:
            self.parameter_patterns[parameter]['count'] += 1
            self.parameter_patterns[parameter]['last_seen'] = finding.created_at
            if endpoint:
                self.parameter_patterns[parameter]['common_endpoints'][endpoint] += 1
            
            # Again, payload extraction would require plugin run data
    
    def add_confirmed_plugin_run(self, plugin_run: PluginRun) -> None:
        """
        Add a confirmed plugin run to the pattern database.
        
        Args:
            plugin_run: A confirmed plugin run (status = COMPLETED with successful output)
        """
        if plugin_run.status != 'COMPLETED':
            return
            
        # Check if the run was successful (simplified check)
        # In practice, we would analyze the output to determine if it found a vulnerability
        if not self._is_recent(plugin_run.created_at):
            return
        
        # Extract information from plugin run
        endpoint = f"/endpoint/{plugin_run.target_id}"  # Placeholder - in practice would be the specific endpoint tested
        payload = self._extract_payload_from_plugin_run(plugin_run)
        
        # Determine HTTP method from container_image or params (simplified)
        method = 'GET'  # Default
        container_image = plugin_run.container_image or ''
        if 'post' in container_image.lower():
            method = 'POST'
        elif 'put' in container_image.lower():
            method = 'PUT'
        elif 'delete' in container_image.lower():
            method = 'DELETE'
        
        # Update endpoint patterns
        if endpoint:
            self.endpoint_patterns[endpoint]['count'] += 1
            self.endpoint_patterns[endpoint]['last_seen'] = plugin_run.created_at
            self.endpoint_patterns[endpoint]['common_methods'][method] += 1
            if payload:
                self.endpoint_patterns[endpoint]['common_payloads'][payload] += 1
            
            # Extract parameters from endpoint (if it's a URL with query params)
            parameters = self._extract_parameters_from_url(endpoint)
            for param in parameters:
                self.endpoint_patterns[endpoint]['common_parameters'][param] += 1
        
        # Update parameter patterns (if we can extract them)
        if payload:
            # Try to extract common parameters from payload
            # This is simplified - in practice would parse the payload properly
            param_matches = re.findall(r'[&?]([^=]+)=', payload)
            for param in param_matches:
                self.parameter_patterns[param]['count'] += 1
                self.parameter_patterns[param]['last_seen'] = plugin_run.created_at
                self.parameter_patterns[param]['common_payloads'][payload] += 1
    
    def get_top_endpoints(self, limit: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        """Get the most productive endpoints based on confirmed findings."""
        sorted_endpoints = sorted(
            self.endpoint_patterns.items(),
            key=lambda x: x[1]['count'] * x[1]['success_rate'],
            reverse=True
        )
        return sorted_endpoints[:limit]
    
    def get_top_parameters(self, limit: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        """Get the most productive parameters based on confirmed findings."""
        sorted_parameters = sorted(
            self.parameter_patterns.items(),
            key=lambda x: x[1]['count'] * x[1]['success_rate'],
            reverse=True
        )
        return sorted_parameters[:limit]
    
    def get_top_vulnerability_types(self, limit: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        """Get the most productive vulnerability types based on confirmed findings."""
        sorted_types = sorted(
            self.vulnerability_patterns.items(),
            key=lambda x: x[1]['count'] * x[1]['success_rate'],
            reverse=True
        )
        return sorted_types[:limit]
    
    def get_hypothesis_suggestions(self, target: Target, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Generate hypothesis suggestions based on learned patterns.
        
        Args:
            target: The target to generate hypotheses for
            limit: Maximum number of suggestions to return
            
        Returns:
            List of hypothesis suggestions
        """
        suggestions = []
        
        # Get target's endpoints
        endpoints = getattr(target, 'endpoints', [])
        if not endpoints:
            return suggestions
        
        # For each endpoint, suggest hypotheses based on learned patterns
        for endpoint_data in endpoints:
            if isinstance(endpoint_data, dict):
                endpoint_url = endpoint_data.get('url', '') or endpoint_data.get('endpoint', '')
                method = endpoint_data.get('method', 'GET')
            else:
                endpoint_url = str(endpoint_data)
                method = 'GET'
            
            if not endpoint_url:
                continue
            
            # Look for similar endpoints in our patterns
            similar_endpoints = []
            for pattern_endpoint, pattern_data in self.endpoint_patterns.items():
                # Simple similarity check - in practice would use more sophisticated matching
                if endpoint_url in pattern_endpoint or pattern_endpoint in endpoint_url:
                    similar_endpoints.append((pattern_endpoint, pattern_data))
            
            # Sort by productivity
            similar_endpoints.sort(
                key=lambda x: x[1]['count'] * x[1]['success_rate'],
                reverse=True
            )
            
            # Generate hypotheses from top similar endpoints
            for pattern_endpoint, pattern_data in similar_endpoints[:3]:  # Top 3 similar
                # Suggest testing with successful parameters
                top_parameters = pattern_data['common_parameters'].most_common(3)
                for param, count in top_parameters:
                    if count >= 2:  # Only suggest if seen multiple times
                        suggestions.append({
                            'id': f"pattern_extract_param_{len(suggestions)}",
                            'description': f"Test parameter '{param}' based on {pattern_data['count']} confirmed successes",
                            'type': 'PATTERN_PARAMETER',
                            'endpoint': endpoint_url,
                            'method': method,
                            'payload': f"test_{param}",
                            'expected_behavior': f"Parameter '{param}' shows vulnerability pattern (seen {count} times in successful tests)"
                        })
                
                # Suggest testing with successful payloads
                top_payloads = pattern_data['common_payloads'].most_common(3)
                for payload, count in top_payloads:
                    if count >= 2:  # Only suggest if seen multiple times
                        suggestions.append({
                            'id': f"pattern_extract_payload_{len(suggestions)}",
                            'description': f"Test payload '{payload[:50]}...' based on {pattern_data['count']} confirmed successes",
                            'type': 'PATTERN_PAYLOAD',
                            'endpoint': endpoint_url,
                            'method': method,
                            'payload': payload,
                            'expected_behavior': f"Payload shows vulnerability pattern (seen {count} times in successful tests)"
                        })
        
        # Also suggest based on vulnerability types
        top_vuln_types = self.get_top_vulnerability_types(3)
        for vuln_type, vuln_data in top_vuln_types:
            if vuln_data['count'] >= 2:
                suggestions.append({
                    'id': f"pattern_vuln_type_{len(suggestions)}",
                    'description': f"Test for {vuln_type} based on {vuln_data['count']} confirmed successes",
                    'type': 'PATTERN_VULN_TYPE',
                    'endpoint': endpoints[0].get('url', '') if endpoints else '/test',
                    'method': 'GET',
                    'payload': f"test_{vuln_type}",
                    'expected_behavior': f"Vulnerability type '{vuln_type}' shows pattern (seen {vuln_data['count']} times)"
                })
        
        # Sort by potential value (count * success_rate) and limit
        suggestions.sort(
            key=lambda x: x.get('confidence', 0.5),  # We don't have confidence yet, so default
            reverse=True
        )
        
        return suggestions[:limit]
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about the learned patterns."""
        return {
            'endpoint_patterns_count': len(self.endpoint_patterns),
            'parameter_patterns_count': len(self.parameter_patterns),
            'vulnerability_patterns_count': len(self.vulnerability_patterns),
            'total_confirmed_endpoints': sum(p['count'] for p in self.endpoint_patterns.values()),
            'total_confirmed_parameters': sum(p['count'] for p in self.parameter_patterns.values()),
            'total_confirmed_vulnerabilities': sum(p['count'] for p in self.vulnerability_patterns.values())
        }


# Global instance
pattern_extraction_service = PatternExtractionService()