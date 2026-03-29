"""Anomaly detection for identifying unusual responses during testing."""
import re
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from collections import deque
import statistics

from app.models.target import Target
from app.models.plugin_run import PluginRun
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """Detect anomalous responses that might indicate security issues."""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        # Store recent responses for baseline calculation
        self.response_history: Dict[str, deque] = {}  # endpoint -> deque of metrics
        self.baseline_stats: Dict[str, Dict[str, float]] = {}  # endpoint -> stats
        
    def _extract_metrics(self, 
                        endpoint: str, 
                        status_code: int, 
                        response_length: int,
                        response_time: float,
                        headers: Dict[str, str],
                        body: str) -> Dict[str, float]:
        """Extract numerical metrics from a response for anomaly detection."""
        metrics = {
            'status_code': float(status_code),
            'response_length': float(response_length),
            'response_time': float(response_time),
            'header_count': float(len(headers)),
            'has_json': 1.0 if self._is_json_response(headers, body) else 0.0,
            'has_html': 1.0 if self._is_html_response(headers, body) else 0.0,
            'has_xml': 1.0 if self._is_xml_response(headers, body) else 0.0,
            'redirect': 1.0 if 300 <= status_code < 400 else 0.0,
            'client_error': 1.0 if 400 <= status_code < 500 else 0.0,
            'server_error': 1.0 if 500 <= status_code < 600 else 0.0,
            'success': 1.0 if 200 <= status_code < 300 else 0.0,
            'content_entropy': self._calculate_entropy(body),
            'special_char_ratio': self._calculate_special_char_ratio(body),
            'digit_ratio': self._calculate_digit_ratio(body),
        }
        return metrics
    
    def _is_json_response(self, headers: Dict[str, str], body: str) -> bool:
        """Check if response is JSON."""
        content_type = headers.get('content-type', '').lower()
        return 'application/json' in content_type or (
            body.strip().startswith('{') and body.strip().endswith('}') or
            body.strip().startswith('[') and body.strip().endswith(']')
        )
    
    def _is_html_response(self, headers: Dict[str, str], body: str) -> bool:
        """Check if response is HTML."""
        content_type = headers.get('content-type', '').lower()
        return 'text/html' in content_type or '<html' in body.lower()
    
    def _is_xml_response(self, headers: Dict[str, str], body: str) -> bool:
        """Check if response is XML."""
        content_type = headers.get('content-type', '').lower()
        return 'xml' in content_type or body.strip().startswith('<?xml')
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        # Count character frequencies
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        for count in freq.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        return entropy
    
    def _calculate_special_char_ratio(self, text: str) -> float:
        """Calculate ratio of special characters."""
        if not text:
            return 0.0
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        return special_chars / len(text)
    
    def _calculate_digit_ratio(self, text: str) -> float:
        """Calculate ratio of digits."""
        if not text:
            return 0.0
        digits = sum(1 for c in text if c.isdigit())
        return digits / len(text)
    
    def _update_baseline(self, endpoint: str, metrics: Dict[str, float]):
        """Update baseline statistics for an endpoint."""
        if endpoint not in self.response_history:
            self.response_history[endpoint] = deque(maxlen=self.window_size)
        
        self.response_history[endpoint].append(metrics)
        
        # Calculate baseline stats when we have enough samples
        if len(self.response_history[endpoint]) >= min(5, self.window_size // 2):
            history_list = list(self.response_history[endpoint])
            stats = {}
            
            # Calculate mean and std for each metric
            metric_names = history_list[0].keys() if history_list else []
            for metric in metric_names:
                values = [h[metric] for h in history_list]
                if len(values) >= 2:
                    try:
                        mean = statistics.mean(values)
                        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
                        stats[f'{metric}_mean'] = mean
                        stats[f'{metric}_stdev'] = max(stdev, 0.1)  # Avoid division by zero
                    except statistics.StatisticsError:
                        stats[f'{metric}_mean'] = statistics.mean(values) if values else 0.0
                        stats[f'{metric}_stdev'] = 0.1
            
            self.baseline_stats[endpoint] = stats
    
    def detect_anomaly(self, 
                      endpoint: str,
                      status_code: int,
                      response_length: int,
                      response_time: float,
                      headers: Dict[str, str],
                      body: str,
                      sensitivity: float = 2.0) -> Dict[str, Any]:
        """
        Detect if a response is anomalous compared to baseline.
        
        Args:
            endpoint: The endpoint URL
            status_code: HTTP status code
            response_length: Length of response body
            response_time: Response time in seconds
            headers: Response headers
            body: Response body
            sensitivity: How many standard deviations to consider anomalous (default 2.0)
            
        Returns:
            Dict with anomaly detection results
        """
        # Extract metrics from current response
        metrics = self._extract_metrics(endpoint, status_code, response_length, response_time, headers, body)
        
        # Update baseline with this sample
        self._update_baseline(endpoint, metrics)
        
        # If we don't have enough baseline data yet, return no anomaly
        if endpoint not in self.baseline_stats:
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'anomaly_score': 0.0,
                'reasons': ['Insufficient baseline data'],
                'metrics': metrics,
                'baseline_available': False
            }
        
        # Get baseline stats for this endpoint
        baseline = self.baseline_stats[endpoint]
        
        # Calculate anomaly score using z-score for each metric
        anomaly_scores = []
        reasons = []
        
        for metric_name, value in metrics.items():
            mean_key = f'{metric_name}_mean'
            stdev_key = f'{metric_name}_stdev'
            
            if mean_key in baseline and stdev_key in baseline:
                mean = baseline[mean_key]
                stdev = baseline[stdev_key]
                
                if stdev > 0:
                    z_score = abs((value - mean) / stdev)
                    anomaly_scores.append(z_score)
                    
                    # If this metric is significantly anomalous, add to reasons
                    if z_score > sensitivity:
                        reasons.append(
                            f"{metric_name}: {value:.2f} (baseline: {mean:.2f} ± {stdev:.2f}, z={z_score:.2f})"
                        )
        
        # Overall anomaly score is the max z-score
        overall_anomaly_score = max(anomaly_scores) if anomaly_scores else 0.0
        is_anomaly = overall_anomaly_score > sensitivity
        
        # Confidence based on how extreme the anomaly is and how much data we have
        baseline_size = len(self.response_history.get(endpoint, []))
        data_factor = min(1.0, baseline_size / self.window_size)
        anomaly_factor = min(1.0, overall_anomaly_score / (sensitivity * 2))  # Cap at 2x sensitivity
        confidence = min(0.95, 0.3 + (data_factor * 0.3) + (anomaly_factor * 0.4))
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': round(confidence, 2),
            'anomaly_score': round(overall_anomaly_score, 2),
            'sensitivity_used': sensitivity,
            'reasons': reasons,
            'metrics': metrics,
            'baseline_available': True,
            'baseline_size': baseline_size
        }
    
    def detect_anomaly_from_plugin_run(self, 
                                      plugin_run: PluginRun,
                                      sensitivity: float = 2.0) -> Dict[str, Any]:
        """
        Detect anomaly from a PluginRun object.
        
        Returns:
            Anomaly detection result
        """
        # Extract data from plugin run
        # target_id is actually the target's ID, but for anomaly detection we need a specific endpoint
        # For now, we'll use a placeholder - in practice this should be enhanced to track specific endpoints
        target_id = plugin_run.target_id or "unknown"
        endpoint = f"target_{target_id}"
        
        # Parse stdout/stderr to extract response info
        stdout = plugin_run.stdout or ""
        stderr = plugin_run.stderr or ""
        
        # Try to extract status code and response length from output
        status_code = 0
        response_length = 0
        response_time = 5.0  # Default assumption
        
        # Look for status code in output
        status_match = re.search(r'status.*?(\d{3})', stdout + stderr, re.IGNORECASE)
        if status_match:
            try:
                status_code = int(status_match.group(1))
            except ValueError:
                pass
        
        # Look for content-length or estimate from output
        length_match = re.search(r'length.*?(\d+)', stdout + stderr, re.IGNORECASE)
        if length_match:
            try:
                response_length = int(length_match.group(1))
            except ValueError:
                pass
        
        # For now, use placeholder headers and body
        headers = {}
        body = stdout + stderr
        
        return self.detect_anomaly(
            endpoint=endpoint,
            status_code=status_code,
            response_length=response_length,
            response_time=response_time,
            headers=headers,
            body=body,
            sensitivity=sensitivity
        )


# Global instance
anomaly_detector = AnomalyDetector()