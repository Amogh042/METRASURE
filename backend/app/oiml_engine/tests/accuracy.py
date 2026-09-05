from typing import List, Dict, Any, Tuple
from app.db.models import Instrument

def get_mpe(load: float, e: float, accuracy_class: str) -> float:
    """
    Calculate Maximum Permissible Error (mpe) based on OIML R-76 Table 6 (TODO: Verify Exact Ranges).
    Using a placeholder approximation based on the load in terms of verification scale interval (e).
    
    TODO: Integrate exact table for Class I, II, III, IIII.
    """
    m = load / e if e > 0 else 0
    
    # Placeholder logic for Class III (most common)
    if accuracy_class == "III":
        if m <= 500:
            return 1.0 * e
        elif m <= 2000:
            return 2.0 * e
        elif m <= 10000:
            return 3.0 * e
        else:
            return 3.0 * e # Fallback
            
    # Default fallback if class is unhandled
    return 1.0 * e

def evaluate_accuracy(instrument: Instrument, measurements: List[Dict[str, float]]) -> Tuple[bool, str, Dict[str, Any], str]:
    """
    Evaluates Accuracy (Error of Indication) test.
    Measurements should have 'load_applied', 'indication'.
    """
    overall_pass = True
    calculated_results = []
    
    e = instrument.verification_scale_interval_e
    
    for m in measurements:
        load = m.get('load_applied', 0.0)
        indication = m.get('indication', 0.0)
        error = indication - load
        
        mpe = get_mpe(load, e, instrument.accuracy_class)
        
        passed = abs(error) <= mpe
        if not passed:
            overall_pass = False
            
        calculated_results.append({
            "load_applied": load,
            "indication": indication,
            "error": error,
            "mpe": mpe,
            "passed": passed
        })
        
    explanation = "All measurement errors within Maximum Permissible Error (MPE)." if overall_pass else "One or more measurement errors exceeded Maximum Permissible Error (MPE)."
    
    return overall_pass, "OIML R-76 (2006) - Accuracy Rule v1.0", {"measurements": calculated_results}, explanation
