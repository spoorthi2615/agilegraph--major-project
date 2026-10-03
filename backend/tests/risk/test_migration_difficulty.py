from src.risk.migration_difficulty import extract_migration_difficulty

def test_migration_difficulty_known():
    inputs = {
        "code_change": 5,
        "dependency_change": 0,
        "certificate_change": 1,
        "infrastructure_change": 0
    }
    factor = extract_migration_difficulty(inputs)
    assert factor.value == (0.5 * 0.4) + (0.5 * 0.2)
    assert factor.confidence == 0.8

def test_migration_difficulty_unknown():
    factor = extract_migration_difficulty({})
    assert factor.value is None
    assert factor.confidence == 0.0
