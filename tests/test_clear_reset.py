"""Property-based test for CalculatorState clear behavior.

Uses Hypothesis to verify Property 9 across reachable states in every mode
(EDITING, RESULT, ERROR) with varied operands and operators.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState, Mode

DIGITS = "0123456789"


@st.composite
def operands(draw) -> str:
    """Generate an operand string as could be produced during EDITING.

    Covers empty operands, single digits, operands up to the 15-digit cap, and
    operands containing a single decimal point (with the leading-zero rule when
    the decimal starts the operand).
    """

    body = draw(st.text(alphabet=DIGITS, min_size=0, max_size=15))
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
def calculator_states(draw) -> CalculatorState:
    """Generate reachable CalculatorState values across all three modes.

    * EDITING - a first operand and optionally a recorded operator plus a
      (possibly empty) second operand.
    * RESULT - a bare formatted result held in ``left`` with no operator.
    * ERROR - a retained two-operand division expression showing the
      divide-by-zero message.
    """

    mode = draw(st.sampled_from(list(Mode)))

    if mode == Mode.RESULT:
        # A completed result is stored as a formatted numeric string in ``left``.
        value = draw(
            st.floats(allow_nan=False, allow_infinity=False, width=32)
        )
        return CalculatorState(
            left=f"{value:.10g}", operator=None, right="", mode=Mode.RESULT
        )

    if mode == Mode.ERROR:
        # ERROR retains the entered expression (a division with a zero divisor).
        left = draw(operands().filter(lambda s: s != ""))
        return CalculatorState(
            left=left, operator=Operator.DIVIDE, right="0", mode=Mode.ERROR
        )

    # EDITING mode.
    has_operator = draw(st.booleans())
    if has_operator:
        left = draw(operands().filter(lambda s: s != ""))
        operator = draw(st.sampled_from(list(Operator)))
        right = draw(operands())
        return CalculatorState(
            left=left, operator=operator, right=right, mode=Mode.EDITING
        )
    left = draw(operands())
    return CalculatorState(left=left, operator=None, right="", mode=Mode.EDITING)


# Feature: calculator-app, Property 9: Clear resets to a single zero from any state
@settings(max_examples=200)
@given(state=calculator_states())
def test_property_9_clear_resets_to_single_zero(state):
    """For any calculator state (including RESULT and ERROR states), pressing
    clear yields an empty expression whose display shows a single zero.

    Validates: Requirements 4.1, 3.4
    """
    cleared = state.press_clear()

    # The expression is empty: no operands, no operator, back to EDITING.
    assert cleared.left == ""
    assert cleared.operator is None
    assert cleared.right == ""
    assert cleared.mode == Mode.EDITING

    # The display shows a single zero.
    assert cleared.display_string() == "0"
