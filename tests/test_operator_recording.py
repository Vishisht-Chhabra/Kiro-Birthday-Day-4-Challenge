"""Property-based test for CalculatorState operator recording.

Uses Hypothesis to verify Property 4 across reachable calculator states that
contain at least one operand and no pending operator (EDITING states with a
non-empty first operand, and RESULT states holding a previous result). Each of
the four operators is exercised.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState, Mode


@st.composite
def operands(draw) -> str:
    """Generate a non-empty operand string as the user would enter it.

    An operand is one or more digit characters (capped at 15) with at most one
    decimal point. When the decimal point is placed at the start a leading zero
    is prepended so the operand mirrors what ``press_decimal`` produces.
    """

    body = draw(st.text(alphabet="0123456789", min_size=1, max_size=15))
    has_decimal = draw(st.booleans())
    if not has_decimal:
        return body
    pos = draw(st.integers(min_value=0, max_value=len(body)))
    if pos == 0:
        return "0." + body  # avoid a bare leading '.'
    return body[:pos] + "." + body[pos:]


@st.composite
def states_with_one_operand_no_operator(draw) -> CalculatorState:
    """Generate reachable states with at least one operand and no operator.

    Covers two reachable shapes:

    * EDITING with a non-empty first operand and no pending operator.
    * RESULT mode holding a bare previous result in ``left`` (treated as the
      first operand when an operator is next pressed).
    """

    left = draw(operands())
    mode = draw(st.sampled_from([Mode.EDITING, Mode.RESULT]))
    return CalculatorState(left=left, operator=None, right="", mode=mode)


# Feature: calculator-app, Property 4: Operator recording
@settings(max_examples=200)
@given(
    state=states_with_one_operand_no_operator(),
    op=st.sampled_from(list(Operator)),
)
def test_property_4_operator_recording(state, op):
    """For any calculator state that contains at least one operand and no
    pending operator, pressing any of the four operators (add, subtract,
    multiply, divide) records exactly that operator in the expression and
    leaves the entered operands unchanged.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4
    """
    new_state = state.press_operator(op)

    # Exactly the selected operator is recorded.
    assert new_state.operator == op

    # The entered first operand is left unchanged.
    assert new_state.left == state.left

    # No second operand is introduced by recording the operator.
    assert new_state.right == ""

    # After recording an operator the calculator is in EDITING mode, ready for
    # the second operand.
    assert new_state.mode == Mode.EDITING
