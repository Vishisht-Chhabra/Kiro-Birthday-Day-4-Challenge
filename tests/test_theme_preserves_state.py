"""Property-based test for Theme_Manager preserving calculator state.

# Feature: calculator-app, Property 13: Applying a theme preserves calculator state
"""

from __future__ import annotations

from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState, Mode
from calculator.theme_manager import THEMES, ThemeManager


# The three valid theme names the selector offers (Requirement 6.2).
THEME_NAMES = sorted(THEMES.keys())


class StubWidgets:
    """A lightweight stub widgets container.

    Exposes ``display``, ``buttons``, and ``selector`` attributes whose stub
    objects accept arbitrary ``configure`` calls, so ``ThemeManager.apply`` can
    style them without a real Tkinter display server.
    """

    class _StubWidget:
        def configure(self, **kwargs):  # pragma: no cover - trivial sink
            return None

    def __init__(self) -> None:
        self.display = self._StubWidget()
        self.buttons = [self._StubWidget() for _ in range(3)]
        self.selector = self._StubWidget()


def _operands():
    """Generate operand strings covering empty, digits, decimals, and negatives."""
    return st.one_of(
        st.just(""),
        st.from_regex(r"[0-9]{1,15}", fullmatch=True),
        st.from_regex(r"[0-9]{0,7}\.[0-9]{0,7}", fullmatch=True),
        st.from_regex(r"-[0-9]{1,10}(\.[0-9]{1,5})?", fullmatch=True),
        st.just("Cannot divide by zero"),
    )


@st.composite
def calculator_states(draw) -> CalculatorState:
    """Build a CalculatorState from operand strings, an optional operator, and a mode."""
    left = draw(_operands())
    operator = draw(st.one_of(st.none(), st.sampled_from(list(Operator))))
    right = draw(_operands())
    mode = draw(st.sampled_from(list(Mode)))
    return CalculatorState(left=left, operator=operator, right=right, mode=mode)


# Feature: calculator-app, Property 13: Applying a theme preserves calculator state
@settings(max_examples=200)
@given(state=calculator_states(), theme_name=st.sampled_from(THEME_NAMES))
def test_applying_theme_preserves_calculator_state(state, theme_name):
    """For any calculator state and any of the three theme names, applying that
    theme leaves the calculator state and its display string unchanged
    (Requirement 6.6)."""
    manager = ThemeManager()
    widgets = StubWidgets()

    # Capture the state and its rendering before applying the theme. Because
    # CalculatorState is frozen, `before` is an independent immutable snapshot.
    before = replace(state)
    display_before = state.display_string()

    manager.apply(theme_name, widgets)

    # The state object is unchanged (value equality on the frozen dataclass)...
    assert state == before
    # ...and its rendered display string is identical.
    assert state.display_string() == display_before
