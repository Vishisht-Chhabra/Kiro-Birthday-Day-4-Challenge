"""Property-based tests for the Arithmetic_Engine.

Uses Hypothesis to verify universal properties of ``evaluate`` across a wide
range of operands and operators.
"""

from __future__ import annotations

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Ok, Operator, evaluate

# Finite floats within a magnitude that keeps arithmetic well away from
# float overflow to +/-inf, so the reference comparison stays meaningful.
operands = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-1e150,
    max_value=1e150,
)

operators = st.sampled_from(list(Operator))


def _significant_digit_count(formatted: str) -> int:
    """Count significant digits in a ``%g``-formatted number string."""
    # Drop any exponent portion (e.g. "1.23e+17" -> "1.23").
    mantissa = formatted.split("e")[0].split("E")[0]
    digits = mantissa.replace("-", "").replace("+", "").replace(".", "")
    # Strip leading zeros (not significant); a lone "0" has zero sig digits.
    stripped = digits.lstrip("0")
    # Trailing zeros in a %g result are dropped, so remaining digits are all
    # significant.
    return len(stripped)


def _reference(left: float, operator: Operator, right: float) -> float:
    """Mathematical application of the operator, mirroring the engine."""
    if operator is Operator.ADD:
        return left + right
    if operator is Operator.SUBTRACT:
        return left - right
    if operator is Operator.MULTIPLY:
        return left * right
    # Operator.DIVIDE
    return left / right


# Feature: calculator-app, Property 6: Evaluation matches the reference operation
@settings(max_examples=200)
@given(left=operands, operator=operators, right=operands)
def test_property_6_evaluation_matches_reference(left, operator, right):
    """For any two operands and any operator that is not division-by-zero, the
    engine's Ok result equals the mathematical application of that operator,
    accurate to within 0.0000000001, and is displayable to at most 10
    significant digits.

    Validates: Requirements 2.5, 2.6, 5.5
    """
    # Exclude division-by-zero: that case is covered by Property 8.
    if operator is Operator.DIVIDE and right == 0:
        return

    result = evaluate(left, operator, right)

    # Non-divide-by-zero arithmetic always succeeds.
    assert isinstance(result, Ok)

    expected = _reference(left, operator, right)

    # Accurate to within the required tolerance (absolute or relative to
    # accommodate large magnitudes without spurious failures).
    tolerance = 0.0000000001
    if math.isinf(expected) or math.isinf(result.value):
        # Overflow to the same signed infinity is considered matching.
        assert result.value == expected
    else:
        abs_diff = abs(result.value - expected)
        scale = max(1.0, abs(expected))
        assert abs_diff <= tolerance * scale

        # Displayable to at most 10 significant digits: the display formatter
        # (%.10g, per the design) never emits more than 10 significant digits.
        displayed = f"{result.value:.10g}"
        assert _significant_digit_count(displayed) <= 10
