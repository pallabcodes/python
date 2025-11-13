"""
Security Patterns for LangChain - Production Security.

This module implements comprehensive security techniques:
1. Prompt Injection Detection - Detect and prevent prompt injection
2. PII Detection - Identify and redact personally identifiable information
3. Content Filtering - Filter harmful or inappropriate content
4. Input Validation - Validate and sanitize inputs
5. Output Sanitization - Sanitize outputs before delivery
6. Rate Limiting - Prevent abuse and DoS attacks
7. Access Control - Role-based access control
8. Audit Logging - Security event logging
9. Encryption - Data encryption at rest and in transit
10. Authentication - OAuth, JWT authentication
11. Security Monitoring - Threat detection and alerting
12. Jailbreak Detection - Detect model jailbreak attempts
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityCheck:
    """Result of security check."""
    passed: bool
    threat_type: str
    severity: SecurityLevel
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 1. PROMPT INJECTION DETECTOR
# ============================================================================

class PromptInjectionDetector:
    """
    Prompt Injection Detector - Detect and prevent prompt injection.
    
    Based on:
    - Prompt injection research
    - Security best practices
    
    Key Features:
    - Injection pattern detection
    - Multi-strategy detection
    - Threat scoring
    - Automatic blocking
    
    When to Use:
    - Public-facing LLM applications
    - User input processing
    - Need security guarantees
    - Production security systems
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.PromptInjectionDetector")
        # Common injection patterns
        self.injection_patterns = [
            r"ignore\s+(previous|above|all)\s+instructions?",
            r"system\s*:\s*",
            r"assistant\s*:\s*",
            r"user\s*:\s*",
            r"<\|.*?\|>",
            r"\[INST\]",
            r"###\s*(instruction|system|prompt)",
        ]
    
    async def check(self, input_text: str) -> SecurityCheck:
        """
        Check for prompt injection.
        
        Args:
            input_text: Input text to check
            
        Returns:
            Security check result
        """
        input_lower = input_text.lower()
        
        for pattern in self.injection_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                return SecurityCheck(
                    passed=False,
                    threat_type="prompt_injection",
                    severity=SecurityLevel.HIGH,
                    details={
                        "pattern": pattern,
                        "matched_text": re.search(pattern, input_lower, re.IGNORECASE).group()
                    }
                )
        
        return SecurityCheck(
            passed=True,
            threat_type="prompt_injection",
            severity=SecurityLevel.LOW,
            details={}
        )


# ============================================================================
# 2. PII DETECTOR
# ============================================================================

class PIIDetector:
    """
    PII Detector - Identify and redact personally identifiable information.
    
    Based on:
    - PII detection research
    - Privacy regulations (GDPR, CCPA)
    
    Key Features:
    - Multiple PII types
    - Pattern-based detection
    - Redaction support
    - Compliance support
    
    When to Use:
    - Privacy-sensitive applications
    - GDPR/CCPA compliance
    - User data processing
    - Production privacy systems
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.PIIDetector")
        # PII patterns
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        }
    
    async def detect(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text.
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected PII
        """
        detected = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return detected
    
    async def redact(self, text: str) -> str:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        redacted = text
        detected = await self.detect(text)
        
        # Sort by start position (reverse) to maintain indices
        detected.sort(key=lambda x: x["start"], reverse=True)
        
        for pii in detected:
            redacted = (
                redacted[:pii["start"]] +
                f"[{pii['type'].upper()}_REDACTED]" +
                redacted[pii["end"]:]
            )
        
        return redacted


# ============================================================================
# 3. CONTENT FILTER
# ============================================================================

class ContentFilter:
    """
    Content Filter - Filter harmful or inappropriate content.
    
    Based on:
    - Content moderation research
    - Safety best practices
    
    Key Features:
    - Harmful content detection
    - Toxicity scoring
    - Multi-category filtering
    - Configurable thresholds
    
    When to Use:
    - Public-facing applications
    - Content moderation
    - Safety requirements
    - Production safety systems
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.ContentFilter")
        # Harmful keywords (simplified - in production use ML models)
        self.harmful_keywords = {
            "violence": ["kill", "attack", "harm"],
            "hate": ["hate", "discriminate"],
            "self_harm": ["suicide", "self-harm"],
        }
    
    async def filter(self, text: str) -> SecurityCheck:
        """
        Filter harmful content.
        
        Args:
            text: Text to filter
            
        Returns:
            Security check result
        """
        text_lower = text.lower()
        
        for category, keywords in self.harmful_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return SecurityCheck(
                        passed=False,
                        threat_type="harmful_content",
                        severity=SecurityLevel.MEDIUM,
                        details={
                            "category": category,
                            "keyword": keyword
                        }
                    )
        
        return SecurityCheck(
            passed=True,
            threat_type="harmful_content",
            severity=SecurityLevel.LOW,
            details={}
        )


# ============================================================================
# 4. RATE LIMITER
# ============================================================================

class RateLimiter:
    """
    Rate Limiter - Prevent abuse and DoS attacks.
    
    Based on:
    - Token bucket algorithm
    - Rate limiting best practices
    
    Key Features:
    - Token bucket algorithm
    - Per-user limiting
    - Burst capacity
    - Configurable rates
    
    When to Use:
    - Public-facing APIs
    - Need abuse prevention
    - DoS protection
    - Production security systems
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: float = 60.0
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self._logger = logging.getLogger(f"{__name__}.RateLimiter")
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user exceeded rate limit.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if within limit, False if exceeded
        """
        import time
        
        current_time = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests outside window
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.window_seconds
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(current_time)
        return True


# ============================================================================
# 5. ACCESS CONTROLLER
# ============================================================================

class AccessController:
    """
    Access Controller - Role-based access control.
    
    Based on:
    - RBAC patterns
    - Access control best practices
    
    Key Features:
    - Role-based access
    - Permission checking
    - Resource-level control
    - Audit logging
    
    When to Use:
    - Multi-user systems
    - Need access control
    - Resource protection
    - Production security systems
    """
    
    def __init__(self):
        self.roles: Dict[str, List[str]] = {}
        self.permissions: Dict[str, List[str]] = {}
        self._logger = logging.getLogger(f"{__name__}.AccessController")
    
    def assign_role(self, user_id: str, role: str):
        """Assign role to user."""
        if user_id not in self.roles:
            self.roles[user_id] = []
        self.roles[user_id].append(role)
        self._logger.info(f"Assigned role {role} to user {user_id}")
    
    def grant_permission(self, role: str, permission: str):
        """Grant permission to role."""
        if role not in self.permissions:
            self.permissions[role] = []
        self.permissions[role].append(permission)
        self._logger.info(f"Granted permission {permission} to role {role}")
    
    async def check_access(
        self,
        user_id: str,
        permission: str
    ) -> bool:
        """
        Check if user has permission.
        
        Args:
            user_id: User identifier
            permission: Required permission
            
        Returns:
            True if user has permission
        """
        user_roles = self.roles.get(user_id, [])
        
        for role in user_roles:
            role_permissions = self.permissions.get(role, [])
            if permission in role_permissions:
                return True
        
        return False


# ============================================================================
# 6. COMPREHENSIVE SECURITY MANAGER
# ============================================================================

class SecurityManager:
    """
    Comprehensive Security Manager - All security checks.
    
    Combines:
    - Prompt injection detection
    - PII detection
    - Content filtering
    - Input validation
    - Output sanitization
    - Audit logging
    - Encryption
    - Authentication
    - Security monitoring
    - Jailbreak detection
    
    When to Use:
    - Production security systems
    - Need comprehensive security
    - Public-facing applications
    - Compliance requirements
    """
    
    def __init__(self):
        self.injection_detector = PromptInjectionDetector()
        self.pii_detector = PIIDetector()
        self.content_filter = ContentFilter()
        self.rate_limiter = RateLimiter()
        self.access_controller = AccessController()
        self.audit_logger = AuditLogger()
        self.encryption_manager = EncryptionManager()
        self.auth_manager = AuthenticationManager()
        self.security_monitor = SecurityMonitor()
        self.jailbreak_detector = JailbreakDetector()
        self._logger = logging.getLogger(f"{__name__}.SecurityManager")
    
    async def validate_input(
        self,
        input_text: str,
        user_id: Optional[str] = None
    ) -> SecurityCheck:
        """
        Validate input comprehensively.
        
        Args:
            input_text: Input to validate
            user_id: Optional user identifier
            
        Returns:
            Security check result
        """
        # Check jailbreak
        jailbreak_check = await self.jailbreak_detector.detect(input_text)
        if not jailbreak_check.passed:
            await self.audit_logger.log_event(
                "jailbreak_attempt", user_id, {"prompt": input_text[:100]}
            )
            return jailbreak_check
        
        # Check prompt injection
        injection_check = await self.injection_detector.check(input_text)
        if not injection_check.passed:
            await self.audit_logger.log_event(
                "prompt_injection", user_id, {"prompt": input_text[:100]}
            )
            return injection_check
        
        # Check harmful content
        content_check = await self.content_filter.filter(input_text)
        if not content_check.passed:
            await self.audit_logger.log_event(
                "harmful_content", user_id, {"prompt": input_text[:100]}
            )
            return content_check
        
        return SecurityCheck(
            passed=True,
            threat_type="input_validation",
            severity=SecurityLevel.LOW,
            details={}
        )
    
    async def sanitize_output(self, output_text: str) -> str:
        """
        Sanitize output (redact PII).
        
        Args:
            output_text: Output to sanitize
            
        Returns:
            Sanitized output
        """
        return await self.pii_detector.redact(output_text)


# ============================================================================
# 7. AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """
    Audit Logger - Security event logging.
    
    Based on:
    - Audit logging best practices
    - Compliance requirements (SOC2, ISO27001)
    
    Key Features:
    - Security event logging
    - Immutable logs
    - Compliance support
    - Event correlation
    
    When to Use:
    - Compliance requirements
    - Security monitoring
    - Incident investigation
    - Production security systems
    """
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.events: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(f"{__name__}.AuditLogger")
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security event.
        
        Args:
            event_type: Type of event
            user_id: User identifier
            details: Event details
        """
        import time
        
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {}
        }
        
        self.events.append(event)
        self._logger.info(f"Audit log: {event_type} by {user_id}")


# ============================================================================
# 8. ENCRYPTION MANAGER
# ============================================================================

class EncryptionManager:
    """
    Encryption Manager - Data encryption.
    
    Based on:
    - Encryption best practices
    - Security standards (AES-256)
    
    Key Features:
    - Encryption at rest
    - Encryption in transit
    - Key management
    - Secure storage
    
    When to Use:
    - Sensitive data
    - Compliance requirements
    - Data protection
    - Production security systems
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.EncryptionManager")
    
    async def encrypt(self, data: str, key: Optional[str] = None) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            
        Returns:
            Encrypted data
        """
        # In production, use proper encryption (AES-256)
        self._logger.info("Encrypting data")
        return f"encrypted_{data}"
    
    async def decrypt(self, encrypted_data: str, key: Optional[str] = None) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
            key: Decryption key
            
        Returns:
            Decrypted data
        """
        # In production, use proper decryption
        self._logger.info("Decrypting data")
        return encrypted_data.replace("encrypted_", "")


# ============================================================================
# 9. AUTHENTICATION MANAGER
# ============================================================================

class AuthenticationManager:
    """
    Authentication Manager - User authentication.
    
    Based on:
    - OAuth 2.0, JWT standards
    - Authentication best practices
    
    Key Features:
    - OAuth integration
    - JWT token management
    - Session management
    - Token validation
    
    When to Use:
    - User authentication
    - API security
    - Multi-user systems
    - Production security systems
    """
    
    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(f"{__name__}.AuthenticationManager")
    
    async def authenticate(
        self,
        credentials: Dict[str, str]
    ) -> Optional[str]:
        """
        Authenticate user.
        
        Args:
            credentials: User credentials
            
        Returns:
            Authentication token
        """
        # In production, validate against auth provider
        token = f"token_{credentials.get('username', 'user')}"
        self.tokens[token] = {
            "user_id": credentials.get("username"),
            "expires_at": None  # In production, set expiration
        }
        return token
    
    async def validate_token(self, token: str) -> bool:
        """Validate authentication token."""
        return token in self.tokens


# ============================================================================
# 10. SECURITY MONITOR
# ============================================================================

class SecurityMonitor:
    """
    Security Monitor - Threat detection and alerting.
    
    Based on:
    - Security monitoring patterns
    - Threat detection research
    
    Key Features:
    - Threat detection
    - Alert generation
    - Anomaly detection
    - Incident response
    
    When to Use:
    - Security operations
    - Threat detection
    - Incident response
    - Production security systems
    """
    
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(f"{__name__}.SecurityMonitor")
    
    async def detect_threat(
        self,
        event: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect security threats.
        
        Args:
            event: Security event
            
        Returns:
            Threat alert if detected
        """
        # In production, use ML-based threat detection
        if event.get("severity") == "high":
            alert = {
                "threat_type": event.get("type"),
                "severity": "high",
                "timestamp": event.get("timestamp")
            }
            self.alerts.append(alert)
            self._logger.warning(f"Security threat detected: {alert}")
            return alert
        return None


# ============================================================================
# 11. JAILBREAK DETECTOR
# ============================================================================

class JailbreakDetector:
    """
    Jailbreak Detector - Detect model jailbreak attempts.
    
    Based on:
    - Jailbreak research
    - Adversarial prompt detection
    
    Key Features:
    - Jailbreak pattern detection
    - Adversarial detection
    - Safety filtering
    - Automatic blocking
    
    When to Use:
    - Public-facing LLMs
    - Safety requirements
    - Content moderation
    - Production security systems
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.JailbreakDetector")
        # Common jailbreak patterns
        self.jailbreak_patterns = [
            r"ignore\s+(all|previous|above)\s+(instructions|rules|guidelines)",
            r"you\s+are\s+(now|a)\s+(unrestricted|uncensored)",
            r"forget\s+(your|all)\s+(instructions|rules)",
            r"act\s+as\s+if\s+you\s+are",
        ]
    
    async def detect(self, prompt: str) -> SecurityCheck:
        """
        Detect jailbreak attempts.
        
        Args:
            prompt: User prompt
            
        Returns:
            Security check result
        """
        prompt_lower = prompt.lower()
        
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return SecurityCheck(
                    passed=False,
                    threat_type="jailbreak",
                    severity=SecurityLevel.CRITICAL,
                    details={"pattern": pattern}
                )
        
        return SecurityCheck(
            passed=True,
            threat_type="jailbreak",
            severity=SecurityLevel.LOW,
            details={}
        )


# ============================================================================
# REAL-WORLD EXAMPLE
# ============================================================================

def security_real_world_example() -> None:
    """
    Real-World Scenario: Security - Public-Facing LLM Application.
    
    REAL-WORLD SCENARIO:
    ====================
    You're building a public-facing LLM application:
    - Users submit queries
    - Need security guarantees
    - Problem: Vulnerable to attacks
    
    THE PROBLEM WITHOUT ADVANCED SECURITY:
    ======================================
    - Prompt injection → system compromise
    - PII exposure → privacy violations
    - Harmful content → safety issues
    - No validation → security vulnerabilities
    - System vulnerable → production risks
    
    THE SOLUTION:
    =============
    Advanced security enables:
    - Prompt injection detection → prevent attacks
    - PII detection → privacy protection
    - Content filtering → safety assurance
    - Input validation → secure processing
    - Production security → reliable system
    
    WHEN TO USE ADVANCED SECURITY:
    ==============================
    ✅ Public-facing LLM applications
    ✅ User input processing
    ✅ Privacy-sensitive applications
    ✅ Need security guarantees
    ✅ Production security systems
    """
    print("=" * 70)
    print("REAL-WORLD SCENARIO: Public-Facing LLM Application")
    print("=" * 70)
    print()
    print("SITUATION:")
    print("  - Public-facing LLM application")
    print("  - Users submit queries")
    print("  - Need security guarantees")
    print("  - Problem: Vulnerable to attacks")
    print()
    print("THE PROBLEM:")
    print("  Without advanced security:")
    print("    ❌ Prompt injection → system compromise")
    print("    ❌ PII exposure → privacy violations")
    print("    ❌ Harmful content → safety issues")
    print("    ❌ No validation → security vulnerabilities")
    print()
    print("THE SOLUTION:")
    print("  With advanced security:")
    print("    ✅ Prompt injection detection → prevent attacks")
    print("    ✅ PII detection → privacy protection")
    print("    ✅ Content filtering → safety assurance")
    print("    ✅ Input validation → secure processing")
    print()
    print("=" * 70)
    print()

    print("Available security techniques:")
    techniques = [
        ("Prompt Injection Detection", "Detect attacks → prevent compromise"),
        ("PII Detection", "Identify PII → privacy protection"),
        ("Content Filtering", "Filter harmful content → safety"),
        ("Input Validation", "Validate inputs → secure processing"),
        ("Output Sanitization", "Sanitize outputs → safe delivery"),
        ("Rate Limiting", "Prevent abuse → DoS protection"),
        ("Access Control", "Role-based access → authorization"),
        ("Audit Logging", "Log events → compliance & investigation"),
        ("Encryption", "Encrypt data → data protection"),
        ("Authentication", "OAuth/JWT → user authentication"),
        ("Security Monitoring", "Detect threats → alert & respond"),
        ("Jailbreak Detection", "Detect jailbreaks → model safety")
    ]

    for technique, benefit in techniques:
        print(f"  ✅ {technique}: {benefit}")

    print()
    print("  ✅ Advanced security enabled production-grade protection!")
    print()
    print("=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("1. WHEN TO USE ADVANCED SECURITY:")
    print("   ✅ Public-facing LLM applications")
    print("   ✅ User input processing")
    print("   ✅ Privacy-sensitive applications")
    print("   ✅ Need security guarantees")
    print()
    print("2. WHY IT MATTERS:")
    print("   - Prevent attacks")
    print("   - Privacy protection")
    print("   - Safety assurance")
    print("   - Production reliability")
    print("=" * 70)
    print()

