from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException, rule_summary
from app.engine.conditions import select_rule, band_details

def evaluate_eccentric(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rules: List[OIMLRule]) -> Dict[str, Any]:
    """
    Evaluates the Eccentric loading test.
    Source Reference: OIML R-76-1 (2006) 3.6.2 Eccentric loading
    Rule: The indications for different positions of a load shall meet the maximum permissible errors,
    when the instrument is tested according to 3.6.2.1 - 3.6.2.4.
    The MPE band is selected per position from m = load / e (Table 6).
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Eccentricity test.")
        
    e_interval = instrument.verification_interval
    
    calculated_values = []
    rules_used = []
    overall_pass = True
    
    for idx, m in enumerate(measurements):
        load = m.get("test_load")
        indication = m.get("indicated_value")
        position = m.get("position")
        
        if load is None or indication is None:
            raise RuleEngineException(f"Missing load or indication at measurement {idx}.")
        if not position:
            raise RuleEngineException(f"Missing position (e.g. Center, Front-Left) at measurement {idx}.")
        
        rule, m_value = select_rule(applicable_rules, load, e_interval)
        band = band_details(rule, m_value, e_interval)
        rules_used.append(rule)
            
        error = indication - load
        passed = round(abs(error), 5) <= round(band["mpe_limit"], 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "position": position,
            "load": load,
            "indication": indication,
            "error": error,
            **band,
            "passed": passed
        })

    explanation = "All eccentric loading errors within MPE." if overall_pass else "One or more eccentric positions exceeded MPE."

    return {
        "calculated_values": {"positions": calculated_values},
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        **rule_summary(rules_used, [c["mpe_limit"] for c in calculated_values], "OIML R-76-1 (2006) 3.6.2"),
    }
