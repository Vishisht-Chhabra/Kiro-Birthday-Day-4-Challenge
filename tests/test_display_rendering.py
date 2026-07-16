"""Property-based test for CalculatorState display rendering totality.

Uses Hypothesis to verify Property 12: for any reachable calculator state
produced by any sequence of button transitions, ``display_string()`` returns a
valid non-empty string without raising. Rather than fabricating states
directly, this test builds reachability by starting from a fresh
``CalculatorState()`` and applying a randomly generated sequence of button
presses, checking the invariant after every step.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState

DIGITS = "0123456789"


@st.composite
def actions(draw):
    """Generate a single button-press action.

    Each action is a callable that applies one transition to a
    ``CalculatorState``. Digits (0-9), the decimal point, the four operators,
    equals, clear, and delete are all covered so that generated sequences can
    reach every mode (EDITING, RESULT, ERROR) and boundary condition.
    """

    kind = draw(
        st.sampled_from(
            ["digit", "decimal", "operator", "equals", "clear", "delete"]
        )
    )
    if kind == "digit":
        d = draw(st.sampled_from(DIGITS))
        return lambda s: s.press_digit(d)
    if kind == "decimal":
        return lambda s: s.press_decimal()
    if kind == "operator":
        op = draw(st.sampled_from(list(Operator)))
        return lambda s: s.press_operator(op)
    if kind == "equals":
        return lambda s: s.press_equals()
    if kind == "clear":
        return lambda s: s.press_clear()
    return lambda s: s.press_delete()


# Feature: calculator-app, Property 12: Display rendering is total
@settings(max_examples=200)
@given(sequence=st.lists(actions(), min_size=0, max_size=40))
def test_property_12_display_rendering_is_total(sequence):
    """For any reachable calculator state produced by any sequence of button
    transitions, display_string() returns a valid non-empty string without
    raising.

    Validates: Requirements 5.4
    """
    state = CalculatorState()

    # The invariant must hold for the initial state as well as after every
    # transition in the sequence.
    initial = state.display_string()
    assert isinstance(initial, str)
    assert initial != ""

    for action in sequence:
        state = action(state)
        rendered = state.display_string()
        assert isinstance(rendered, str)
        assert rendered != ""
