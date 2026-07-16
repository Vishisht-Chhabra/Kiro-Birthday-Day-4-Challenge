"""Property-based test for starting a fresh expression from a terminal display.

Uses Hypothesis to verify Property 3: pressing a digit while the calculator is
in RESULT mode (a bare previous result) or ERROR mode (a division-by-zero
message) discards the terminal display and starts a new EDITING expression
containing exactly that single digit.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.calculator_state import CalculatorState, Mode

DIGITS = "0123456789"


@st.composite
def result_operands(draw) -> str:
    """Generate a formatted result string as ``press_equals`` would store it.

    Covers integers, negatives, decimals, and large magnitudes, formatted the
    same way the state stores a completed result (at most 10 significant
    digits).
    """

    value = draw(
        st.floats(
            allow_nan=False,
            allow_infinity=False,
            min_value=-1e12,
            max_value=1e12,
        )
    )
    return f"{value:.10g}"


@st.composite
def terminal_states(draw) -> CalculatorState:
    """Generate reachable RESULT and ERROR calculator states.

    RESULT states hold a bare previous result in ``left`` with no pending
    operator. ERROR states retain the entered expression (any operands and
    operator) while displaying the division-by-zero message.
    """

    if draw(st.booleans()):
        # RESULT mode: a bare previous result, no pending operator.
        return CalculatorState(
            left=draw(result_operands()),
            operator=None,
            right="",
            mode=Mode.RESULT,
        )
    # ERROR mode: the entered expression is retained internally.
    from calculator.arithmetic_engine import Operator

    return CalculatorState(
        left=draw(result_operands()),
        operator=draw(st.sampled_from(list(Operator))),
        right=draw(result_operands()),
        mode=Mode.ERROR,
    )


# Feature: calculator-app, Property 3: Digit from a terminal display starts a fresh expression
@settings(max_examples=200)
@given(state=terminal_states(), digit=st.sampled_from(DIGITS))
def test_property_3_digit_from_terminal_display_starts_fresh_expression(state, digit):
    """For any calculator state in RESULT mode (a bare previous result, no
    pending operator) or ERROR mode, pressing a digit produces a new EDITING
    expression whose entire content is exactly that single digit, with no error
    message and no residual result.

    Validates: Requirements 1.4, 3.5
    """
    new_state = state.press_digit(digit)

    # A fresh EDITING expression containing only the pressed digit.
    assert new_state.mode == Mode.EDITING
    assert new_state.left == digit
    assert new_state.operator is None
    assert new_state.right == ""

    # The display shows exactly that digit: no residual result, no error text.
    assert new_state.display_string() == digit
