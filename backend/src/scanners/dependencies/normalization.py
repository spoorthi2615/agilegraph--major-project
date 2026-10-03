def classify_crypto_relevance(package_name: str, ecosystem: str) -> str:
    """
    Categorizes: CRYPTOGRAPHIC, SECURITY_RELEVANT, GENERAL, UNKNOWN
    """
    pkg = package_name.lower()
    
    crypto_keywords = ["crypto", "bouncycastle", "hash", "aes", "rsa", "tls", "ssl", "jwt", "jwe"]
    security_keywords = ["auth", "security", "oauth", "password"]
    
    # Specific allowlist for known packages
    known_crypto = {
        "pypi": ["cryptography", "pycryptodome", "bcrypt", "argon2-cffi"],
        "maven": ["org.bouncycastle:bcprov-jdk15on", "commons-codec:commons-codec"],
        "go": ["golang.org/x/crypto"]
    }
    
    if ecosystem in known_crypto and pkg in known_crypto[ecosystem]:
        return "CRYPTOGRAPHIC"
        
    for kw in crypto_keywords:
        if kw in pkg:
            return "CRYPTOGRAPHIC"
            
    for kw in security_keywords:
        if kw in pkg:
            return "SECURITY_RELEVANT"
            
    return "GENERAL"
