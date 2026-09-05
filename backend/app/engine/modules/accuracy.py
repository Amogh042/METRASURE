from typing import List, Dict, Any
from app.db.models import Instrument, OIMLRule
from app.engine.core import RuleEngineException

def evaluate_accuracy(instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rule: OIMLRule) -> Dict[str, Any]:
    """
    Evaluates the Accuracy / error of indication test.
    Source Reference: OIML R-76-1 (2006) 3.5.1 Errors of indication
    
    TODO: OIML R-76 Table 6 specifies stepped MPEs depending on the load `m` (e.g., 1e, 2e, 3e).
    Since the exact table isn't fully verified here, we rely on the `applicable_rule` passed 
    to provide the permissible_error multiplier for `e` dynamically based on its configured condition.
    """
    if not measurements:
        raise RuleEngineException("Missing measurements for Accuracy test.")
        
    e_interval = instrument.verification_interval
    if e_interval <= 0:
        raise RuleEngineException("Invalid instrument verification_interval. Must be > 0.")
        
    # TODO: Multiplier parsing based on applicable_rule condition.
    # Currently assuming applicable_rule provides a flat multiplier for MVP.
    mpe_limit = applicable_rule.permissible_error * e_interval
    
    calculated_values = []
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
            
        error = indication - load
        
        # OIML R-76: Absolute error must be <= MPE
        passed = round(abs(error), 5) <= round(mpe_limit, 5)
        
        if not passed:
            overall_pass = False
            
        calculated_values.append({
            "sequence": m.get("sequence", idx + 1),
            "test_load": load,
            "indicated_value": indication,
            "error": error,
            "mpe_limit": mpe_limit,
            "passed": passed
        })

    explanation = "All errors of indication were within Maximum Permissible Error (MPE)." if overall_pass else "One or more errors of indication exceeded the Maximum Permissible Error (MPE)."

    return {
        "calculated_values": {"measurements": calculated_values},
        "applicable_rule": applicable_rule.rule_id,
        "permissible_limit": mpe_limit,
        "pass_fail": "PASS" if overall_pass else "FAIL",
        "explanation": explanation,
        "source_reference": applicable_rule.source_reference or "OIML R-76-1 (2006) 3.5.1",
        "rule_version": applicable_rule.standard_version
    }
