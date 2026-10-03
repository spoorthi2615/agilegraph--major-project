from src.risk.factors import FactorValue

# INITIAL HEURISTIC MAPPING - NOT FINAL WEIGHTS
# Represents post-quantum migration risk in this project's context, 
# not a generic statement that every use is currently universally weak.
# 1.0 = Highly vulnerable to quantum/classical attacks
# 0.5 = Transitioning/Medium weakness
# 0.0 = Quantum resistant / currently strong
DEFAULT_WEAKNESS_MAP = {
    "md5": 1.0,
    "sha1": 1.0,
    "des": 1.0,
    "3des": 0.8,
    "rsa": 0.9, # Post-quantum vulnerable
    "ecdsa": 0.9, # Post-quantum vulnerable
    "aes": 0.3, # Symmetric (Grover's)
    "sha256": 0.1,
    "sha512": 0.05,
    "kyber": 0.0, # PQC
    "dilithium": 0.0, # PQC
}

def extract_crypto_weakness(algorithm: str, weakness_map: dict = None, key_size: int = None) -> FactorValue:
    if weakness_map is None:
        weakness_map = DEFAULT_WEAKNESS_MAP
        
    if not algorithm:
        return FactorValue(value=None, source="algorithm unknown", confidence=0.0)
        
    alg = algorithm.lower()
    
    for key, weakness in weakness_map.items():
        if key in alg:
            # Explicit key size modifications for RSA
            if key == "rsa" and key_size is not None:
                if key_size <= 1024:
                    return FactorValue(value=1.0, source=f"algorithm classification (rsa-{key_size})", confidence=0.9)
                elif key_size >= 4096:
                    return FactorValue(value=0.8, source=f"algorithm classification (rsa-{key_size})", confidence=0.9)
                else:
                    return FactorValue(value=0.9, source=f"algorithm classification (rsa-{key_size})", confidence=0.9)
                    
            return FactorValue(value=weakness, source=f"algorithm classification ({key})", confidence=0.9)
            
    return FactorValue(value=None, source=f"unrecognized algorithm ({algorithm})", confidence=0.0)
