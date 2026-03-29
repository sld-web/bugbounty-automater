"""Endpoint classifier for categorizing discovered endpoints."""
import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs

from app.models.target import Target
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EndpointClassifier:
    """Classify endpoints based on URL patterns, parameters, and response characteristics."""

    # Patterns for different endpoint types
    AUTHENTICATED_PATTERNS = [
        r'/api/v\d+/auth',
        r'/login',
        r'/auth',
        r'/signin',
        r'/oauth',
        r'/sso',
        r'/session',
        r'/token',
        r'/jwt',
        r'/api/v\d+/users?/me',
        r'/api/v\d+/profile',
        r'/api/v\d+/account',
        r'/api/v\d+/settings',
        r'/api/v\d+/preferences',
        r'/admin',
        r'/administrator',
        r'/wp-admin',
        r'/phpmyadmin',
        r'/webadmin',
        r'/manage',
        r'/control',
        r'/dashboard',
        r'/cp/',
        r'/cpanel',
    ]

    API_PATTERNS = [
        r'/api/v\d+',
        r'/rest/',
        r'/graphql',
        r'/soap',
        r'/ws/',
        r'/service/',
        r'/rpc',
        r'/json',
        r'/xml',
        r'/ajax',
        r'\.json$',
        r'\.xml$',
        r'\.api$',
    ]

    MOBILE_PATTERNS = [
        r'/mobile/',
        r'/m/',
        r'/app/',
        r'/ios/',
        r'/android/',
        r'/api/v\d+/mobile',
        r'/api/v\d+/apps?',
        r'/endpoint',
        r'/push',
        r'/notify',
        r'/sync',
    ]

    ADMIN_PATTERNS = [
        r'/admin',
        r'/administrator',
        r'/manage',
        r'/manage/',
        r'/control',
        r'/panel',
        r'/cpanel',
        r'/plesk',
        r'/webmin',
        r'/wp-admin',
        r'/wp-json/wp/v2/users',
        r'/dashboard',
        r'/backend',
        r'/console',
        r'/superuser',
        r'/root',
        r'/sysadmin',
        r'/network-admin',
        r'/site-admin',
    ]

    PUBLIC_PATTERNS = [
        r'/public',
        r'/static',
        r'/assets',
        r'/css',
        r'/js',
        r'/images?',
        r'/img',
        r'/fonts?',
        r'/media',
        r'/upload',
        r'/download',
        r'/feed',
        r'/rss',
        r'/sitemap',
        r'/robots\.txt',
        r'/humans\.txt',
        r'/crossdomain\.xml',
        r'/clientaccesspolicy\.xml',
    ]

    SENSITIVE_PARAMETERS = [
        'token',
        'auth',
        'session',
        'sid',
        'id',
        'user_id',
        'uid',
        'account',
        'key',
        'api_key',
        'access_token',
        'refresh_token',
        'password',
        'pass',
        'pwd',
        'secret',
        'hash',
        'hmac',
        'signature',
        'nonce',
        'timestamp',
        't',
        '_t',
        '_token',
        '__token',
        'csrf',
        'xsrf',
        '_wpnonce',
        'wpnonce',
    ]

    def __init__(self):
        self.compiled_auth_patterns = [re.compile(p, re.IGNORECASE) for p in self.AUTHENTICATED_PATTERNS]
        self.compiled_api_patterns = [re.compile(p, re.IGNORECASE) for p in self.API_PATTERNS]
        self.compiled_mobile_patterns = [re.compile(p, re.IGNORECASE) for p in self.MOBILE_PATTERNS]
        self.compiled_admin_patterns = [re.compile(p, re.IGNORECASE) for p in self.ADMIN_PATTERNS]
        self.compiled_public_patterns = [re.compile(p, re.IGNORECASE) for p in self.PUBLIC_PATTERNS]

    def classify_endpoint(self, endpoint: str, method: str = "GET", 
                         response_status: Optional[int] = None,
                         response_headers: Optional[Dict[str, str]] = None,
                         response_body: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify an endpoint based on URL, method, and response characteristics.
        
        Returns:
            Dict with keys: 'type', 'confidence', 'reasons'
        """
        if not endpoint:
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'reasons': ['Empty endpoint']
            }

        # Normalize endpoint
        endpoint_lower = endpoint.lower().strip()
        
        # Parse URL if it's a full URL
        try:
            parsed = urlparse(endpoint_lower)
            path = parsed.path
            query_params = parse_qs(parsed.query)
        except Exception:
            path = endpoint_lower
            query_params = {}

        # Initialize scores for each type
        scores = {
            'public': 0,
            'authenticated': 0,
            'admin': 0,
            'api': 0,
            'mobile': 0
        }
        reasons = []

        # Check path patterns
        for pattern in self.compiled_auth_patterns:
            if pattern.search(path):
                scores['authenticated'] += 2
                reasons.append(f"Matches authenticated pattern: {pattern.pattern}")

        for pattern in self.compiled_api_patterns:
            if pattern.search(path):
                scores['api'] += 2
                reasons.append(f"Matches API pattern: {pattern.pattern}")

        for pattern in self.compiled_mobile_patterns:
            if pattern.search(path):
                scores['mobile'] += 2
                reasons.append(f"Matches mobile pattern: {pattern.pattern}")

        for pattern in self.compiled_admin_patterns:
            if pattern.search(path):
                scores['admin'] += 2
                reasons.append(f"Matches admin pattern: {pattern.pattern}")

        for pattern in self.compiled_public_patterns:
            if pattern.search(path):
                scores['public'] += 1
                reasons.append(f"Matches public pattern: {pattern.pattern}")

        # Check for sensitive parameters in query string
        sensitive_found = []
        for param in query_params.keys():
            if param.lower() in self.SENSITIVE_PARAMETERS:
                sensitive_found.append(param)
        
        if sensitive_found:
            scores['authenticated'] += len(sensitive_found) * 2
            reasons.append(f"Sensitive parameters found: {', '.join(sensitive_found)}")

        # Check HTTP method
        if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            scores['authenticated'] += 1
            reasons.append(f"Non-GET method ({method}) suggests authenticated endpoint")

        # Check response status codes
        if response_status is not None:
            if response_status in [401, 403]:
                scores['authenticated'] += 3
                scores['admin'] += 1
                reasons.append(f"Response {response_status} indicates authentication/authorization required")
            elif response_status == 429:
                # Rate limited - often indicates protected endpoint
                scores['authenticated'] += 1
                reasons.append("Rate limited (429) suggests protected endpoint")
            elif response_status in [200, 201, 202, 204]:
                # Successful response - check content type
                if response_headers:
                    content_type = response_headers.get('content-type', '').lower()
                    if 'application/json' in content_type:
                        scores['api'] += 2
                        reasons.append("JSON response suggests API endpoint")
                    elif 'text/html' in content_type:
                        # HTML could be anything, but check for admin/login indicators
                        if response_body:
                            body_lower = response_body.lower()
                            if any(word in body_lower for word in ['login', 'password', 'username', 'sign in']):
                                scores['authenticated'] += 2
                                reasons.append("HTML contains login/auth indicators")
                            elif any(word in body_lower for word in ['admin', 'dashboard', 'control panel']):
                                scores['admin'] += 2
                                reasons.append("HTML contains admin/dashboard indicators")

        # Determine the highest scoring type
        max_score = 0
        classified_type = 'public'  # default
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                # Get the type with highest score
                for endpoint_type, score in scores.items():
                    if score == max_score:
                        classified_type = endpoint_type
                        break
            # Calculate confidence based on score relative to max possible
            # Rough heuristic: confidence = min(0.95, 0.3 + (score * 0.1))
            confidence = min(0.95, 0.3 + (max_score * 0.1))
        else:
            # Default to public if no patterns matched
            classified_type = 'public'
            confidence = 0.3
            reasons.append("No specific patterns matched, defaulting to public")

        return {
            'type': classified_type,
            'confidence': round(confidence, 2),
            'reasons': reasons,
            'scores': scores
        }

    def classify_target_endpoints(self, target: Target) -> Dict[str, Any]:
        """
        Classify all endpoints for a target and update the target's endpoint_classifications.
        
        Returns:
            Dict with classification summary
        """
        if not target.endpoints:
            return {
                'total_endpoints': 0,
                'classified': {},
                'message': 'No endpoints to classify'
            }

        classifications = {}
        type_counts = {
            'public': 0,
            'authenticated': 0,
            'admin': 0,
            'api': 0,
            'mobile': 0,
            'unknown': 0
        }

        for endpoint_data in target.endpoints:
            if isinstance(endpoint_data, dict):
                endpoint_url = endpoint_data.get('url', '') or endpoint_data.get('endpoint', '')
                method = endpoint_data.get('method', 'GET')
                # Extract response info if available from plugin runs or manual testing
                response_status = endpoint_data.get('status_code')
                response_headers = endpoint_data.get('headers', {})
                response_body = endpoint_data.get('response_body', '')
            else:
                # Assume it's a string URL
                endpoint_url = str(endpoint_data)
                method = 'GET'
                response_status = None
                response_headers = {}
                response_body = ''

            if not endpoint_url:
                continue

            classification = self.classify_endpoint(
                endpoint=endpoint_url,
                method=method,
                response_status=response_status,
                response_headers=response_headers,
                response_body=response_body
            )
            
            endpoint_type = classification['type']
            classifications[endpoint_url] = {
                'type': endpoint_type,
                'confidence': classification['confidence'],
                'reasons': classification['reasons']
            }
            type_counts[endpoint_type] = type_counts.get(endpoint_type, 0) + 1

        # Update target's endpoint_classifications field
        target.endpoint_classifications = classifications

        # Determine overall target classification based on majority
        if type_counts['authenticated'] > 0 or type_counts['admin'] > 0:
            primary_type = 'authenticated' if type_counts['authenticated'] >= type_counts['admin'] else 'admin'
        elif type_counts['api'] > 0:
            primary_type = 'api'
        elif type_counts['mobile'] > 0:
            primary_type = 'mobile'
        else:
            primary_type = 'public'

        return {
            'total_endpoints': len(target.endpoints),
            'classified': classifications,
            'type_counts': type_counts,
            'primary_type': primary_type,
            'classification_summary': f"Target classified as {primary_type} based on endpoint analysis"
        }


# Global instance for easy access
endpoint_classifier = EndpointClassifier()