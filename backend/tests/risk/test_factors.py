from src.risk.factors import FactorValue

def test_factor_value():
    fv = FactorValue(value=1.0, source="test", confidence=1.0)
    assert fv.value == 1.0
