from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException

def evaluate_zero(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rule: OIMLRule) -> Dict[str, Any]:
    """
    Evaluates Zero Indication / Error of Zero.
    Source Reference: OIML R-76-1 (2006) 4.5.2 Error of zero indication
    Rule: After zero-setting, the effect of zero deviation shall not exceed 0.25e.
    
    TODO: The applicable_rule config should define 0.25e limit for this test.
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Zero test.")
        
    e_interval = instrument.verification_interval
    mpe_limit = applicable_rule.permissible_error * e_interval
    
    calculated_values = []
    overall_pass = True
    
    for idx, m in enumerate(measurements):
        indication = m.get("indicated_value")
        # Load should be 0 for zero test
        load = m.get("test_load", 0.0)
        
        if indication is None:
            raise RuleEngineException(f"Missing indication at measurement {idx}.")
            
        error = indication - load
        passed = round(abs(error), 5) <= round(mpe_limit, 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "load": load,
            "indication": indication,
            "error": error,
            "mpe_limit": mpe_limit,
            "passed": passed
        })

    explanation = "Zero indication errors within MPE (0.25e limit typical)." if overall_pass else "Zero indication error exceeded MPE."

    return {
        "calculated_values": {"measurements": calculated_values},
        "applicable_rule": applicable_rule.rule_id,
        "permissible_limit": mpe_limit,
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        "source_reference": applicable_rule.source_reference or "OIML R-76-1 (2006) 4.5.2",
        "rule_version": applicable_rule.standard_version
    }
