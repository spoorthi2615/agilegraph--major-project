import ast
from typing import List
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

class PythonCryptoVisitor(ast.NodeVisitor):
    def __init__(self, repository: str, filepath: str):
        self.repository = repository
        self.filepath = filepath
        self.findings: List[FindingRecord] = []
        
        # Explicit small set of APIs
        self.target_modules = {"cryptography", "hashlib", "Crypto", "Cryptodome", "rsa"}
        self.imported_modules = set(self.target_modules)
        self.imported_names = set()

    def visit_Import(self, node):
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in self.target_modules:
                mod_name = alias.asname if alias.asname else alias.name
                self.imported_modules.add(mod_name)
                self.findings.append(FindingRecord(
                    asset_type=AssetType.LIBRARY,
                    repository=self.repository,
                    file=self.filepath,
                    line=node.lineno,
                    language=Language.PYTHON,
                    library=base_module,
                    evidence=f"Imported {alias.name}",
                    confidence=1.0
                ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in self.target_modules or "Crypto" in node.module or "Cryptodome" in node.module:
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.imported_names.add(name)
                
                self.findings.append(FindingRecord(
                    asset_type=AssetType.LIBRARY,
                    repository=self.repository,
                    file=self.filepath,
                    line=node.lineno,
                    language=Language.PYTHON,
                    library=base_module,
                    evidence=f"Imported from {node.module}",
                    confidence=1.0
                ))
        self.generic_visit(node)

    def visit_Call(self, node):
        # Build full dot-separated name for the function called (e.g. "Cryptodome.Cipher.AES.new")
        full_name = self._get_full_name(node.func)
        if not full_name:
            self.generic_visit(node)
            return
            
        parts = full_name.split('.')
        base = parts[0]
        
        is_crypto_call = False
        algorithm = None
        api = full_name
        
        # 1. Match imported aliases (h.md5) or full crypto modules (hashlib.md5, Cryptodome.Cipher.AES.new)
        if base in self.imported_modules or base in self.imported_names or base in ("Crypto", "Cryptodome", "cryptography", "rsa", "hashlib"):
            # Try to identify the algorithm from the parts
            for part in parts:
                p = part.lower()
                if p in ("md5", "sha1", "sha256", "sha512", "des", "des3", "aes", "rsa", "arc4", "blowfish", "generate_private_key", "newkeys"):
                    algorithm = part
                    break
                    
            if algorithm:
                is_crypto_call = True
                
        # 2. Check for hashlib.new("sha1")
        if (base == "hashlib" or base in self.imported_modules) and "new" in parts:
            if node.args and isinstance(node.args[0], ast.Constant):
                algorithm = str(node.args[0].value)
                is_crypto_call = True

        if is_crypto_call and algorithm:
            # Clean up algorithm name
            algorithm = algorithm.lower()
            if algorithm == "newkeys":
                algorithm = "rsa"
            elif algorithm == "generate_private_key":
                algorithm = "rsa"
                
            op = "encryption"
            if algorithm in ("md5", "sha1", "sha256", "sha512"):
                op = "hashing"
            elif algorithm == "rsa" and "generate" in full_name.lower():
                op = "key_generation"
            elif algorithm == "rsa" and "newkeys" in full_name.lower():
                op = "key_generation"

            self.findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=self.repository,
                file=self.filepath,
                line=node.lineno,
                language=Language.PYTHON,
                library=base,
                api=f"{api}()",
                algorithm=algorithm,
                operation=op,
                evidence=f"Called {api}()",
                confidence=1.0,
                extra=self._extract_key_size(node)
            ))
        
        self.generic_visit(node)
        
    def _get_full_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_full_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        return ""
        
    def _extract_key_size(self, node: ast.Call) -> dict:
        key_size = None
        for kw in node.keywords:
            if kw.arg == "key_size" and isinstance(kw.value, ast.Constant):
                key_size = kw.value.value
                
        # Positional arguments: e.g. generate_private_key(65537, 1024)
        if not key_size and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            key_size = node.args[1].value
        elif not key_size and len(node.args) == 1 and isinstance(node.args[0], ast.Constant):
            # newkeys(1024) or generate(1024)
            key_size = node.args[0].value
            
        return {"key_size": int(key_size)} if key_size and isinstance(key_size, (int, float)) else {}

def scan_python_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    visitor = PythonCryptoVisitor(repository, filepath)
    visitor.visit(tree)
    return visitor.findings
