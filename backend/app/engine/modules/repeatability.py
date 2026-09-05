from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException

def evaluate_repeatability(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rule: OIMLRule) -> Dict[str, Any]:
    """
    Evaluates the Repeatability test.
    Source Reference: OIML R-76-1 (2006) 3.6.1 Repeatability
    Rule: The difference between any two results of several weighings of the same load 
    shall not be greater than the absolute value of the maximum permissible error (MPE).
    
    TODO: Integrate specific MPE step lookup for the given load.
    Currently using configured applicable_rule's permissible_error.
    """
    if not measurements or len(measurements) < 2:
        raise RuleEngineException("Repeatability test requires at least 2 measurements.")
        
    e_interval = instrument.verification_interval
    if e_interval <= 0:
        raise RuleEngineException("Invalid instrument verification_interval. Must be > 0.")
        
    mpe_limit = applicable_rule.permissible_error * e_interval
    
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
        
    max_indication = max(indications)
    min_indication = min(indications)
    max_difference = max_indication - min_indication
    
    passed = max_difference <= mpe_limit
    
    calculated_values = {
        "load": base_load,
        "max_indication": max_indication,
        "min_indication": min_indication,
        "max_difference": max_difference,
        "mpe_limit": mpe_limit,
        "measurements": indications
    }
    
    if passed:
        explanation = f"Max difference ({max_difference}) is within the MPE limit ({mpe_limit})."
    else:
        explanation = f"Max difference ({max_difference}) exceeds the MPE limit ({mpe_limit})."

    return {
        "calculated_values": calculated_values,
        "applicable_rule": applicable_rule.rule_id,
        "permissible_limit": mpe_limit,
        "pass_fail": "PASS" if passed else "FAIL",
        "explanation": explanation,
        "source_reference": applicable_rule.source_reference or "OIML R-76-1 (2006) 3.6.1",
        "rule_version": applicable_rule.standard_version
    }
