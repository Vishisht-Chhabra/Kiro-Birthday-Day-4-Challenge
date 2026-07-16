"""Property-based test for division-by-zero handling.

Uses Hypothesis to verify that dividing by zero never yields a numeric result:
at the engine level ``evaluate`` returns the divide-by-zero error indicator,
and at the state level ``press_equals`` transitions into ERROR mode showing the
fixed divide-by-zero message and retains that state until a clear or delete.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Err, EvalError, Ok, Operator, evaluate
from calculator.calculator_state import CalculatorState, Mode

# Finite left operands spanning negatives, zero, decimals, and large
# magnitudes, kept away from float overflow so parsing/formatting stay well
# defined.
left_operands = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-1e150,
    max_value=1e150,
)

# String forms of a zero divisor that a user could enter on the Display.
zero_divisor_strings = st.sampled_from(["0", "0.", "0.0", "00", "0.00", "000"])

# Left operand strings a user could have entered as the first operand.
left_operand_strings = st.sampled_from(
    ["0", "1", "7", "42", "0.5", "3.14", "123456789", "999999999999999", "10"]
)


# Feature: calculator-app, Property 8: Division by zero yields an error, never a numeric result
@settings(max_examples=200)
@given(left=left_operands, divisor_string=zero_divisor_strings)
def test_property_8_engine_division_by_zero_is_error(left, divisor_string):
    """Engine level: for any left operand, dividing by a zero divisor returns
    the divide-by-zero error indicator and never a numeric ``Ok`` result.

    Validates: Requirements 3.1, 3.2, 3.3
    """
    result = evaluate(left, Operator.DIVIDE, float(divisor_string))

    assert not isinstance(result, Ok)
    assert isinstance(result, Err)
    assert result.error is EvalError.DIVIDE_BY_ZERO


# Feature: calculator-app, Property 8: Division by zero yields an error, never a numeric result
@settings(max_examples=200)
@given(left_string=left_operand_strings, divisor_string=zero_divisor_strings)
def test_property_8_state_division_by_zero_enters_error_mode(
    left_string, divisor_string
):
    """State level: a complete division expression whose divisor is zero, after
    pressing equals, enters ERROR mode, shows the fixed divide-by-zero message,
    suppresses any numeric result, and retains the error state until a clear or
    delete action.

    Validates: Requirements 3.1, 3.2, 3.3
    """
    state = CalculatorState(
        left=left_string,
        operator=Operator.DIVIDE,
        right=divisor_string,
        mode=Mode.EDITING,
    )

    after_equals = state.press_equals()

    # ERROR mode with the fixed message, never a numeric RESULT.
    assert after_equals.mode is Mode.ERROR
    assert after_equals.mode is not Mode.RESULT
    assert after_equals.display_string() == "Cannot divide by zero"

    # The error state is retained across a non-recovery transition such as
    # pressing an operator (only clear or a digit/delete recover).
    assert after_equals.press_operator(Operator.ADD).mode is Mode.ERROR
    assert (
        after_equals.press_operator(Operator.ADD).display_string()
        == "Cannot divide by zero"
    )
