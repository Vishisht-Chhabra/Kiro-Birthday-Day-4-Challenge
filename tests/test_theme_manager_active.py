"""Property-based test for Theme_Manager's single-active-theme invariant.

# Feature: calculator-app, Property 14: Exactly one theme is active
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from calculator.theme_manager import THEMES, ThemeManager


# The three valid theme names the selector offers (Requirement 6.2).
THEME_NAMES = sorted(THEMES.keys())


class StubWidgets:
    """A lightweight stub widgets container.

    Exposes ``display``, ``buttons``, and ``selector`` attributes. The stub
    objects accept arbitrary ``configure`` calls so ``ThemeManager.apply`` can
    style them without a real Tkinter display server.
    """

    class _StubWidget:
        def configure(self, **kwargs):  # pragma: no cover - trivial sink
            return None

    def __init__(self) -> None:
        self.display = self._StubWidget()
        self.buttons = [self._StubWidget() for _ in range(3)]
        self.selector = self._StubWidget()


# Feature: calculator-app, Property 14: Exactly one theme is active
@settings(max_examples=200)
@given(sequence=st.lists(st.sampled_from(THEME_NAMES), min_size=1))
def test_exactly_one_theme_active_after_any_sequence(sequence):
    """For any non-empty sequence of theme applications, after the sequence
    completes exactly one theme is active and it equals the most recently
    applied theme (Requirement 6.7)."""
    manager = ThemeManager()
    widgets = StubWidgets()

    for theme_name in sequence:
        manager.apply(theme_name, widgets)

    # Exactly one theme is active: `active` holds a single valid theme name...
    assert manager.active in THEMES
    # ...and it is the most recently applied theme.
    assert manager.active == sequence[-1]
