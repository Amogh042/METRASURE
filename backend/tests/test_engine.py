import pytest
from app.engine.core import calculate, RuleEngineException
from app.db.models import Instrument, OIMLRule

class MockInstrument:
    def __init__(self, verification_interval=1.0, accuracy_class="III", unit="kg"):
        self.verification_interval = verification_interval
        self.accuracy_class = accuracy_class
        self.unit = unit

class MockRule:
    def __init__(self, rule_id="RULE-1", permissible_error=1.0, standard_version="2006", source_reference="Ref", condition="Always"):
        self.rule_id = rule_id
        self.condition = condition
        self.permissible_error = permissible_error
        self.standard_version = standard_version
        self.source_reference = source_reference

def test_missing_rule():
    inst = MockInstrument()
    with pytest.raises(RuleEngineException, match="Missing applicable rule configuration"):
        calculate("Accuracy", inst, [{"test_load": 10, "indicated_value": 10}], None)

def test_missing_accuracy_class():
    inst = MockInstrument(accuracy_class=None)
    rule = MockRule()
    with pytest.raises(RuleEngineException, match="Instrument is missing an accuracy class."):
        calculate("Accuracy", inst, [{"test_load": 10, "indicated_value": 10}], [rule])

def test_unsupported_test_type():
    inst = MockInstrument()
    rule = MockRule()
    with pytest.raises(RuleEngineException, match="Unsupported test type"):
        calculate("UnknownTest", inst, [{"test_load": 10, "indicated_value": 10}], [rule])

# Accuracy Module Tests
def test_accuracy_pass():
    inst = MockInstrument(verification_interval=1.0, unit="kg")
    rule = MockRule(permissible_error=1.0) # MPE = 1.0 * 1.0 = 1.0
    measurements = [
        {"test_load": 10.0, "indicated_value": 10.5, "unit": "kg"}, # error = 0.5 (PASS)
    ]
    res = calculate("Accuracy", inst, measurements, [rule])
    assert res["pass_fail"] == "PASS"

def test_accuracy_fail_above_limit():
    inst = MockInstrument(verification_interval=1.0, unit="kg")
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 10.0, "indicated_value": 11.5, "unit": "kg"}, # error = 1.5 (FAIL)
    ]
    res = calculate("Accuracy", inst, measurements, [rule])
    assert res["pass_fail"] == "FAIL"

def test_accuracy_boundary_condition():
    inst = MockInstrument(verification_interval=1.0, unit="kg")
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 10.0, "indicated_value": 11.0, "unit": "kg"}, # error = 1.0 (PASS, exact boundary)
    ]
    res = calculate("Accuracy", inst, measurements, [rule])
    assert res["pass_fail"] == "PASS"

def test_accuracy_negative_load():
    inst = MockInstrument(verification_interval=1.0, unit="kg")
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": -10.0, "indicated_value": 10.5, "unit": "kg"},
    ]
    with pytest.raises(RuleEngineException, match="Invalid negative load"):
        calculate("Accuracy", inst, measurements, [rule])

def test_accuracy_wrong_unit():
    inst = MockInstrument(verification_interval=1.0, unit="kg")
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 10.0, "indicated_value": 10.5, "unit": "g"}, # Wrong unit
    ]
    with pytest.raises(RuleEngineException, match="Measurement unit"):
        calculate("Accuracy", inst, measurements, [rule])

def test_accuracy_missing_measurement_data():
    inst = MockInstrument(verification_interval=1.0, unit="kg")
    rule = MockRule(permissible_error=1.0)
    measurements = []
    with pytest.raises(RuleEngineException, match="Missing measurements"):
        calculate("Accuracy", inst, measurements, [rule])

# Repeatability Module Tests
def test_repeatability_pass():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=1.0)
    # Needs at least 2 measurements at same load
    measurements = [
        {"test_load": 50.0, "indicated_value": 50.1},
        {"test_load": 50.0, "indicated_value": 50.8}, # diff = 0.7 <= 1.0
    ]
    res = calculate("Repeatability", inst, measurements, [rule])
    assert res["pass_fail"] == "PASS"

def test_repeatability_fail():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 50.0, "indicated_value": 50.1},
        {"test_load": 50.0, "indicated_value": 51.2}, # diff = 1.1 > 1.0 (FAIL)
    ]
    res = calculate("Repeatability", inst, measurements, [rule])
    assert res["pass_fail"] == "FAIL"

def test_repeatability_different_loads():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 50.0, "indicated_value": 50.1},
        {"test_load": 60.0, "indicated_value": 60.1},
    ]
    with pytest.raises(RuleEngineException, match="Repeatability test loads must be identical"):
        calculate("Repeatability", inst, measurements, [rule])

# Eccentricity Module Tests
def test_eccentricity_pass():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"position": "Center", "test_load": 50.0, "indicated_value": 50.5},
        {"position": "Front-Left", "test_load": 50.0, "indicated_value": 49.5},
    ]
    res = calculate("Eccentricity", inst, measurements, [rule])
    assert res["pass_fail"] == "PASS"

def test_eccentricity_missing_position():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 50.0, "indicated_value": 50.5}, # Missing position
    ]
    with pytest.raises(RuleEngineException, match="Missing position"):
        calculate("Eccentricity", inst, measurements, [rule])

# Zero Module Tests
def test_zero_pass():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=0.25) # Typically 0.25e for zero
    measurements = [
        {"test_load": 0.0, "indicated_value": 0.2}, # diff 0.2 <= 0.25 (PASS)
    ]
    res = calculate("Zero", inst, measurements, [rule])
    assert res["pass_fail"] == "PASS"

def test_zero_fail():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=0.25)
    measurements = [
        {"test_load": 0.0, "indicated_value": 0.3}, # diff 0.3 > 0.25 (FAIL)
    ]
    res = calculate("Zero", inst, measurements, [rule])
    assert res["pass_fail"] == "FAIL"

# Tare Module Tests
def test_tare_pass():
    inst = MockInstrument(verification_interval=1.0)
    rule = MockRule(permissible_error=1.0)
    measurements = [
        {"test_load": 10.0, "indicated_value": 10.5}, # error 0.5 <= 1.0 (PASS)
    ]
    res = calculate("Tare", inst, measurements, [rule])
    assert res["pass_fail"] == "PASS"
