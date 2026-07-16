"""Property-based test for CalculatorState.press_equals on incomplete expressions.

Uses Hypothesis to verify Property 7: pressing equals on any expression that
does not hold exactly two operands and one operator is a no-op, leaving both
the state and its display string unchanged.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState, Mode


@st.composite
def operands(draw) -> str:
    """Generate an operand string as could be produced during EDITING.

    Zero or more digit characters (capped at 15) with at most one decimal
    point. A leading decimal point is prefixed with a zero to mirror what
    ``press_decimal`` produces from an empty operand.
    """

    body = draw(st.text(alphabet="0123456789", min_size=0, max_size=15))
    has_decimal = draw(st.booleans())
    if not has_decimal:
        return body
    if body == "":
        return "0."
    pos = draw(st.integers(min_value=0, max_value=len(body)))
    if pos == 0:
        return "0." + body
    return body[:pos] + "." + body[pos:]


@st.composite
def nonempty_operands(draw) -> str:
    """Generate a non-empty operand string containing at least one digit."""

    operand = draw(operands())
    if any(ch.isdigit() for ch in operand):
        return operand
    # Ensure at least one digit so the operand is a real value.
    return "0" + operand if operand else "0"


@st.composite
def incomplete_states(draw) -> CalculatorState:
    """Generate reachable calculator states that are NOT a complete
    two-operand-one-operator EDITING expression.

    A complete expression (which ``press_equals`` would evaluate) requires
    EDITING mode with a non-empty ``left``, a recorded ``operator``, and a
    non-empty ``right``. This strategy produces everything else:

    * EDITING missing the left operand (empty ``left``),
    * EDITING missing the operator (no operator recorded),
    * EDITING missing the right operand (operator recorded, empty ``right``),
    * RESULT mode (a bare previous result, no pending operator),
    * ERROR mode (division-by-zero message shown).
    """

    kind = draw(
        st.sampled_from(
            [
                "editing_no_operator",
                "editing_empty_left",
                "editing_empty_right",
                "result",
                "error",
            ]
        )
    )

    if kind == "editing_no_operator":
        # Any single operand, no operator, empty right. Includes empty left.
        left = draw(operands())
        return CalculatorState(left=left, operator=None, right="", mode=Mode.EDITING)

    if kind == "editing_empty_left":
        # Operator recorded but no first operand entered (not reachable as a
        # complete expression); right may be empty or not.
        operator = draw(st.sampled_from(list(Operator)))
        right = draw(operands())
        return CalculatorState(
            left="", operator=operator, right=right, mode=Mode.EDITING
        )

    if kind == "editing_empty_right":
        # Operator recorded, first operand present, second operand still empty.
        left = draw(nonempty_operands())
        operator = draw(st.sampled_from(list(Operator)))
        return CalculatorState(
            left=left, operator=operator, right="", mode=Mode.EDITING
        )

    if kind == "result":
        # A bare previous result held in ``left``, no pending operator.
        left = draw(nonempty_operands())
        return CalculatorState(left=left, operator=None, right="", mode=Mode.RESULT)

    # kind == "error": division-by-zero state; the entered expression may be a
    # full or partial expression that produced the error.
    left = draw(nonempty_operands())
    operator = draw(st.sampled_from(list(Operator)))
    right = draw(operands())
    return CalculatorState(
        left=left, operator=operator, right=right, mode=Mode.ERROR
    )


def _is_complete(state: CalculatorState) -> bool:
    """Whether the state is a complete two-operand-one-operator EDITING expr."""
    return (
        state.mode == Mode.EDITING
        and state.left != ""
        and state.operator is not None
        and state.right != ""
    )


# Feature: calculator-app, Property 7: Equals is a no-op on incomplete expressions
@settings(max_examples=200)
@given(state=incomplete_states())
def test_property_7_equals_is_noop_on_incomplete_expressions(state):
    """For any calculator state that does not contain exactly two operands and
    one operator, pressing equals does not produce a result and leaves the
    state and display unchanged.

    Validates: Requirements 2.8
    """
    # The generator must only produce incomplete expressions.
    assert not _is_complete(state)

    display_before = state.display_string()

    new_state = state.press_equals()

    # Requirement 2.8: no result is produced and the state is unchanged.
    assert new_state == state
    # The display is likewise unchanged.
    assert new_state.display_string() == display_before
