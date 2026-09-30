from typing import List, Dict, Any, Optional
from app.db.models import Instrument, OIMLRule

class RuleEngineException(Exception):
    pass

def calculate(test_type: str, instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rules: Optional[List[OIMLRule]]) -> Dict[str, Any]:
    """
    Main entry point for the OIML Rule Engine.
    Routes the calculation to the specific test module.
    
    Args:
        test_type: String identifier of the test (e.g., 'Accuracy', 'Repeatability')
        instrument: Instrument ORM object
        measurements: List of dictionaries containing raw measurement data
        applicable_rules: All enabled OIMLRule rows for this test type and accuracy class.
            Each rule's `condition` defines the load band (m = load / e) it applies to;
            the engine selects the matching band per measurement (OIML R-76-1 Table 6).
        
    Returns:
        Dictionary containing calculated values, pass/fail status, and auditable explanation.
    """
    if not applicable_rules:
        raise RuleEngineException("Missing applicable rule configuration for this test.")
        
    if not instrument.accuracy_class:
        raise RuleEngineException("Instrument is missing an accuracy class.")

    if not instrument.verification_interval or instrument.verification_interval <= 0:
        raise RuleEngineException("Invalid instrument verification_interval. Must be > 0.")

    # Import modules here to avoid circular imports if needed, though they are standalone
    from .modules.accuracy import evaluate_accuracy
    from .modules.repeatability import evaluate_repeatability
    from .modules.eccentric import evaluate_eccentric
    from .modules.zero import evaluate_zero
    from .modules.tare import evaluate_tare
    
    test_type_upper = test_type.upper()
    
    if test_type_upper == "ACCURACY":
        return evaluate_accuracy(instrument, measurements, applicable_rules)
    elif test_type_upper == "REPEATABILITY":
        return evaluate_repeatability(instrument, measurements, applicable_rules)
    elif test_type_upper == "ECCENTRICITY":
        return evaluate_eccentric(instrument, measurements, applicable_rules)
    elif test_type_upper == "ZERO":
        return evaluate_zero(instrument, measurements, applicable_rules)
    elif test_type_upper == "TARE":
        return evaluate_tare(instrument, measurements, applicable_rules)
    else:
        raise RuleEngineException(f"Unsupported test type: {test_type}")

def rule_summary(rules_used: List[OIMLRule], mpe_limits: List[float], default_source: str) -> Dict[str, Any]:
    """Top-level audit fields for the rules actually applied (in first-use order)."""
    unique = list({r.rule_id: r for r in rules_used}.values())
    distinct_limits = {round(x, 9) for x in mpe_limits}
    return {
        "applicable_rule": ", ".join(r.rule_id for r in unique),
        "applicable_rules": [r.rule_id for r in unique],
        # Single value when every measurement fell in the same band, otherwise see per-measurement mpe_limit
        "permissible_limit": distinct_limits.pop() if len(distinct_limits) == 1 else None,
        "source_reference": (unique[0].source_reference or default_source) if unique else default_source,
        "rule_version": unique[0].standard_version if unique else None,
    }
