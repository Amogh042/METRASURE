import pytest
from app.engine.core import calculate, RuleEngineException
from app.engine.conditions import parse_condition, select_rule
from seed import build_table6_rules


class MockInstrument:
    def __init__(self, verification_interval=0.01, accuracy_class="III", unit="kg"):
        self.verification_interval = verification_interval
        self.accuracy_class = accuracy_class
        self.unit = unit


def seeded_rules(test_type, accuracy_class):
    return [r for r in build_table6_rules() if r.test_type == test_type and r.accuracy_class == accuracy_class]


# --- Parser ---

@pytest.mark.parametrize("condition, inside, outside", [
    ("0<=m<=500e", [0, 250, 500], [500.0001, 501]),
    ("500e<m<=2000e", [500.0001, 2000], [500, 2000.0001]),
    ("200000e<m", [200000.5, 1e9], [200000, 0]),
    ("m<=50e", [0, 50], [50.1]),
    (" 0 <= m <= 500e ", [0, 500], [501]),   # whitespace as typed in the admin form
    ("0e<=m<500e", [0, 499.9], [500]),
])
def test_parse_condition_bands(condition, inside, outside):
    band = parse_condition(condition)
    assert all(band.contains(m) for m in inside)
    assert not any(band.contains(m) for m in outside)


@pytest.mark.parametrize("condition", ["Always", "always", " ALWAYS "])
def test_parse_condition_always(condition):
    band = parse_condition(condition)
    assert band.contains(0) and band.contains(1e12)


@pytest.mark.parametrize("condition", [
    "", "m", "0<=x<=500e", "500e>=m", "0<=m<=500e<=1000e", "__import__('os')", "1e3<m",
    "2000e<m<=500e", "m<=-5e", None,
])
def test_parse_condition_rejects_invalid(condition):
    with pytest.raises(RuleEngineException):
        parse_condition(condition)


# --- Seeded Table 6 bands, Class III, e = 0.01 kg ---

@pytest.mark.parametrize("load, expected_rule, expected_mpe_e", [
    (5.00, "R76-ACC-III-001", 0.5),   # m = 500e   -> 0.5e (upper bound inclusive)
    (5.01, "R76-ACC-III-002", 1.0),   # m = 501e   -> 1e
    (20.00, "R76-ACC-III-002", 1.0),  # m = 2000e  -> 1e (upper bound inclusive)
    (20.01, "R76-ACC-III-003", 1.5),  # m = 2001e  -> 1.5e
])
def test_class_iii_band_boundaries(load, expected_rule, expected_mpe_e):
    inst = MockInstrument()
    res = calculate("Accuracy", inst, [{"sequence": 1, "test_load": load, "indicated_value": load, "unit": "kg"}], seeded_rules("Accuracy", "III"))
    row = res["calculated_values"]["measurements"][0]
    assert row["rule_id"] == expected_rule
    assert row["mpe_multiplier"] == expected_mpe_e
    assert row["mpe_limit"] == pytest.approx(expected_mpe_e * 0.01)
    assert row["band"] == next(r.condition for r in seeded_rules("Accuracy", "III") if r.rule_id == expected_rule)


def test_class_iii_limit_applied_per_band():
    inst = MockInstrument()
    rules = seeded_rules("Accuracy", "III")
    measurements = [
        {"sequence": 1, "test_load": 5.00, "indicated_value": 5.005, "unit": "kg"},    # 0.005 <= 0.5e  PASS
        {"sequence": 2, "test_load": 5.01, "indicated_value": 5.02, "unit": "kg"},     # 0.010 <= 1e    PASS
        {"sequence": 3, "test_load": 20.01, "indicated_value": 20.025, "unit": "kg"},  # 0.015 <= 1.5e  PASS
    ]
    res = calculate("Accuracy", inst, measurements, rules)
    assert res["pass_fail"] == "PASS"
    assert res["applicable_rules"] == ["R76-ACC-III-001", "R76-ACC-III-002", "R76-ACC-III-003"]
    assert res["permissible_limit"] is None  # mixed bands

    measurements[0]["indicated_value"] = 5.006  # 0.006 > 0.5e at 500e
    res = calculate("Accuracy", inst, measurements, rules)
    assert res["pass_fail"] == "FAIL"
    assert [m["passed"] for m in res["calculated_values"]["measurements"]] == [False, True, True]


def test_load_above_class_range_raises():
    inst = MockInstrument()
    with pytest.raises(RuleEngineException, match="outside every configured MPE band"):
        calculate("Accuracy", inst, [{"sequence": 1, "test_load": 100.01, "indicated_value": 100.01, "unit": "kg"}], seeded_rules("Accuracy", "III"))


def test_repeatability_uses_band_of_test_load():
    inst = MockInstrument()
    rules = seeded_rules("Repeatability", "III")
    # 15 kg = 1500e -> 1e = 0.01 kg
    res = calculate("Repeatability", inst, [{"test_load": 15.0, "indicated_value": v} for v in (15.0, 15.01, 15.005)], rules)
    assert res["pass_fail"] == "PASS"
    assert res["calculated_values"]["rule_id"] == "R76-REP-III-002"
    # 4 kg = 400e -> 0.5e = 0.005 kg, same spread now fails
    res = calculate("Repeatability", inst, [{"test_load": 4.0, "indicated_value": v} for v in (4.0, 4.01)], rules)
    assert res["pass_fail"] == "FAIL"
    assert res["calculated_values"]["rule_id"] == "R76-REP-III-001"


def test_eccentricity_and_tare_select_bands():
    inst = MockInstrument()
    ecc = calculate("Eccentricity", inst, [{"position": "Center", "test_load": 10.0, "indicated_value": 10.01}], seeded_rules("Eccentricity", "III"))
    assert ecc["calculated_values"]["positions"][0]["rule_id"] == "R76-ECC-III-002"
    assert ecc["pass_fail"] == "PASS"
    tare = calculate("Tare", inst, [{"test_load": 3.0, "indicated_value": 3.005}], seeded_rules("Tare", "III"))
    assert tare["calculated_values"]["measurements"][0]["rule_id"] == "R76-TAR-III-001"
    assert tare["pass_fail"] == "PASS"


def test_zero_uses_flat_quarter_e():
    inst = MockInstrument()
    rules = seeded_rules("Zero", "III")
    assert [r.condition for r in rules] == ["Always"]
    assert calculate("Zero", inst, [{"test_load": 0.0, "indicated_value": 0.0025}], rules)["pass_fail"] == "PASS"
    assert calculate("Zero", inst, [{"test_load": 0.0, "indicated_value": 0.003}], rules)["pass_fail"] == "FAIL"


def test_class_ii_bands():
    inst = MockInstrument(verification_interval=0.001, accuracy_class="II")
    rules = seeded_rules("Accuracy", "II")
    rule, _ = select_rule(rules, 5.0, 0.001)    # 5000e
    assert rule.rule_id == "R76-ACC-II-001"
    rule, _ = select_rule(rules, 5.001, 0.001)  # 5001e
    assert rule.rule_id == "R76-ACC-II-002"


def test_seeded_bands_do_not_overlap_or_gap():
    # Every class/test band set is contiguous from 0 and non-overlapping (select_rule raises on overlap)
    for r in build_table6_rules():
        parse_condition(r.condition)
    for cls, e_top in [("I", 300000), ("II", 100000), ("III", 10000), ("IIII", 1000)]:
        rules = seeded_rules("Accuracy", cls)
        for m in [0, 0.5, 50, 50.5, 200, 200.5, 500, 500.5, 2000, 2000.5, 5000, 5000.5, 20000, 20000.5, 50000, 50000.5]:
            if m <= e_top:
                select_rule(rules, m, 1.0)
