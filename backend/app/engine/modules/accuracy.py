from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException, rule_summary
from app.engine.conditions import select_rule, band_details

def evaluate_accuracy(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rules: List[OIMLRule]) -> Dict[str, Any]:
    """
    Evaluates the Accuracy / error of indication test.
    Source Reference: OIML R-76-1 (2006) 3.5.1 Errors of indication, Table 6 (initial verification MPEs)
    
    The MPE is stepped by load: for each measurement, m = load / e selects the rule whose
    configured condition band contains m, and that rule's permissible_error (in e) is applied.
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Accuracy test.")
        
    e_interval = instrument.verification_interval
    
    calculated_values = []
    rules_used = []
    overall_pass = True
    
    for idx, m in enumerate(measurements):
        load = m.get("test_load")
        indication = m.get("indicated_value")
        unit = m.get("unit")
        
        if load is None or indication is None:
            raise RuleEngineException(f"Missing load or indication at measurement index {idx}.")
        if load < 0:
            raise RuleEngineException(f"Invalid negative load ({load}) at measurement index {idx}.")
        if unit != instrument.unit:
            raise RuleEngineException(f"Measurement unit ({unit}) does not match instrument unit ({instrument.unit}).")
        
        rule, m_value = select_rule(applicable_rules, load, e_interval)
        band = band_details(rule, m_value, e_interval)
        rules_used.append(rule)
            
        error = indication - load
        
        # OIML R-76: Absolute error must be <= MPE
        passed = round(abs(error), 5) <= round(band["mpe_limit"], 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "sequence": m.get("sequence", idx + 1),
            "test_load": load,
            "indicated_value": indication,
            "error": error,
            **band,
            "passed": passed
        })

    explanation = "All errors of indication were within Maximum Permissible Error (MPE)." if overall_pass else "One or more errors of indication exceeded the Maximum Permissible Error (MPE)."

    return {
        "calculated_values": {"measurements": calculated_values},
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        **rule_summary(rules_used, [c["mpe_limit"] for c in calculated_values], "OIML R-76-1 (2006) 3.5.1"),
    }
