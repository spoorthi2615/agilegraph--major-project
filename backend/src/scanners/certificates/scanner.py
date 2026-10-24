import re
from typing import List, Optional
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

try:
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec, ed25519, ed448
    HAVE_CRYPTOGRAPHY = True
except ImportError:
    HAVE_CRYPTOGRAPHY = False

PEM_CERT_PATTERN = re.compile(
    r'-----BEGIN (?:X509 |TRUSTED )?CERTIFICATE-----[\s\S]*?-----END (?:X509 |TRUSTED )?CERTIFICATE-----'
)

# Code patterns in Python, Java, Go that load or manipulate certificates
PYTHON_CERT_CODE_PATTERN = re.compile(
    r'\b(ssl\.create_default_context|load_cert_chain|load_pem_x509_certificate|load_der_x509_certificate|get_server_certificate)\b'
)

JAVA_CERT_CODE_PATTERN = re.compile(
    r'\b(CertificateFactory\.getInstance|KeyStore\.getInstance|TrustManagerFactory\.getInstance)\b'
)

GO_CERT_CODE_PATTERN = re.compile(
    r'\b(tls\.LoadX509KeyPair|x509\.ParseCertificate|x509\.ParseCertificates|x509\.NewCertPool)\b'
)


def parse_pem_certificate(pem_text: str) -> Optional[dict]:
    """Parses a PEM certificate using cryptography library if available."""
    if not HAVE_CRYPTOGRAPHY:
        return None

    try:
        cert = x509.load_pem_x509_certificate(pem_text.encode('utf-8'))
        pub_key = cert.public_key()

        algo = "unknown"
        key_size = None
        if isinstance(pub_key, rsa.RSAPublicKey):
            algo = "rsa"
            key_size = pub_key.key_size
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            algo = "ecdsa"
            key_size = pub_key.key_size
        elif isinstance(pub_key, ed25519.Ed25519PublicKey):
            algo = "ed25519"
            key_size = 256
        elif isinstance(pub_key, ed448.Ed448PublicKey):
            algo = "ed448"
            key_size = 448
        elif isinstance(pub_key, dsa.DSAPublicKey):
            algo = "dsa"
            key_size = pub_key.key_size

        sig_algo = getattr(cert.signature_hash_algorithm, "name", None)
        subject_str = cert.subject.rfc4514_string()
        issuer_str = cert.issuer.rfc4514_string()

        return {
            "algorithm": algo,
            "key_size": key_size,
            "signature_algorithm": sig_algo,
            "subject": subject_str,
            "issuer": issuer_str,
            "not_valid_after": cert.not_valid_after_utc.isoformat() if hasattr(cert, "not_valid_after_utc") else cert.not_valid_after.isoformat()
        }
    except Exception:
        return None


def scan_certificate_file(repository: str, filepath: str, content: str) -> List[FindingRecord]:
    """Scans dedicated certificate files or any text file containing embedded PEM blocks."""
    findings = []
    
    # Check for PEM blocks
    matches = list(PEM_CERT_PATTERN.finditer(content))
    if matches:
        for idx, match in enumerate(matches, start=1):
            pem_block = match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            parsed = parse_pem_certificate(pem_block)
            
            algo = parsed.get("algorithm", "unknown") if parsed else "unknown"
            extra = parsed if parsed else {}
            
            findings.append(FindingRecord(
                asset_type=AssetType.CERTIFICATE,
                repository=repository,
                file=filepath,
                line=line_num,
                algorithm=algo,
                operation="certificate_identity",
                evidence=f"X.509 Certificate (PEM block #{idx})",
                confidence=1.0 if parsed else 0.85,
                extra=extra
            ))
    elif filepath.lower().endswith(('.crt', '.pem', '.cer', '.der', '.p12', '.pfx')):
        # Certificate file without plain PEM block (could be DER binary or format)
        findings.append(FindingRecord(
            asset_type=AssetType.CERTIFICATE,
            repository=repository,
            file=filepath,
            line=1,
            algorithm="unknown",
            operation="certificate_file",
            evidence=f"Certificate file: {filepath}",
            confidence=0.8,
            extra={"file_format": filepath.split('.')[-1].lower()}
        ))
        
    return findings


def scan_certificate_in_code(repository: str, filepath: str, code: str, language: Language) -> List[FindingRecord]:
    """Scans code files for certificate management, loading, and verification calls."""
    findings = []
    
    # First, also check if the code file has embedded PEM certificates (e.g. mock certs, test certs)
    pem_findings = scan_certificate_file(repository, filepath, code)
    findings.extend(pem_findings)

    # Next, scan for code loading APIs
    lines = code.split('\n')
    for i, line in enumerate(lines, start=1):
        pattern = None
        if language == Language.PYTHON:
            pattern = PYTHON_CERT_CODE_PATTERN
        elif language == Language.JAVA:
            pattern = JAVA_CERT_CODE_PATTERN
        elif language == Language.GO:
            pattern = GO_CERT_CODE_PATTERN

        if pattern:
            match = pattern.search(line)
            if match:
                api_name = match.group(1)
                findings.append(FindingRecord(
                    asset_type=AssetType.CERTIFICATE,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=language,
                    api=api_name,
                    operation="certificate_loading",
                    evidence=line.strip(),
                    confidence=0.9,
                    extra={"api": api_name}
                ))

    return findings
