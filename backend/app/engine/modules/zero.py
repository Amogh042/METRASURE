from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException, rule_summary
from app.engine.conditions import select_rule, band_details

def evaluate_zero(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rules: List[OIMLRule]) -> Dict[str, Any]:
    """
    Evaluates Zero Indication / Error of Zero.
    Source Reference: OIML R-76-1 (2006) 4.5.2 Error of zero indication
    Rule: After zero-setting, the effect of zero deviation shall not exceed 0.25e.
    The limit comes from the configured rule (normally a single "Always" rule of 0.25e).
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Zero test.")
        
    e_interval = instrument.verification_interval
    
    calculated_values = []
    rules_used = []
    overall_pass = True
    
    for idx, m in enumerate(measurements):
        indication = m.get("indicated_value")
        # Load should be 0 for zero test
        load = m.get("test_load") or 0.0
        
        if indication is None:
            raise RuleEngineException(f"Missing indication at measurement {idx}.")
        
        rule, m_value = select_rule(applicable_rules, load, e_interval)
        band = band_details(rule, m_value, e_interval)
        rules_used.append(rule)
            
        error = indication - load
        passed = round(abs(error), 5) <= round(band["mpe_limit"], 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "sequence": m.get("sequence", idx + 1),
            "load": load,
            "indication": indication,
            "error": error,
            **band,
            "passed": passed
        })

    explanation = "Zero indication errors within MPE (0.25e limit typical)." if overall_pass else "Zero indication error exceeded MPE."

    return {
        "calculated_values": {"measurements": calculated_values},
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        **rule_summary(rules_used, [c["mpe_limit"] for c in calculated_values], "OIML R-76-1 (2006) 4.5.2"),
    }
