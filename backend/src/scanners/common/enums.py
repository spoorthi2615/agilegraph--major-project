from enum import Enum

class AssetType(str, Enum):
    FILE = "file"
    CRYPTO_USAGE = "crypto_usage"
    CERTIFICATE = "certificate"
    ENDPOINT = "endpoint"
    LIBRARY = "library"
    SENSITIVE_DATA = "sensitive_data"

class Language(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    GO = "go"
    UNKNOWN = "unknown"
