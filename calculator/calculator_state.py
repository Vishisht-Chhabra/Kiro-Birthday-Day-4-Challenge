"""CalculatorState: the pure in-memory editing model for the Calculator_App.

Captures the current Expression (two operands and an optional operator), the
editing mode, and all input/editing rules as pure state transitions. Each
transition returns a new immutable :class:`CalculatorState` instance. This
module has no knowledge of Tkinter and performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from calculator.arithmetic_engine import Err, Operator, evaluate

MAX_OPERAND_DIGITS = 15
MAX_SIGNIFICANT_DIGITS = 10


class Mode(Enum):
    """The current editing mode of the calculator."""

    EDITING = "editing"  # user is building an expression
    RESULT = "result"  # display shows a completed result, no operator pending
    ERROR = "error"  # division-by-zero message is shown


def _digit_count(operand: str) -> int:
    """Count only the digit characters in an operand string.

    The decimal point does not count against the 15-digit operand cap.
    """

    return sum(1 for ch in operand if ch.isdigit())


def _format_result(value: float) -> str:
    """Format a numeric result to at most 10 significant digits.

    Uses Python's general float formatting (``g``), which renders
    integer-valued results without a trailing ``.0``, collapses floating-point
    noise within the required tolerance, and preserves ``inf``/``-inf`` and
    ``nan`` representations rather than raising (Requirement 2.6).
    """

    return f"{value:.{MAX_SIGNIFICANT_DIGITS}g}"


@dataclass(frozen=True)
class CalculatorState:
    """An immutable snapshot of the calculator's expression and mode.

    Operands are stored as strings during entry to faithfully preserve user
    input (leading zero, trailing decimal point) and are parsed to ``float``
    only at evaluation time.
    """

    left: str = ""
    operator: Operator | None = None
    right: str = ""
    mode: Mode = Mode.EDITING

    # --- helpers -----------------------------------------------------------

    def _editing_current(self) -> str:
        """Return the operand currently being edited.

        The second operand (``right``) is the current operand once an operator
        has been recorded; otherwise the first operand (``left``) is current.
        """

        return self.right if self.operator is not None else self.left

    def _with_current(self, operand: str) -> "CalculatorState":
        """Return a new state with ``operand`` written to the current operand."""

        if self.operator is not None:
            return replace(self, right=operand)
        return replace(self, left=operand)

    # --- transitions (each returns a new CalculatorState) ------------------

    def press_digit(self, d: str) -> "CalculatorState":
        """Append digit ``d`` to the current operand, enforcing the 15-digit cap.

        In RESULT or ERROR mode (a terminal display), pressing a digit starts a
        fresh EDITING expression containing only that digit, discarding any
        previous result or error message (Requirements 1.4, 3.5).

        Otherwise, only digit characters count toward the cap; if the current
        operand already contains 15 digits the state is returned unchanged.
        """

        if self.mode in (Mode.RESULT, Mode.ERROR):
            return CalculatorState(left=d, operator=None, right="", mode=Mode.EDITING)

        current = self._editing_current()
        if _digit_count(current) >= MAX_OPERAND_DIGITS:
            return self
        return self._with_current(current + d)

    def press_decimal(self) -> "CalculatorState":
        """Add a single decimal point to the current operand.

        When the current operand is empty it starts with a leading zero
        (``"0."``). If the operand already contains a decimal point, the state
        is returned unchanged.
        """

        current = self._editing_current()
        if "." in current:
            return self
        if current == "":
            return self._with_current("0.")
        return self._with_current(current + ".")

    def press_operator(self, op: Operator) -> "CalculatorState":
        """Record or replace the pending operator.

        Behavior (Requirements 2.1–2.4, 2.7):

        * EDITING with at least one operand entered and no pending operator →
          record ``op`` as the pending operator (Property 4).
        * An operator already recorded but the second operand is still empty →
          replace the recorded operator with ``op`` (Property 5).
        * RESULT mode (a bare previous result held in ``left``) → treat that
          result as the first operand and record ``op``, returning to EDITING.
        * No operand entered yet (empty ``left`` in EDITING) or ERROR mode →
          the state is returned unchanged.
        * An operator is recorded and a second operand has been entered →
          returned unchanged (evaluation/chaining is handled elsewhere).
        """

        # ERROR mode: operator selection is ignored until clear/digit.
        if self.mode == Mode.ERROR:
            return self

        # RESULT mode: the previous result (stored in ``left``) becomes the
        # first operand and the operator is recorded, resuming editing.
        if self.mode == Mode.RESULT:
            if self.left == "":
                return self
            return replace(self, operator=op, right="", mode=Mode.EDITING)

        # EDITING mode.
        if self.operator is None:
            # Record the operator only when at least one operand exists.
            if self.left == "":
                return self
            return replace(self, operator=op)

        # An operator is already recorded.
        if self.right == "":
            # No second operand yet: replace the pending operator (Req 2.7).
            return replace(self, operator=op)

        # A second operand exists: leave the state unchanged here.
        return self

    def press_equals(self) -> "CalculatorState":
        """Evaluate a complete expression and transition to a terminal display.

        Behavior (Requirements 1.4, 2.5, 2.6, 2.8, 3.1, 3.2, 3.3, 3.5, 5.5):

        * Only computes when the expression holds exactly two operands and one
          operator while in EDITING mode; otherwise the state is returned
          unchanged (Requirement 2.8, Property 7).
        * Parses the operand strings to ``float`` and delegates to
          :func:`arithmetic_engine.evaluate`.
        * On ``Ok``, formats the value to at most 10 significant digits, stores
          it as the sole operand, and transitions to :attr:`Mode.RESULT`.
        * On ``Err(DIVIDE_BY_ZERO)``, transitions to :attr:`Mode.ERROR`,
          retaining the entered expression until a clear or digit press.
        """

        # Guard: equals only computes with exactly two operands and one
        # operator in EDITING mode. Anything else is a no-op.
        if (
            self.mode != Mode.EDITING
            or self.left == ""
            or self.operator is None
            or self.right == ""
        ):
            return self

        left_value = float(self.left)
        right_value = float(self.right)
        result = evaluate(left_value, self.operator, right_value)

        if isinstance(result, Err):
            # Retain the expression; display renders the fixed error message.
            return replace(self, mode=Mode.ERROR)

        formatted = _format_result(result.value)
        return CalculatorState(
            left=formatted, operator=None, right="", mode=Mode.RESULT
        )

    def press_clear(self) -> "CalculatorState":
        """Reset to a fresh, empty expression from any mode.

        Regardless of the current mode (EDITING, RESULT, or ERROR), clear
        discards the entire expression, any computed result, and any error
        message, returning a fresh EDITING state whose ``display_string()``
        renders a single zero (Requirements 3.4, 4.1).
        """

        return CalculatorState()

    def press_delete(self) -> "CalculatorState":
        """Remove the most recently entered character from the expression.

        Behavior (Requirements 4.2, 4.3, 4.4, 4.5, 3.3):

        * RESULT mode → a bare previous result is left unchanged
          (Requirement 4.5).
        * ERROR mode → delete ends the error state and reveals the retained
          expression, then removes its most recently entered character
          (Requirement 3.3).
        * EDITING mode → the expression is the display string
          (``left`` + operator symbol + ``right``). When it has more than one
          character, the most recently entered character is removed
          (Requirement 4.2); when it has a single character or is empty, the
          state is floored to a fresh empty expression whose display shows a
          single zero (Requirements 4.3, 4.4).
        """

        # RESULT mode: a displayed result is not editable via delete (Req 4.5).
        if self.mode == Mode.RESULT:
            return self

        # ERROR mode: delete recovers by revealing the retained expression in
        # EDITING mode, then applies the normal delete rule (Req 3.3).
        if self.mode == Mode.ERROR:
            return replace(self, mode=Mode.EDITING).press_delete()

        # EDITING mode. Floor to "0" when the expression is empty or a single
        # character (Requirements 4.3, 4.4).
        if len(self.display_string()) <= 1:
            return CalculatorState()

        # More than one character: drop the most recently entered one. The last
        # character of the display string is the last digit of ``right`` if a
        # second operand exists, otherwise the operator symbol if one is
        # recorded, otherwise the last digit of ``left`` (Requirement 4.2).
        if self.right != "":
            return replace(self, right=self.right[:-1])
        if self.operator is not None:
            return replace(self, operator=None)
        return replace(self, left=self.left[:-1])

    def display_string(self) -> str:
        """Render the current expression, result, or error for the Display.

        * ERROR mode → the fixed message ``"Cannot divide by zero"``
          (Requirement 3.2).
        * RESULT mode → the formatted numeric result held in ``left``
          (Requirement 5.5).
        * EDITING mode → an empty expression renders as ``"0"``; otherwise the
          concatenation of ``left``, the operator symbol (if an operator is
          recorded), and ``right``.
        """

        if self.mode == Mode.ERROR:
            return "Cannot divide by zero"

        if self.mode == Mode.RESULT:
            return self.left

        if self.left == "" and self.operator is None and self.right == "":
            return "0"

        operator_symbol = self.operator.value if self.operator is not None else ""
        return f"{self.left}{operator_symbol}{self.right}"
