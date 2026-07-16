"""Property-based test for CalculatorState operator replacement.

Uses Hypothesis to verify Property 5: pressing an operator when an operator is
already recorded and no second operand has been entered replaces the recorded
operator while leaving both operands unchanged.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import MAX_OPERAND_DIGITS, CalculatorState, Mode


@st.composite
def operands(draw, min_digits: int = 0) -> str:
    """Generate an operand string as the user would enter it.

    Covers boundary cases from the design: empty, a single digit, exactly
    ``MAX_OPERAND_DIGITS`` digits, and operands containing a single decimal
    point. A reachable operand never exceeds the 15-digit cap.
    """

    n_digits = draw(st.integers(min_value=min_digits, max_value=MAX_OPERAND_DIGITS))
    digits = draw(st.text(alphabet="0123456789", min_size=n_digits, max_size=n_digits))

    if not draw(st.booleans()):
        return digits
    if digits == "":
        return "0."  # leading-zero rule when empty
    pos = draw(st.integers(min_value=0, max_value=len(digits)))
    if pos == 0:
        return "0." + digits
    return digits[:pos] + "." + digits[pos:]


@st.composite
def states_with_pending_operator_and_no_second_operand(draw) -> CalculatorState:
    """Generate reachable EDITING states with an operator recorded and empty ``right``.

    A recorded operator is only reachable once a first operand exists, so
    ``left`` is non-empty. The second operand is empty, which is exactly the
    precondition for Property 5 (operator replacement).
    """

    left = draw(operands(min_digits=1))
    operator = draw(st.sampled_from(list(Operator)))
    return CalculatorState(
        left=left, operator=operator, right="", mode=Mode.EDITING
    )


# Feature: calculator-app, Property 5: Operator replacement when no second operand exists
@settings(max_examples=200)
@given(
    state=states_with_pending_operator_and_no_second_operand(),
    new_operator=st.sampled_from(list(Operator)),
)
def test_property_5_operator_replacement_when_no_second_operand(state, new_operator):
    """For any calculator state that has an operator recorded and an empty
    second operand, pressing any operator replaces the recorded operator with
    the newly selected one and leaves both operands unchanged.

    Validates: Requirements 2.7
    """
    new_state = state.press_operator(new_operator)

    # The recorded operator is replaced with the newly selected operator.
    assert new_state.operator == new_operator

    # Both operands are left unchanged.
    assert new_state.left == state.left
    assert new_state.right == state.right
    assert new_state.right == ""

    # The mode is unchanged (still EDITING).
    assert new_state.mode == state.mode
