from typing import List, Dict, Any, Optional
from app.db.models import Instrument, OIMLRule

class RuleEngineException(Exception):
    pass

def calculate(test_type: str, instrument: Instrument, measurements: List[Dict[str, Any]], applicable_rule: Optional[OIMLRule]) -> Dict[str, Any]:
    """
    Main entry point for the OIML Rule Engine.
    Routes the calculation to the specific test module.
    
    Args:
        test_type: String identifier of the test (e.g., 'Accuracy', 'Repeatability')
        instrument: Instrument ORM object
        measurements: List of dictionaries containing raw measurement data
        applicable_rule: OIMLRule ORM object configured in the database
        
    Returns:
        Dictionary containing calculated values, pass/fail status, and auditable explanation.
    """
    if not applicable_rule:
        raise RuleEngineException("Missing applicable rule configuration for this test.")
        
    if not instrument.accuracy_class:
        raise RuleEngineException("Instrument is missing an accuracy class.")

    # Import modules here to avoid circular imports if needed, though they are standalone
    from .modules.accuracy import evaluate_accuracy
    from .modules.repeatability import evaluate_repeatability
    from .modules.eccentric import evaluate_eccentric
    from .modules.zero import evaluate_zero
    from .modules.tare import evaluate_tare
    
    test_type_upper = test_type.upper()
    
    if test_type_upper == "ACCURACY":
        return evaluate_accuracy(instrument, measurements, applicable_rule)
    elif test_type_upper == "REPEATABILITY":
        return evaluate_repeatability(instrument, measurements, applicable_rule)
    elif test_type_upper == "ECCENTRICITY":
        return evaluate_eccentric(instrument, measurements, applicable_rule)
    elif test_type_upper == "ZERO":
        return evaluate_zero(instrument, measurements, applicable_rule)
    elif test_type_upper == "TARE":
        return evaluate_tare(instrument, measurements, applicable_rule)
    else:
        raise RuleEngineException(f"Unsupported test type: {test_type}")
