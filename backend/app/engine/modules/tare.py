from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException

def evaluate_tare(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rule: OIMLRule) -> Dict[str, Any]:
    """
    Evaluates Tare weighing.
    Source Reference: OIML R-76-1 (2006) 3.5.3.3 Tare-weighing device
    Rule: The MPE applies to the net load for any possible tare value.
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Tare test.")
        
    e_interval = instrument.verification_interval
    mpe_limit = applicable_rule.permissible_error * e_interval
    
    calculated_values = []
    overall_pass = True
    
    for idx, m in enumerate(measurements):
        net_load = m.get("test_load")
        indication = m.get("indicated_value")
        
        if net_load is None or indication is None:
            raise RuleEngineException(f"Missing net load or indication at measurement {idx}.")
            
        error = indication - net_load
        passed = round(abs(error), 5) <= round(mpe_limit, 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "net_load": net_load,
            "indication": indication,
            "error": error,
            "mpe_limit": mpe_limit,
            "passed": passed
        })

    explanation = "All tare net load errors within MPE." if overall_pass else "One or more tare net load errors exceeded MPE."

    return {
        "calculated_values": {"measurements": calculated_values},
        "applicable_rule": applicable_rule.rule_id,
        "permissible_limit": mpe_limit,
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        "source_reference": applicable_rule.source_reference or "OIML R-76-1 (2006) 3.5.3.3",
        "rule_version": applicable_rule.standard_version
    }
