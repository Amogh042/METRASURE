"""
Strict parser for OIMLRule.condition strings (no eval).

Supported forms, where m = load / e (whitespace ignored):
    "Always"
    "0<=m<=500e"        lower and upper bound
    "500e<m<=2000e"
    "200000e<m"         lower bound only (open-ended)
    "m<=500e"           upper bound only
Bounds may be written with or without the trailing "e" (e.g. "0" or "0e").
"""
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple
from app.engine.core import RuleEngineException

_NUM = r"(\d+(?:\.\d+)?)e?"
_CONDITION_RE = re.compile(rf"^(?:{_NUM}(<=|<))?m(?:(<=|<){_NUM})?$")

# m is load / e; round away float noise such as 5.01 / 0.01 = 500.99999999999994
_M_PRECISION = 6


@dataclass(frozen=True)
class Band:
    lower: Optional[float] = None
    lower_inclusive: bool = False
    upper: Optional[float] = None
    upper_inclusive: bool = False

    def contains(self, m: float) -> bool:
        m = round(m, _M_PRECISION)
        if self.lower is not None:
            if m < self.lower or (m == self.lower and not self.lower_inclusive):
                return False
        if self.upper is not None:
            if m > self.upper or (m == self.upper and not self.upper_inclusive):
                return False
        return True


ALWAYS = Band()


def parse_condition(condition: Optional[str]) -> Band:
    if condition is None:
        raise RuleEngineException("Rule condition is missing.")
    text = re.sub(r"\s+", "", condition)
    if text.lower() == "always":
        return ALWAYS

    match = _CONDITION_RE.match(text)
    if not match:
        raise RuleEngineException(
            f"Invalid rule condition '{condition}'. Expected 'Always' or a band such as '0<=m<=500e', '500e<m<=2000e' or '200000e<m'."
        )
    lower, lower_op, upper_op, upper = match.groups()
    if lower is None and upper is None:
        raise RuleEngineException(f"Invalid rule condition '{condition}': at least one bound is required.")

    band = Band(
        lower=float(lower) if lower is not None else None,
        lower_inclusive=lower_op == "<=",
        upper=float(upper) if upper is not None else None,
        upper_inclusive=upper_op == "<=",
    )
    if band.lower is not None and band.upper is not None and band.lower > band.upper:
        raise RuleEngineException(f"Invalid rule condition '{condition}': lower bound exceeds upper bound.")
    return band


def select_rule(rules: Iterable[Any], load: float, e_interval: float) -> Tuple[Any, float]:
    """
    Returns (rule, m) for the single rule whose condition band contains m = load / e.
    Raises RuleEngineException if no band, or more than one band, matches.
    """
    rules = list(rules)
    m = load / e_interval
    matches = [r for r in rules if parse_condition(r.condition).contains(m)]

    if not matches:
        conditions = ", ".join(r.condition for r in rules)
        raise RuleEngineException(
            f"Load {load:g} (m = {m:g}e) is outside every configured MPE band ({conditions}). "
            "Check the load does not exceed the instrument's range for this accuracy class."
        )
    if len(matches) > 1:
        ids = ", ".join(r.rule_id for r in matches)
        raise RuleEngineException(f"Overlapping rule bands for m = {m:g}e: {ids}. Fix the rule configuration.")
    return matches[0], m


def band_details(rule: Any, m: float, e_interval: float) -> dict:
    """Per-measurement audit fields describing which band was applied."""
    return {
        "rule_id": rule.rule_id,
        "band": rule.condition,
        "m": round(m, _M_PRECISION),
        "mpe_multiplier": rule.permissible_error,
        "mpe_limit": rule.permissible_error * e_interval,
    }
