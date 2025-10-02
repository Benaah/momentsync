import os
import hashlib
import hmac
import secrets
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import ipaddress
import re

logger = logging.getLogger(__name__)


class SecurityService:
    """
    Comprehensive security service for MomentSync
    Includes JWT authentication, rate limiting, encryption, and access control
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.jwt_algorithm = 'HS256'
        self.access_token_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        self.refresh_token_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Rate limiting configuration
        self.rate_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 requests per 5 minutes
            'upload': {'requests': 10, 'window': 3600},  # 10 uploads per hour
            'api': {'requests': 100, 'window': 3600},  # 100 API calls per hour
            'password_reset': {'requests': 3, 'window': 3600},  # 3 password resets per hour
        }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create encryption key for data encryption
        """
        key = cache.get('encryption_key')
        if not key:
            key = Fernet.generate_key()
            cache.set('encryption_key', key, timeout=None)  # Never expire
        return key
    
    def generate_jwt_tokens(self, user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens
        """
        try:
            now = timezone.now()
            
            # Access token payload
            access_payload = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'iat': now,
                'exp': now + self.access_token_lifetime,
                'type': 'access',
                'jti': secrets.token_urlsafe(32)  # JWT ID for token revocation
            }
            
            # Refresh token payload
            refresh_payload = {
                'user_id': user.id,
                'iat': now,
                'exp': now + self.refresh_token_lifetime,
                'type': 'refresh',
                'jti': secrets.token_urlsafe(32)
            }
            
            # Generate tokens
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.jwt_algorithm)
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.jwt_algorithm)
            
            # Store refresh token in cache for validation
            cache.set(f'refresh_token_{refresh_payload["jti"]}', user.id, timeout=self.refresh_token_lifetime.total_seconds())
            
            return {
                'access': access_token,
                'refresh': refresh_token,
                'access_expires': now + self.access_token_lifetime,
                'refresh_expires': now + self.refresh_token_lifetime
            }
            
        except Exception as e:
            logger.error(f"Error generating JWT tokens: {str(e)}")
            raise
    
    def validate_jwt_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        """
        Validate JWT token and return payload
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            
            # Check token type
            if payload.get('type') != token_type:
                raise PermissionDenied('Invalid token type')
            
            # Check if token is revoked (for refresh tokens)
            if token_type == 'refresh':
                jti = payload.get('jti')
                if not cache.get(f'refresh_token_{jti}'):
                    raise PermissionDenied('Token has been revoked')
            
            # Check expiration
            if payload.get('exp', 0) < time.time():
                raise PermissionDenied('Token has expired')
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise PermissionDenied('Token has expired')
        except jwt.InvalidTokenError:
            raise PermissionDenied('Invalid token')
        except Exception as e:
            logger.error(f"Error validating JWT token: {str(e)}")
            raise PermissionDenied('Token validation failed')
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a JWT token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            jti = payload.get('jti')
            
            if jti:
                # Add to revocation list
                cache.set(f'revoked_token_{jti}', True, timeout=86400)  # 24 hours
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    def check_rate_limit(self, user_id: int, action: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limits
        """
        try:
            if action not in self.rate_limits:
                return {'allowed': True, 'remaining': 0, 'reset_time': None}
            
            limit_config = self.rate_limits[action]
            window = limit_config['window']
            max_requests = limit_config['requests']
            
            # Create rate limit key
            key = f'rate_limit_{action}_{user_id}'
            if ip_address:
                key += f'_{ip_address}'
            
            # Get current count
            current_count = cache.get(key, 0)
            
            if current_count >= max_requests:
                # Get reset time
                ttl = cache.ttl(key)
                reset_time = timezone.now() + timedelta(seconds=ttl) if ttl else None
                
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': reset_time,
                    'message': f'Rate limit exceeded. Try again in {ttl} seconds.'
                }
            
            # Increment counter
            cache.set(key, current_count + 1, timeout=window)
            
            return {
                'allowed': True,
                'remaining': max_requests - current_count - 1,
                'reset_time': timezone.now() + timedelta(seconds=window)
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return {'allowed': True, 'remaining': 0, 'reset_time': None}
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data
        """
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            raise
    
    def hash_password(self, password: str, salt: str = None) -> Dict[str, str]:
        """
        Hash password with salt
        """
        try:
            if not salt:
                salt = secrets.token_hex(32)
            
            # Use PBKDF2 for password hashing
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            key = base64.b64encode(kdf.derive(password.encode())).decode()
            
            return {
                'hash': key,
                'salt': salt
            }
            
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
            raise
    
    def verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """
        Verify password against hash
        """
        try:
            new_hash = self.hash_password(password, salt)
            return hmac.compare_digest(new_hash['hash'], hash_value)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure token
        """
        return secrets.token_urlsafe(length)
    
    def validate_ip_address(self, ip_address: str) -> bool:
        """
        Validate IP address format
        """
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
    
    def is_ip_allowed(self, ip_address: str, allowed_ips: List[str] = None) -> bool:
        """
        Check if IP address is allowed
        """
        try:
            if not allowed_ips:
                return True
            
            ip = ipaddress.ip_address(ip_address)
            
            for allowed_ip in allowed_ips:
                try:
                    if '/' in allowed_ip:
                        # CIDR notation
                        network = ipaddress.ip_network(allowed_ip)
                        if ip in network:
                            return True
                    else:
                        # Single IP
                        if ip == ipaddress.ip_address(allowed_ip):
                            return True
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking IP address: {str(e)}")
            return False
    
    def sanitize_input(self, input_string: str) -> str:
        """
        Sanitize user input to prevent XSS and injection attacks
        """
        try:
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
            
            for char in dangerous_chars:
                input_string = input_string.replace(char, '')
            
            # Remove script tags
            input_string = re.sub(r'<script.*?</script>', '', input_string, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove javascript: protocols
            input_string = re.sub(r'javascript:', '', input_string, flags=re.IGNORECASE)
            
            # Remove data: protocols
            input_string = re.sub(r'data:', '', input_string, flags=re.IGNORECASE)
            
            return input_string.strip()
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {str(e)}")
            return input_string
    
    def validate_file_upload(self, file, max_size: int = None, allowed_types: List[str] = None) -> Dict[str, Any]:
        """
        Validate file upload for security
        """
        try:
            if not file:
                return {'valid': False, 'error': 'No file provided'}
            
            # Check file size
            if max_size and file.size > max_size:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum size: {max_size / (1024*1024):.1f}MB'
                }
            
            # Check file type
            if allowed_types:
                file_type = file.content_type.split('/')[0]
                if file_type not in allowed_types:
                    return {
                        'valid': False,
                        'error': f'File type not allowed. Allowed types: {", ".join(allowed_types)}'
                    }
            
            # Check file extension
            file_extension = os.path.splitext(file.name)[1].lower()
            dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar']
            
            if file_extension in dangerous_extensions:
                return {
                    'valid': False,
                    'error': 'File type not allowed for security reasons'
                }
            
            # Check file content (basic magic number check)
            file.seek(0)
            header = file.read(1024)
            file.seek(0)
            
            # Check for executable signatures
            executable_signatures = [b'MZ', b'\x7fELF', b'\xfe\xed\xfa', b'\xce\xfa\xed\xfe']
            
            for signature in executable_signatures:
                if header.startswith(signature):
                    return {
                        'valid': False,
                        'error': 'File appears to be an executable and is not allowed'
                    }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating file upload: {str(e)}")
            return {'valid': False, 'error': 'File validation failed'}
    
    def log_security_event(self, event_type: str, user_id: int, details: Dict[str, Any], ip_address: str = None):
        """
        Log security events for monitoring
        """
        try:
            event = {
                'timestamp': timezone.now().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'ip_address': ip_address,
                'details': details
            }
            
            # Store in cache for real-time monitoring
            cache_key = f'security_event_{event_type}_{user_id}_{int(time.time())}'
            cache.set(cache_key, event, timeout=86400)  # 24 hours
            
            # Log to file
            logger.warning(f"Security Event: {event_type} - User: {user_id} - IP: {ip_address} - Details: {details}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
    
    def check_suspicious_activity(self, user_id: int, ip_address: str) -> Dict[str, Any]:
        """
        Check for suspicious user activity
        """
        try:
            # Check for multiple failed login attempts
            failed_logins = cache.get(f'failed_logins_{user_id}', 0)
            if failed_logins > 5:
                return {
                    'suspicious': True,
                    'reason': 'Multiple failed login attempts',
                    'severity': 'high'
                }
            
            # Check for unusual IP addresses
            user_ips = cache.get(f'user_ips_{user_id}', [])
            if ip_address not in user_ips and len(user_ips) > 0:
                # New IP address
                user_ips.append(ip_address)
                cache.set(f'user_ips_{user_id}', user_ips, timeout=86400)
                
                if len(user_ips) > 3:
                    return {
                        'suspicious': True,
                        'reason': 'Multiple IP addresses used',
                        'severity': 'medium'
                    }
            
            # Check for rapid API calls
            api_calls = cache.get(f'api_calls_{user_id}', 0)
            if api_calls > 1000:  # More than 1000 API calls in the last hour
                return {
                    'suspicious': True,
                    'reason': 'Excessive API usage',
                    'severity': 'medium'
                }
            
            return {'suspicious': False}
            
        except Exception as e:
            logger.error(f"Error checking suspicious activity: {str(e)}")
            return {'suspicious': False}
    
    def generate_csrf_token(self, user_id: int) -> str:
        """
        Generate CSRF token for user
        """
        try:
            token = secrets.token_urlsafe(32)
            cache.set(f'csrf_token_{user_id}', token, timeout=3600)  # 1 hour
            return token
        except Exception as e:
            logger.error(f"Error generating CSRF token: {str(e)}")
            return ''
    
    def validate_csrf_token(self, user_id: int, token: str) -> bool:
        """
        Validate CSRF token
        """
        try:
            stored_token = cache.get(f'csrf_token_{user_id}')
            return hmac.compare_digest(stored_token or '', token)
        except Exception as e:
            logger.error(f"Error validating CSRF token: {str(e)}")
            return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers for HTTP responses
        """
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
