"""Integration tests for theme application on the Tkinter GUI.

Constructs a real :class:`~calculator.gui.CalculatorGUI`, applies each of the
three themes via ``_on_theme_selected``, and asserts that representative widget
option values (background, foreground, font) on the Display, a representative
button, and the theme selector match the applied theme's definition
(Requirements 6.3, 6.4, 6.5). Also asserts the active-theme indicator and
``ThemeManager.active`` reflect the applied theme (Requirement 6.8).

These tests require a live Tk display server. In a headless environment
constructing ``tk.Tk()`` raises ``tk.TclError``; such runs are skipped rather
than failed (use ``xvfb`` in headless CI to exercise them).
"""

from __future__ import annotations

import tkinter as tk

import pytest

from calculator.gui import CalculatorGUI
from calculator.theme_manager import THEMES, Theme

# A representative button token to check (a plain digit button). All buttons
# receive identical theming, so one is representative of the whole set.
_REPRESENTATIVE_BUTTON = "7"

# The three themes exercised by these tests (Requirement 6.2).
_THEME_NAMES = ("Classic", "Dark", "Fun")


@pytest.fixture()
def gui():
    """Yield a constructed ``CalculatorGUI``, skipping if no display is present.

    The Tk root is destroyed during teardown regardless of test outcome.
    """
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - headless environment
        pytest.skip(f"Tkinter display server unavailable: {exc}")

    try:
        yield CalculatorGUI(root)
    finally:
        root.destroy()


def _font_str(widget: tk.Widget) -> str:
    """Return the widget's font option as a normalized string.

    Tk renders a ``(family, size)`` font as e.g. ``"Helvetica 16"`` or, when the
    family contains spaces, ``"{Comic Sans MS} 18"``. Returning the string form
    lets callers assert on the family and size substrings without depending on
    the exact quoting Tk chooses.
    """
    return str(widget.cget("font"))


def _assert_display_matches(gui: CalculatorGUI, theme: Theme) -> None:
    """Assert the Display's colors and font match ``theme``."""
    assert gui.display.cget("bg") == theme.display_bg
    assert gui.display.cget("fg") == theme.display_fg
    font = _font_str(gui.display)
    assert theme.font_family in font
    assert str(theme.font_size) in font


def _assert_button_matches(gui: CalculatorGUI, theme: Theme) -> None:
    """Assert a representative button's colors and font match ``theme``."""
    button = gui.buttons[_REPRESENTATIVE_BUTTON]
    assert button.cget("bg") == theme.button_bg
    assert button.cget("fg") == theme.button_fg
    font = _font_str(button)
    assert theme.font_family in font
    assert str(theme.font_size) in font


def _assert_selector_matches(gui: CalculatorGUI, theme: Theme) -> None:
    """Assert the theme selector's colors and font match ``theme``.

    The selector uses the theme's accent color as its background and the button
    foreground color as its text color (see ``ThemeManager.apply``).
    """
    assert gui.selector.cget("bg") == theme.accent
    assert gui.selector.cget("fg") == theme.button_fg
    font = _font_str(gui.selector)
    assert theme.font_family in font
    assert str(theme.font_size) in font


@pytest.mark.parametrize("theme_name", _THEME_NAMES)
def test_theme_application_styles_display_button_and_selector(gui, theme_name):
    """Applying a theme restyles the Display, buttons, and selector to match it.

    Validates: Requirements 6.3, 6.4, 6.5
    """
    theme = THEMES[theme_name]

    gui._on_theme_selected(theme_name)

    _assert_display_matches(gui, theme)
    _assert_button_matches(gui, theme)
    _assert_selector_matches(gui, theme)


@pytest.mark.parametrize("theme_name", _THEME_NAMES)
def test_theme_application_updates_active_indicator(gui, theme_name):
    """Applying a theme records it as active and reflects it in the indicator.

    Validates: Requirements 6.8
    """
    gui._on_theme_selected(theme_name)

    # Exactly one theme is active and it is the one just applied.
    assert gui.theme_manager.active == theme_name
    # The selector variable tracks the active theme...
    assert gui.theme_var.get() == theme_name
    # ...and the on-screen indicator names it.
    assert theme_name in gui.theme_indicator.cget("text")


def test_switching_themes_replaces_previous_styling(gui):
    """Switching between all three themes leaves every widget matching the last.

    Applying Classic, then Dark, then Fun in sequence must leave the Display, a
    representative button, and the selector styled for Fun, with Fun recorded as
    the single active theme (Requirements 6.3, 6.4, 6.5, 6.8).
    """
    for theme_name in ("Classic", "Dark", "Fun"):
        gui._on_theme_selected(theme_name)

    fun = THEMES["Fun"]
    _assert_display_matches(gui, fun)
    _assert_button_matches(gui, fun)
    _assert_selector_matches(gui, fun)
    assert gui.theme_manager.active == "Fun"
    assert "Fun" in gui.theme_indicator.cget("text")
