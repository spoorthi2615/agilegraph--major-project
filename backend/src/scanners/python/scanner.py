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
        # Very basic check for hashlib.md5 or similar
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "hashlib":
                self.findings.append(FindingRecord(
                    asset_type=AssetType.CRYPTO_USAGE,
                    repository=self.repository,
                    file=self.filepath,
                    line=node.lineno,
                    language=Language.PYTHON,
                    library="hashlib",
                    api=f"hashlib.{node.func.attr}",
                    algorithm=node.func.attr,
                    operation="hashing",
                    evidence=f"Called hashlib.{node.func.attr}()",
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
