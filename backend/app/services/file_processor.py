"""File processing service for extracting data from uploaded files."""
import re
import logging
import tempfile
import json
from typing import Optional

logger = logging.getLogger(__name__)


def extract_all_data_from_text(text: str) -> dict:
    """Extract all types of data from text: credentials, IPs, domains, endpoints, etc."""
    result = {
        'credentials': [],
        'ips': [],
        'domains': [],
        'endpoints': [],
        'notes': [],
        'usernames': [],
        'passwords': [],
    }
    
    ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    result['ips'] = list(set(re.findall(ip_pattern, text)))
    
    domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|io|co|app|dev|xyz|info|biz|us|uk|ca|au|de|fr|jp|cn|ru|br|in|php|htm|html)\b'
    result['domains'] = list(set(d.lower() for d in re.findall(domain_pattern, text) if not any(x in d.lower() for x in ['example', 'test', 'localhost'])))
    
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    result['endpoints'] = list(set(re.findall(url_pattern, text)))
    
    cred_patterns = [
        (r'(?:username|user|login)[:\s]*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', 'email'),
        (r'(?:username|user|login)[:\s]*([a-zA-Z0-9_-]{3,30})', 'username'),
        (r'(?:password|pass|pwd)[:\s]*([^\s\n]{4,50})', 'password'),
        (r'(?:api[_-]?key|secret|token)[:\s]*([a-zA-Z0-9_-]{10,100})', 'api_key'),
    ]
    
    found_creds = set()
    for pattern, cred_type in cred_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                value = str(match[0]) if match[0] else ''
            else:
                value = str(match)
            
            if value and value.lower() not in found_creds and len(value) > 2:
                found_creds.add(value.lower())
                result['credentials'].append({
                    'type': cred_type,
                    'value': value,
                    'confidence': 'high' if len(value) > 8 else 'medium'
                })
                if cred_type == 'username':
                    result['usernames'].append(value)
                elif cred_type == 'password':
                    result['passwords'].append(value)
    
    table_pattern = r'(?:IP|Address|Host|Server|Endpoint|URL)[:\s]*([^\n]+(?:\n[^\n]+)*?)(?:\n\n|\Z)'
    for match in re.finditer(table_pattern, text, re.IGNORECASE):
        content = match.group(1).strip()
        if len(content) > 5:
            result['notes'].append(content[:200])
    
    return result


def extract_credentials_from_text(text: str) -> list[dict]:
    """Extract potential credentials from text using regex patterns."""
    data = extract_all_data_from_text(text)
    return data.get('credentials', [])


def parse_certificate_with_cryptography(cert_content: bytes) -> Optional[dict]:
    """Parse certificate files using cryptography library."""
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        
        result = {
            'type': 'certificate',
            'subject': None,
            'issuer': None,
            'valid_from': None,
            'valid_to': None,
            'serial': None,
            'fingerprint': None,
            'public_key_algorithm': None,
            'signature_algorithm': None,
        }
        
        if cert_content.startswith(b'-----BEGIN CERTIFICATE-----'):
            result['format'] = 'PEM'
            cert = x509.load_pem_x509_certificate(cert_content, default_backend())
        elif cert_content.startswith(b'\x30\x82'):
            result['format'] = 'DER'
            cert = x509.load_der_x509_certificate(cert_content, default_backend())
        else:
            result['format'] = 'unknown'
            return None
        
        try:
            subject_parts = []
            for attr in cert.subject:
                subject_parts.append(f"{attr.oid._name}={attr.value}")
            result['subject'] = ', '.join(subject_parts)
        except Exception:
            pass
        
        try:
            issuer_parts = []
            for attr in cert.issuer:
                issuer_parts.append(f"{attr.oid._name}={attr.value}")
            result['issuer'] = ', '.join(issuer_parts)
        except Exception:
            pass
        
        result['valid_from'] = str(cert.not_valid_before)
        result['valid_to'] = str(cert.not_valid_after)
        result['serial'] = str(cert.serial_number)
        
        try:
            fingerprint = cert.fingerprint(hashes.SHA256())
            result['fingerprint'] = fingerprint.hex()
        except Exception:
            pass
        
        try:
            result['signature_algorithm'] = cert.signature_algorithm_oid._name
        except Exception:
            pass
        
        try:
            pub_key = cert.public_key()
            result['public_key_algorithm'] = pub_key.__class__.__name__.replace('PublicKey', '')
        except Exception:
            pass
        
        return result
    
    except ImportError:
        logger.warning("cryptography library not available")
        return None
    except Exception as e:
        logger.error(f"Certificate parsing error: {e}")
        return None


def parse_certificate_openssl(cert_content: bytes) -> Optional[dict]:
    """Parse certificate files using openssl command as fallback."""
    try:
        import subprocess
        
        result = {
            'type': 'certificate',
            'subject': None,
            'issuer': None,
            'valid_from': None,
            'valid_to': None,
            'serial': None,
            'fingerprint': None,
        }
        
        if cert_content.startswith(b'-----BEGIN CERTIFICATE-----'):
            result['format'] = 'PEM'
            input_content = cert_content
        elif cert_content.startswith(b'\x30\x82'):
            result['format'] = 'DER'
            input_content = b'-----BEGIN CERTIFICATE-----\n' + cert_content + b'\n-----END CERTIFICATE-----\n'
        else:
            result['format'] = 'unknown'
            return None
        
        try:
            proc = subprocess.run(
                ['openssl', 'x509', '-inform', 'PEM', '-noout', '-text'],
                input=input_content,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if proc.returncode == 0:
                text_output = proc.stdout
                
                subject_match = re.search(r'Subject:\s*(.+)', text_output)
                if subject_match:
                    result['subject'] = subject_match.group(1).strip()
                
                issuer_match = re.search(r'Issuer:\s*(.+)', text_output)
                if issuer_match:
                    result['issuer'] = issuer_match.group(1).strip()
                
                dates_match = re.findall(r'Not (Before|After):\s*(.+)', text_output)
                for label, date in dates_match:
                    if label == 'Before':
                        result['valid_from'] = date.strip()
                    else:
                        result['valid_to'] = date.strip()
                
                serial_match = re.search(r'Serial Number:\s*(.+)', text_output)
                if serial_match:
                    result['serial'] = serial_match.group(1).strip()
        
        except Exception as e:
            logger.warning(f"OpenSSL parsing failed: {e}")
        
        return result if result['subject'] else None
    
    except Exception as e:
        logger.error(f"Certificate parsing error: {e}")
        return None


def parse_certificate(cert_content: bytes) -> Optional[dict]:
    """Parse certificate files (CER, PEM, etc.) with multiple fallbacks."""
    result = parse_certificate_with_cryptography(cert_content)
    if result:
        return result
    
    result = parse_certificate_openssl(cert_content)
    return result


def parse_pfx_with_cryptography(pfx_content: bytes, password: str = "") -> Optional[dict]:
    """Parse PFX/P12 certificate bundles using cryptography library."""
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.serialization import pkcs12
        
        result = {
            'type': 'pfx_bundle',
            'format': 'PFX/PKCS12',
            'certificates': [],
            'private_key_found': False,
            'private_key_encrypted': False,
        }
        
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_content,
                password.encode() if password else None,
                backend=default_backend()
            )
            
            if private_key:
                result['private_key_found'] = True
                result['private_key_algorithm'] = private_key.__class__.__name__.replace('PrivateKey', '')
            
            if certificate:
                subject_parts = []
                for attr in certificate.subject:
                    subject_parts.append(f"{attr.oid._name}={attr.value}")
                result['certificates'].append({
                    'subject': ', '.join(subject_parts),
                    'serial': str(certificate.serial_number),
                    'valid_from': str(certificate.not_valid_before),
                    'valid_to': str(certificate.not_valid_after),
                })
            
            for cert in (additional_certs or []):
                subject_parts = []
                for attr in cert.subject:
                    subject_parts.append(f"{attr.oid._name}={attr.value}")
                result['certificates'].append({
                    'subject': ', '.join(subject_parts),
                    'serial': str(cert.serial_number),
                    'valid_from': str(cert.not_valid_before),
                    'valid_to': str(cert.not_valid_after),
                })
            
            return result
            
        except Exception as e:
            if "password" in str(e).lower():
                result['error'] = "Invalid password"
            else:
                result['error'] = str(e)
            return result
    
    except ImportError:
        logger.warning("cryptography library not available for PFX parsing")
        return None
    except Exception as e:
        logger.error(f"PFX parsing error: {e}")
        return None


def parse_pfx_certificate(pfx_content: bytes, password: str = "") -> Optional[dict]:
    """Parse PFX/P12 certificate bundles with multiple fallbacks."""
    result = parse_pfx_with_cryptography(pfx_content, password)
    if result and 'error' not in result:
        return result
    
    if result and result.get('error') == 'Invalid password':
        return result
    
    return None


def extract_text_from_pdf_with_pdfplumber(pdf_content: bytes) -> str | None:
    """Extract text from PDF using pdfplumber (best quality)."""
    try:
        import pdfplumber
        import io
        
        text_parts = []
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            row_text = ' | '.join(str(cell) if cell else '' for cell in row)
                            if row_text.strip():
                                text_parts.append(f"[TABLE] {row_text}")
        
        return '\n\n'.join(text_parts)
    
    except ImportError:
        logger.warning("pdfplumber not available")
        return None
    except Exception as e:
        logger.error(f"pdfplumber extraction error: {e}")
        return None


def extract_text_from_pdf_with_pypdf2(pdf_content: bytes) -> str | None:
    """Extract text from PDF using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_content)
            pdf_path = f.name
        
        try:
            reader = PdfReader(pdf_path)
            text_parts = []
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            return '\n'.join(text_parts)
        finally:
            os.unlink(pdf_path)
    
    except ImportError:
        logger.warning("PyPDF2 not available")
        return None
    except Exception as e:
        logger.error(f"PyPDF2 extraction error: {e}")
        return None


def extract_text_fallback(content: bytes) -> str | None:
    """Fallback text extraction - looks for text between stream markers."""
    try:
        text = content.decode('latin-1', errors='ignore')
        
        text_parts = re.findall(r'\(([^)]{3,200})\)', text)
        
        clean_parts = []
        for part in text_parts:
            clean = ''.join(c for c in part if c.isprintable() or c in '\n\t')
            if len(clean) > 3:
                clean_parts.append(clean)
        
        return '\n'.join(clean_parts[:500])
    except Exception:
        return None


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF with multiple library fallbacks."""
    text = extract_text_from_pdf_with_pdfplumber(pdf_content)
    if text and len(text) > 100:
        return text
    
    text = extract_text_from_pdf_with_pypdf2(pdf_content)
    if text and len(text) > 100:
        return text
    
    text = extract_text_fallback(pdf_content)
    return text or ""


def process_file(filename: str, content: bytes, pfx_password: str = "") -> dict:
    """Process an uploaded file and extract all relevant data."""
    result = {
        'filename': filename,
        'type': 'unknown',
        'size': len(content),
        'credentials_found': [],
        'certificate_info': None,
        'text_content': None,
        'extracted_data': {
            'ips': [],
            'domains': [],
            'endpoints': [],
            'usernames': [],
            'passwords': [],
            'notes': [],
        },
        'warnings': [],
        'ai_used': False,
        'ai_extraction': None,
    }
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    try:
        if ext in ['pdf']:
            result['type'] = 'document'
            result['text_content'] = extract_text_from_pdf(content)
            
            if result['text_content']:
                extracted = extract_all_data_from_text(result['text_content'])
                result['credentials_found'] = extracted['credentials']
                result['extracted_data']['ips'] = extracted['ips']
                result['extracted_data']['domains'] = extracted['domains']
                result['extracted_data']['endpoints'] = extracted['endpoints']
                result['extracted_data']['usernames'] = extracted['usernames']
                result['extracted_data']['passwords'] = extracted['passwords']
                result['extracted_data']['notes'] = extracted['notes']
        
        elif ext in ['cer', 'crt', 'pem', 'der']:
            result['type'] = 'certificate'
            result['certificate_info'] = parse_certificate(content)
        
        elif ext in ['pfx', 'p12']:
            result['type'] = 'certificate_bundle'
            result['certificate_info'] = parse_pfx_certificate(content, pfx_password)
            if result['certificate_info'] and result['certificate_info'].get('error'):
                result['warnings'].append(result['certificate_info']['error'])
        
        elif ext in ['txt', 'log', 'json', 'xml', 'yaml', 'yml']:
            result['type'] = 'text'
            result['text_content'] = content.decode('utf-8', errors='ignore')
            
            if result['text_content']:
                extracted = extract_all_data_from_text(result['text_content'])
                result['credentials_found'] = extracted['credentials']
                result['extracted_data']['ips'] = extracted['ips']
                result['extracted_data']['domains'] = extracted['domains']
                result['extracted_data']['endpoints'] = extracted['endpoints']
                result['extracted_data']['usernames'] = extracted['usernames']
                result['extracted_data']['passwords'] = extracted['passwords']
                result['extracted_data']['notes'] = extracted['notes']
        
        elif ext in ['mp4', 'avi', 'mov', 'mkv']:
            result['type'] = 'video'
            result['warnings'].append("Video files are stored as reference, not processed")
        
        elif ext in ['zip', 'tar', 'gz', 'rar']:
            result['type'] = 'archive'
            result['warnings'].append("Archives require manual extraction")
        
        else:
            result['warnings'].append(f"Unknown file type: {ext}")
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        result['type'] = 'error'
        result['warnings'].append(f"Processing error: {str(e)}")
    
    return result


async def process_file_with_ai_async(filename: str, content: bytes, pfx_password: str = "") -> dict:
    """Process file with AI extraction (call this from async context)."""
    from app.services.openai_service import openai_service
    
    result = process_file(filename, content, pfx_password)
    
    if result['type'] == 'document' and result['text_content'] and openai_service.is_available:
        if len(result['text_content']) > 100:
            try:
                ai_result = await openai_service.extract_from_pdf(
                    result['text_content'],
                    filename
                )
                if ai_result:
                    result['ai_extraction'] = ai_result
                    result['ai_used'] = True
                    
                    if ai_result.get('credentials'):
                        for cred in ai_result['credentials']:
                            result['credentials_found'].append({
                                'type': cred.get('type', 'unknown'),
                                'value': cred.get('value', ''),
                                'confidence': 'high',
                                'source': 'ai_extraction'
                            })
                    
                    if ai_result.get('ip_addresses'):
                        ips_set = set(result['extracted_data']['ips'])
                        ips_set.update(ai_result['ip_addresses'])
                        result['extracted_data']['ips'] = list(ips_set)
                    
                    if ai_result.get('domains'):
                        domains_set = set(result['extracted_data']['domains'])
                        domains_set.update(ai_result['domains'])
                        result['extracted_data']['domains'] = list(domains_set)
                    
                    if ai_result.get('endpoints'):
                        endpoints_set = set(result['extracted_data']['endpoints'])
                        endpoints_set.update(ai_result['endpoints'])
                        result['extracted_data']['endpoints'] = list(endpoints_set)
                    
                    if ai_result.get('notes'):
                        notes_set = set(result['extracted_data']['notes'])
                        notes_set.update(ai_result['notes'])
                        result['extracted_data']['notes'] = list(notes_set)
                    
                    if ai_result.get('test_accounts'):
                        for acc in ai_result['test_accounts']:
                            if acc.get('username'):
                                result['extracted_data']['usernames'].append(acc['username'])
                            if acc.get('password'):
                                result['extracted_data']['passwords'].append(acc['password'])
                            if acc.get('purpose'):
                                result['extracted_data']['notes'].append(f"Test Account: {acc['purpose']}")
            
            except Exception as e:
                result['warnings'].append(f"AI extraction failed: {str(e)}")
    
    return result
