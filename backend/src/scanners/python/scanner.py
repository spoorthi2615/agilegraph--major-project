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
        self.target_modules = {"cryptography", "hashlib", "Crypto"}

    def visit_Import(self, node):
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in self.target_modules:
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
            if base_module in self.target_modules:
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
        # Basic check for hashlib.md5(), hashlib.new('md5'), Crypto.Cipher.DES, etc.
        if isinstance(node.func, ast.Attribute):
            # Check for hashlib.md5(), hashlib.new('md5')
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "hashlib":
                algorithm = node.func.attr
                api = f"hashlib.{node.func.attr}"
                
                # Handle hashlib.new("md5")
                if algorithm == "new" and node.args and isinstance(node.args[0], ast.Constant):
                    algorithm = str(node.args[0].value)
                    
                self.findings.append(FindingRecord(
                    asset_type=AssetType.CRYPTO_USAGE,
                    repository=self.repository,
                    file=self.filepath,
                    line=node.lineno,
                    language=Language.PYTHON,
                    library="hashlib",
                    api=f"{api}()",
                    algorithm=algorithm,
                    operation="hashing",
                    evidence=f"Called {api}()",
                    confidence=1.0
                ))
            # Check for Crypto.Cipher.DES / AES etc, or just DES.new() if imported
            elif isinstance(node.func.value, ast.Name):
                if node.func.value.id in ("DES", "AES", "RSA", "Blowfish", "ARC4"):
                    algorithm = node.func.value.id
                    api = f"{algorithm}.{node.func.attr}"
                    self.findings.append(FindingRecord(
                        asset_type=AssetType.CRYPTO_USAGE,
                        repository=self.repository,
                        file=self.filepath,
                        line=node.lineno,
                        language=Language.PYTHON,
                        library="Crypto",
                        api=f"{api}()",
                        algorithm=algorithm,
                        operation="encryption",
                        evidence=f"Called {api}()",
                        confidence=1.0
                    ))
            elif isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
                if node.func.value.value.id in ("Crypto", "cryptography"):
                    algorithm = node.func.value.attr
                    api = f"{node.func.value.value.id}.{node.func.value.attr}.{node.func.attr}"
                    self.findings.append(FindingRecord(
                        asset_type=AssetType.CRYPTO_USAGE,
                        repository=self.repository,
                        file=self.filepath,
                        line=node.lineno,
                        language=Language.PYTHON,
                        library=node.func.value.value.id,
                        api=f"{api}()",
                        algorithm=algorithm,
                        operation="encryption",
                        evidence=f"Called {api}()",
                        confidence=1.0
                    ))
        self.generic_visit(node)

def scan_python_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    visitor = PythonCryptoVisitor(repository, filepath)
    visitor.visit(tree)
    return visitor.findings
