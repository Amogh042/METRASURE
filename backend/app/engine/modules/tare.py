from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException, rule_summary
from app.engine.conditions import select_rule, band_details

def evaluate_tare(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rules: List[OIMLRule]) -> Dict[str, Any]:
    """
    Evaluates Tare weighing.
    Source Reference: OIML R-76-1 (2006) 3.5.3.3 Tare-weighing device
    Rule: The MPE applies to the net load for any possible tare value.
    The MPE band is selected per measurement from m = net load / e (Table 6).
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Tare test.")
        
    e_interval = instrument.verification_interval
    
    calculated_values = []
    rules_used = []
    overall_pass = True
    
    for idx, m in enumerate(measurements):
        net_load = m.get("test_load")
        indication = m.get("indicated_value")
        
        if net_load is None or indication is None:
            raise RuleEngineException(f"Missing net load or indication at measurement {idx}.")
        
        rule, m_value = select_rule(applicable_rules, net_load, e_interval)
        band = band_details(rule, m_value, e_interval)
        rules_used.append(rule)
            
        error = indication - net_load
        passed = round(abs(error), 5) <= round(band["mpe_limit"], 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "sequence": m.get("sequence", idx + 1),
            "net_load": net_load,
            "indication": indication,
            "error": error,
            **band,
            "passed": passed
        })

    explanation = "All tare net load errors within MPE." if overall_pass else "One or more tare net load errors exceeded MPE."

    return {
        "calculated_values": {"measurements": calculated_values},
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        **rule_summary(rules_used, [c["mpe_limit"] for c in calculated_values], "OIML R-76-1 (2006) 3.5.3.3"),
    }
