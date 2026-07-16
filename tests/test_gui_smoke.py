"""Smoke test for GUI construction.

Constructs a ``CalculatorGUI`` on a live Tk root and asserts the Display and a
button for every input token exist: digits 0-9, the decimal point, the four
operators, equals, clear, and delete (Requirement 5.1).

Tkinter requires a display server. In headless environments creating the root
raises ``tk.TclError``; this test skips in that case rather than failing, while
still running wherever a display is available (see the design's Test
Environment Note).
"""

from __future__ import annotations

import tkinter as tk

import pytest

from calculator.gui import CalculatorGUI

# Every input token the GUI must expose a button for (Requirement 5.1):
# digits 0-9, the decimal point, the four operators, equals, clear, delete.
_EXPECTED_BUTTON_TOKENS: tuple[str, ...] = (
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    ".",
    "+", "-", "*", "/",
    "=",
    "C",
    "DEL",
)


@pytest.fixture
def gui():
    """Build a CalculatorGUI on a fresh Tk root, skipping if headless."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"no display server available for Tkinter: {exc}")

    try:
        yield CalculatorGUI(root)
    finally:
        root.destroy()


@pytest.mark.gui
def test_gui_construction_creates_display_and_all_buttons(gui):
    """The GUI renders a Display and a button for every token (Req 5.1)."""
    # The Display exists and is a Tkinter Label widget.
    assert isinstance(gui.display, tk.Label)

    # A button exists for every expected input token. Buttons are built from
    # tk.Label (bound to click events) so that background colors render on
    # macOS; assert the widget exists and is the expected clickable widget.
    for token in _EXPECTED_BUTTON_TOKENS:
        assert token in gui.buttons, f"missing button for token {token!r}"
        assert isinstance(gui.buttons[token], tk.Label)

    # No unexpected tokens leaked into the button registry.
    assert set(gui.buttons.keys()) == set(_EXPECTED_BUTTON_TOKENS)
