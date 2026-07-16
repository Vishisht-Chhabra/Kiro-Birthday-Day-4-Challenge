"""Property-based test for CalculatorState delete on a displayed result.

Uses Hypothesis to verify Property 11: pressing delete while a bare previous
result is displayed (RESULT mode) leaves both the state and the displayed
result unchanged.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.calculator_state import (
    CalculatorState,
    Mode,
    _format_result,
)


@st.composite
def result_states(draw) -> CalculatorState:
    """Generate reachable RESULT-mode calculator states.

    A RESULT state holds a bare previous result in ``left`` with no pending
    operator and an empty second operand (exactly what ``press_equals``
    produces on a successful evaluation). The stored string is formatted the
    same way ``press_equals`` formats results, covering negatives, zero,
    decimals, and large magnitudes.
    """

    value = draw(
        st.floats(
            allow_nan=False,
            allow_infinity=False,
            min_value=-1e12,
            max_value=1e12,
        )
    )
    result = _format_result(value)
    return CalculatorState(left=result, operator=None, right="", mode=Mode.RESULT)


# Feature: calculator-app, Property 11: Delete does not alter a displayed result
@settings(max_examples=200)
@given(state=result_states())
def test_property_11_delete_does_not_alter_a_displayed_result(state):
    """For any calculator state in RESULT mode (showing only a previous
    result), pressing delete leaves the state and displayed result unchanged.

    Validates: Requirements 4.5
    """
    display_before = state.display_string()

    new_state = state.press_delete()

    # The state is completely unchanged (same operands, operator, and mode).
    assert new_state == state
    # And the displayed result is unchanged.
    assert new_state.display_string() == display_before
