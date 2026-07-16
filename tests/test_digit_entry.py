"""Property-based tests for CalculatorState digit entry.

Uses Hypothesis to verify Property 1 (the 15-digit operand cap) across a wide
range of reachable EDITING states and digit presses.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import (
    MAX_OPERAND_DIGITS,
    CalculatorState,
    Mode,
    _digit_count,
)

DIGITS = "0123456789"


@st.composite
def operands(draw, min_digits: int = 0):
    """Generate an operand string as the user would enter it.

    Covers the boundary cases called out by the design: empty, a single digit,
    exactly ``MAX_OPERAND_DIGITS`` digits, and operands containing a single
    decimal point. Digit counts range from ``min_digits`` up to the cap; a
    reachable operand never exceeds the cap because ``press_digit`` enforces
    it, so operands with more than ``MAX_OPERAND_DIGITS`` digits are not
    generated.
    """

    n_digits = draw(st.integers(min_value=min_digits, max_value=MAX_OPERAND_DIGITS))
    digits = draw(st.text(alphabet=DIGITS, min_size=n_digits, max_size=n_digits))

    include_decimal = draw(st.booleans())
    if not include_decimal:
        return digits
    if digits == "":
        # A lone decimal point starts with a leading zero, e.g. "0.".
        return "0."
    pos = draw(st.integers(min_value=0, max_value=len(digits)))
    return digits[:pos] + "." + digits[pos:]


@st.composite
def editing_states(draw):
    """Generate reachable EDITING CalculatorState values.

    When no operator is recorded the second operand is empty (as it would be
    before an operator is pressed). When an operator is recorded the first
    operand is non-empty, mirroring how a reachable expression is built.
    """

    has_operator = draw(st.booleans())
    if has_operator:
        left = draw(operands(min_digits=1))
        operator = draw(st.sampled_from(list(Operator)))
        right = draw(operands())
        return CalculatorState(
            left=left, operator=operator, right=right, mode=Mode.EDITING
        )
    left = draw(operands())
    return CalculatorState(left=left, operator=None, right="", mode=Mode.EDITING)


# Feature: calculator-app, Property 1: Digit append respects the 15-digit cap
@settings(max_examples=200)
@given(state=editing_states(), digit=st.sampled_from(DIGITS))
def test_property_1_digit_append_respects_15_digit_cap(state, digit):
    """For any calculator state and any digit 0-9, pressing that digit either
    appends it to the current operand (when the operand has fewer than 15
    digits) leaving all other operands and the operator unchanged, or leaves
    the state unchanged (when the current operand already has 15 digits). The
    current operand's digit count never exceeds 15.

    Validates: Requirements 1.1, 1.6
    """
    editing_current = state.right if state.operator is not None else state.left
    digits_before = _digit_count(editing_current)

    new_state = state.press_digit(digit)

    # Mode is never changed by digit entry.
    assert new_state.mode == state.mode

    if digits_before < MAX_OPERAND_DIGITS:
        # The digit is appended to the current operand...
        if state.operator is not None:
            assert new_state.right == state.right + digit
            # ...leaving the other operand and the operator unchanged.
            assert new_state.left == state.left
            assert new_state.operator == state.operator
        else:
            assert new_state.left == state.left + digit
            assert new_state.right == state.right
            assert new_state.operator == state.operator
    else:
        # At the cap: the press is ignored and the state is unchanged.
        assert new_state == state

    # The current operand's digit count never exceeds the cap.
    new_current = new_state.right if new_state.operator is not None else new_state.left
    assert _digit_count(new_current) <= MAX_OPERAND_DIGITS
