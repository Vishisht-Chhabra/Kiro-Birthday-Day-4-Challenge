"""Timing / performance example tests for the Calculator_App.

These are single timed example tests (not property tests) that measure a
relevant operation with :func:`time.perf_counter` and assert it completes
within the required bound:

* equals computes within 200 ms (Requirement 2.5)
* a button press updates the Display within 200 ms (Requirement 5.3)
* applying a theme completes within 1 s (Requirements 6.3, 6.4, 6.5)
* startup rendering completes within 3 s (Requirement 5.1)

The equals-computation bound is exercised purely on ``CalculatorState`` and
needs no display server. The remaining bounds involve the Tkinter ``GUI`` and
therefore require a live display; on a headless machine (where ``tk.Tk()``
raises ``tk.TclError``) those tests skip gracefully rather than fail.
"""

from __future__ import annotations

import time
import tkinter as tk

import pytest

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState, Mode


# Timing bounds expressed in seconds.
EQUALS_BOUND_S = 0.200
BUTTON_UPDATE_BOUND_S = 0.200
THEME_APPLY_BOUND_S = 1.0
STARTUP_BOUND_S = 3.0


@pytest.fixture
def gui_root():
    """Provide a Tk root for GUI timing tests, skipping if headless.

    Attempts to create a real Tk root. If no display server is available the
    constructor raises ``tk.TclError``; the test is skipped instead of failing.
    The root is destroyed on teardown.
    """
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"No display server available for Tkinter: {exc}")

    # Keep the window off-screen/hidden during the timed measurement.
    try:
        root.withdraw()
    except tk.TclError:
        pass

    try:
        yield root
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass


def test_equals_computes_within_200ms():
    """press_equals on a complete two-operand expression computes within 200 ms.

    Validates: Requirement 2.5
    """
    # A complete expression: 123456 * 654321 (two operands, one operator).
    state = CalculatorState(
        left="123456", operator=Operator.MULTIPLY, right="654321", mode=Mode.EDITING
    )

    start = time.perf_counter()
    result = state.press_equals()
    elapsed = time.perf_counter() - start

    # The computation actually produced a result (guards against a no-op).
    assert result.mode == Mode.RESULT
    assert elapsed < EQUALS_BOUND_S, (
        f"equals took {elapsed * 1000:.3f} ms, exceeding the 200 ms bound"
    )


@pytest.mark.gui
def test_button_to_display_update_within_200ms(gui_root):
    """A digit button press refreshes the Display within 200 ms.

    Validates: Requirement 5.3
    """
    from calculator.gui import CalculatorGUI

    gui = CalculatorGUI(gui_root)

    start = time.perf_counter()
    gui._on_button("7")
    elapsed = time.perf_counter() - start

    # The Display reflects the pressed digit...
    assert gui.display.cget("text") == "7"
    # ...and the update completed within the bound.
    assert elapsed < BUTTON_UPDATE_BOUND_S, (
        f"button-to-display update took {elapsed * 1000:.3f} ms, "
        "exceeding the 200 ms bound"
    )


@pytest.mark.gui
def test_theme_apply_within_1s(gui_root):
    """Applying a theme completes within 1 second.

    Validates: Requirements 6.3, 6.4, 6.5
    """
    from calculator.gui import CalculatorGUI

    gui = CalculatorGUI(gui_root)

    start = time.perf_counter()
    gui._on_theme_selected("Dark")
    elapsed = time.perf_counter() - start

    # The theme was actually applied...
    assert gui.theme_manager.active == "Dark"
    # ...within the 1 second bound.
    assert elapsed < THEME_APPLY_BOUND_S, (
        f"theme apply took {elapsed * 1000:.3f} ms, exceeding the 1 s bound"
    )


@pytest.mark.gui
def test_startup_render_within_3s(gui_root):
    """Constructing the GUI (startup render) completes within 3 seconds.

    Validates: Requirement 5.1
    """
    from calculator.gui import CalculatorGUI

    start = time.perf_counter()
    gui = CalculatorGUI(gui_root)
    elapsed = time.perf_counter() - start

    # The Display was rendered and initialized to zero on startup.
    assert gui.display.cget("text") == "0"
    assert elapsed < STARTUP_BOUND_S, (
        f"startup render took {elapsed * 1000:.3f} ms, exceeding the 3 s bound"
    )
