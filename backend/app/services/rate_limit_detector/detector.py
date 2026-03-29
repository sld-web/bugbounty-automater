"""Rate limit detection for identifying when targets are rate limiting requests."""
import time
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

from app.models.target import Target
from app.models.plugin_run import PluginRun
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitDetector:
    """Detect rate limiting patterns and recommend throttling strategies."""
    
    def __init__(self, window_size: int = 20, threshold: float = 0.3):
        """
        Initialize rate limit detector.
        
        Args:
            window_size: Number of recent requests to consider for detection
            threshold: Ratio of rate-limited requests to total requests to trigger alert
        """
        self.window_size = window_size
        self.threshold = threshold
        
        # Track request history per endpoint/target
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.rate_limit_status_codes = {429, 503, 504}  # Common rate limit codes
        self.retry_after_headers = ['retry-after', 'x-rate-limit-reset', 'ratelimit-reset']
        
    def _is_rate_limited(self, status_code: int, headers: Dict[str, str]) -> bool:
        """Check if a response indicates rate limiting."""
        # Check status code
        if status_code in self.rate_limit_status_codes:
            return True
            
        # Check for rate limit headers
        headers_lower = {k.lower(): v for k, v in headers.items()}
        for header in self.retry_after_headers:
            if header in headers_lower:
                return True
                
        # Check for rate limit messages in body (would need body parameter)
        # This would be enhanced in practice
        
        return False
    
    def _extract_retry_after(self, headers: Dict[str, str]) -> Optional[int]:
        """Extract retry-after value from headers in seconds."""
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # Check standard Retry-After header
        if 'retry-after' in headers_lower:
            try:
                value = headers_lower['retry-after']
                # Could be seconds or HTTP-date
                if value.isdigit():
                    return int(value)
                # For HTTP-date, we'd need to parse it - simplified for now
                return None
            except ValueError:
                pass
        
        # Check custom headers
        for header in ['x-rate-limit-reset', 'ratelimit-reset']:
            if header in headers_lower:
                try:
                    return int(headers_lower[header])
                except ValueError:
                    pass
                    
        return None
    
    def record_request(self, 
                      endpoint: str,
                      status_code: int,
                      headers: Dict[str, str],
                      response_time: float,
                      timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Record a request and check for rate limiting.
        
        Returns:
            Dict with rate limit detection results
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Record the request
        request_data = {
            'timestamp': timestamp,
            'status_code': status_code,
            'headers': dict(headers),
            'response_time': response_time,
            'is_rate_limited': self._is_rate_limited(status_code, headers),
            'retry_after': self._extract_retry_after(headers)
        }
        
        self.request_history[endpoint].append(request_data)
        
        # Analyze recent history
        history = list(self.request_history[endpoint])
        if not history:
            return {
                'is_rate_limited_now': False,
                'rate_limit_probability': 0.0,
                'recommendation': 'normal',
                'retry_after': None,
                'requests_in_window': 0
            }
        
        # Calculate rate limit probability
        total_requests = len(history)
        rate_limited_requests = sum(1 for req in history if req['is_rate_limited'])
        rate_limit_probability = rate_limited_requests / total_requests if total_requests > 0 else 0.0
        
        # Check if the most recent request was rate limited
        is_rate_limited_now = history[-1]['is_rate_limited'] if history else False
        
        # Get the most recent retry-after value
        retry_after = None
        for req in reversed(history):
            if req['retry_after'] is not None:
                retry_after = req['retry_after']
                break
        
        # Determine recommendation
        recommendation = 'normal'
        if rate_limit_probability >= self.threshold:
            if is_rate_limited_now:
                recommendation = 'stop_immediately'
            elif rate_limit_probability > 0.6:
                recommendation = 'slow_down_significantly'
            else:
                recommendation = 'slow_down'
        elif rate_limit_probability > 0.1:
            recommendation = 'proceed_with_caution'
        
        return {
            'is_rate_limited_now': is_rate_limited_now,
            'rate_limit_probability': round(rate_limit_probability, 3),
            'total_requests_in_window': total_requests,
            'rate_limited_requests_in_window': rate_limited_requests,
            'recommendation': recommendation,
            'retry_after': retry_after,
            'window_size': self.window_size,
            'threshold': self.threshold
        }
    
    def record_request_from_plugin_run(self, 
                                      plugin_run: PluginRun,
                                      endpoint: str,
                                      response_time: float = 5.0) -> Dict[str, Any]:
        """
        Record a request from a PluginRun object.
        
        Returns:
            Rate limit detection result
        """
        # Extract data from plugin run
        stdout = plugin_run.stdout or ""
        stderr = plugin_run.stderr or ""
        combined_output = stdout + stderr
        
        # Try to extract status code from output
        status_code = 200  # Default assumption
        import re
        status_match = re.search(r'status.*?(\d{3})', combined_output, re.IGNORECASE)
        if status_match:
            try:
                status_code = int(status_match.group(1))
            except ValueError:
                pass
        
        # Extract headers (simplified - in practice would parse from output)
        headers = {}
        # Look for common headers in output
        for header in ['content-type', 'server', 'date']:
            pattern = rf'{header}:\s*([^\n]+)'
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                headers[header] = match.group(1).strip()
        
        return self.record_request(
            endpoint=endpoint,
            status_code=status_code,
            headers=headers,
            response_time=response_time
        )


# Global instance
rate_limit_detector = RateLimitDetector()