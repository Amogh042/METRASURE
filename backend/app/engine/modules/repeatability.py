from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException, rule_summary
from app.engine.conditions import select_rule, band_details

def evaluate_repeatability(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rules: List[OIMLRule]) -> Dict[str, Any]:
    """
    Evaluates the Repeatability test.
    Source Reference: OIML R-76-1 (2006) 3.6.1 Repeatability
    Rule: The difference between any two results of several weighings of the same load 
    shall not be greater than the absolute value of the maximum permissible error (MPE).
    
    The MPE is the Table 6 band of the (common) test load, selected from m = load / e.
    """
    if not measurements or len(measurements) < 2:
        raise RuleEngineException("Repeatability test requires at least 2 measurements.")
        
    e_interval = instrument.verification_interval
    
    # Ensure all measurements are at the same load (ideally ~50% Max or near Max)
    base_load = measurements[0].get("test_load")
    indications = []
    
    for idx, m in enumerate(measurements):
        load = m.get("test_load")
        indication = m.get("indicated_value")
        
        if load is None or indication is None:
            raise RuleEngineException(f"Missing load or indication at measurement index {idx}.")
        if load != base_load:
            raise RuleEngineException(f"Repeatability test loads must be identical. Found {load} != {base_load}.")
            
        indications.append(indication)
        
    rule, m_value = select_rule(applicable_rules, base_load, e_interval)
    band = band_details(rule, m_value, e_interval)
    mpe_limit = band["mpe_limit"]
        
    max_indication = max(indications)
    min_indication = min(indications)
    max_difference = max_indication - min_indication
    
    passed = round(max_difference, 5) <= round(mpe_limit, 5)

    calculated_values = {
        "load": base_load,
        "max_indication": max_indication,
        "min_indication": min_indication,
        "max_difference": max_difference,
        **band,
        "measurements": indications
    }
    
    if passed:
        explanation = f"Max difference ({max_difference:.4f}) is within the MPE limit ({mpe_limit:.4f}, band {rule.condition})."
    else:
        explanation = f"Max difference ({max_difference:.4f}) exceeds the MPE limit ({mpe_limit:.4f}, band {rule.condition})."

    return {
        "calculated_values": calculated_values,
        "pass_fail": "PASS" if passed else "FAIL",
        "explanation": explanation,
        **rule_summary([rule], [mpe_limit], "OIML R-76-1 (2006) 3.6.1"),
    }
