"""Property-based tests for CalculatorState delete (backspace).

Uses Hypothesis to verify Property 10: pressing delete in EDITING mode removes
exactly the most recently entered character from the display, with a floor at a
single zero once the expression is reduced to one character or is empty.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import (
    MAX_OPERAND_DIGITS,
    CalculatorState,
    Mode,
)

DIGITS = "0123456789"


@st.composite
def operands(draw, min_digits: int = 0):
    """Generate an operand string as the user would enter it.

    Covers empty, single-digit, full-cap, and decimal-containing operands,
    mirroring reachable operands built by digit/decimal entry.
    """

    n_digits = draw(st.integers(min_value=min_digits, max_value=MAX_OPERAND_DIGITS))
    digits = draw(st.text(alphabet=DIGITS, min_size=n_digits, max_size=n_digits))

    include_decimal = draw(st.booleans())
    if not include_decimal:
        return digits
    if digits == "":
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


# Feature: calculator-app, Property 10: Delete removes the last character with a floor at zero
@settings(max_examples=200)
@given(state=editing_states())
def test_property_10_delete_removes_last_character_with_floor_at_zero(state):
    """For any calculator state in EDITING mode, pressing delete removes exactly
    the most recently entered character; when the expression had more than one
    character the display equals the previous display without its last
    character, and when it had one character or was empty the display shows a
    single zero.

    Validates: Requirements 4.2, 4.3, 4.4
    """
    display_before = state.display_string()

    new_state = state.press_delete()
    display_after = new_state.display_string()

    if len(display_before) > 1:
        assert display_after == display_before[:-1]
    else:
        assert display_after == "0"
