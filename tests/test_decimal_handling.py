"""Property-based test for CalculatorState decimal point handling.

Uses Hypothesis to verify Property 2 across a range of reachable EDITING
states, including operands with and without an existing decimal point and
empty operands.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState, Mode


@st.composite
def operands(draw) -> str:
    """Generate an operand string as could be produced during EDITING.

    An operand is zero or more digit characters (capped at 15) with at most
    one decimal point. When a decimal point is placed at the start, a leading
    zero is prepended so the operand mirrors what ``press_decimal`` produces
    from an empty operand.
    """

    body = draw(st.text(alphabet="0123456789", min_size=0, max_size=15))
    has_decimal = draw(st.booleans())
    if not has_decimal:
        return body
    if body == "":
        return "0."  # leading-zero rule when empty
    pos = draw(st.integers(min_value=0, max_value=len(body)))
    if pos == 0:
        return "0." + body  # avoid a bare leading '.'
    return body[:pos] + "." + body[pos:]


@st.composite
def editing_states(draw) -> CalculatorState:
    """Generate reachable EDITING calculator states.

    Covers states with only a first operand as well as states with a recorded
    operator and a (possibly empty) second operand, so the "current operand"
    is exercised both as ``left`` and as ``right``.
    """

    left = draw(operands())
    if draw(st.booleans()):
        operator = draw(st.sampled_from(list(Operator)))
        right = draw(operands())
        return CalculatorState(
            left=left, operator=operator, right=right, mode=Mode.EDITING
        )
    return CalculatorState(left=left, mode=Mode.EDITING)


def _current_operand(state: CalculatorState) -> str:
    """The operand currently being edited (``right`` once an operator exists)."""
    return state.right if state.operator is not None else state.left


# Feature: calculator-app, Property 2: Decimal point handling
@settings(max_examples=200)
@given(state=editing_states())
def test_property_2_decimal_point_handling(state):
    """For any calculator state, pressing the decimal point button results in
    the current operand containing exactly one decimal point: if the operand
    had none it gains one (starting with a leading zero when the operand was
    empty), and if it already had one the state is left unchanged.

    Validates: Requirements 1.2, 1.3, 1.5
    """
    current_before = _current_operand(state)
    had_decimal = "." in current_before

    new_state = state.press_decimal()
    current_after = _current_operand(new_state)

    # The current operand always contains exactly one decimal point afterward.
    assert current_after.count(".") == 1

    if had_decimal:
        # Requirement 1.3: a second decimal point is ignored; state unchanged.
        assert new_state == state
    else:
        # Requirement 1.2 / 1.5: exactly one decimal point is gained.
        if current_before == "":
            # Requirement 1.5: empty operand starts with a leading zero.
            assert current_after == "0."
        else:
            assert current_after == current_before + "."

        # The operator, mode, and the other operand are all unchanged.
        assert new_state.operator == state.operator
        assert new_state.mode == state.mode
        if new_state.operator is not None:
            assert new_state.left == state.left
        else:
            assert new_state.right == state.right
