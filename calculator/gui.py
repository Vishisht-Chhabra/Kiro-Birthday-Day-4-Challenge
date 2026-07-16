"""GUI: the Tkinter view/controller layer for the Calculator_App.

``CalculatorGUI`` is a thin adapter that owns a single :class:`CalculatorState`
and a :class:`ThemeManager`. It renders the Display, a button for every input
token (digits 0-9, decimal point, the four operators, equals, clear, delete),
and a three-option theme selector. Button clicks are translated into pure
:class:`CalculatorState` transitions via :meth:`CalculatorGUI._on_button`, and
the resulting state is reflected back onto the Display via
:meth:`CalculatorGUI._refresh_display`.

All calculation and editing logic lives in the pure ``CalculatorState`` and
``Arithmetic_Engine`` modules; this layer performs no arithmetic itself. Theme
changes are routed to the ``ThemeManager`` and never touch calculator state
(Requirement 6.6).

The module imports cleanly without a display server; only *constructing*
``CalculatorGUI`` requires a live Tk root.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from calculator.arithmetic_engine import Operator
from calculator.calculator_state import CalculatorState
from calculator.theme_manager import ThemeManager

# Input tokens for the digit and decimal buttons.
_DIGIT_TOKENS: tuple[str, ...] = tuple(str(d) for d in range(10))
_DECIMAL_TOKEN = "."

# Action tokens for clear and delete (distinct from any operator symbol).
_CLEAR_TOKEN = "C"
_DELETE_TOKEN = "DEL"
_EQUALS_TOKEN = "="

# Maps an operator button token to its Arithmetic_Engine Operator. The tokens
# match the Operator enum values so the display reflects the recorded operator.
_OPERATOR_TOKENS: dict[str, Operator] = {op.value: op for op in Operator}

# Order the four operators deterministically for layout.
_OPERATOR_ORDER: tuple[str, ...] = ("+", "-", "*", "/")

# The three selectable themes (Requirement 6.2).
_THEME_NAMES: tuple[str, ...] = ("Classic", "Dark", "Fun")
_DEFAULT_THEME = "Classic"


class CalculatorGUI:
    """Tkinter view/controller owning one ``CalculatorState`` and theme manager."""

    def __init__(self, root: "tk.Tk") -> None:
        """Build the widgets, initialize the Display to zero, and apply Classic.

        Args:
            root: The Tk root (or Toplevel) window to build the calculator into.
        """
        self.root = root
        self.state = CalculatorState()
        self.theme_manager = ThemeManager()

        # Button widgets keyed by their input token, so tests and the theme
        # manager can locate every button (digits, decimal, operators, equals,
        # clear, delete).
        self.buttons: dict[str, tk.Button] = {}

        try:
            self.root.title("Calculator")
        except tk.TclError:
            # Some minimal/headless roots may not support title(); ignore.
            pass

        self._build_display()
        self._build_theme_selector()
        self._build_buttons()

        # Initialize the Display to zero on startup (Requirement 5.2).
        self._refresh_display()

        # Apply the Classic theme as the default at startup (Requirement 6.1).
        self._on_theme_selected(_DEFAULT_THEME)

    # --- widget construction ------------------------------------------------

    def _build_display(self) -> None:
        """Create the Display widget spanning the top of the window."""
        self.display = tk.Label(
            self.root,
            text="0",
            anchor="e",
            padx=12,
            pady=16,
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew")

    def _build_theme_selector(self) -> None:
        """Create the three-option theme selector and its active indicator."""
        # StringVar backing the selector; its value is the active theme name.
        self.theme_var = tk.StringVar(master=self.root, value=_DEFAULT_THEME)

        # An OptionMenu offering exactly the three themes (Requirement 6.2).
        self.selector = tk.OptionMenu(
            self.root,
            self.theme_var,
            *_THEME_NAMES,
            command=self._on_theme_selected,
        )
        self.selector.grid(row=1, column=0, columnspan=3, sticky="nsew")

        # Active-theme indicator shown alongside the selector (Requirement 6.8).
        self.theme_indicator = tk.Label(
            self.root,
            text=f"Active: {_DEFAULT_THEME}",
            anchor="center",
        )
        self.theme_indicator.grid(row=1, column=3, sticky="nsew")

    def _build_buttons(self) -> None:
        """Create a button for every input token in a calculator-style grid."""
        # Digit + decimal + equals layout (rows 2-5), operators down column 3.
        #
        #   7 8 9 +
        #   4 5 6 -
        #   1 2 3 *
        #   0 . = /
        digit_layout = [
            ("7", "8", "9"),
            ("4", "5", "6"),
            ("1", "2", "3"),
            ("0", ".", "="),
        ]
        for r, row_tokens in enumerate(digit_layout, start=2):
            for c, token in enumerate(row_tokens):
                self._add_button(token, row=r, column=c)

        # Operators run down the right-hand column, one per digit row.
        for i, token in enumerate(_OPERATOR_ORDER):
            self._add_button(token, row=2 + i, column=3)

        # Clear and delete span the bottom row.
        self._add_button(_CLEAR_TOKEN, row=6, column=0, columnspan=2, label="Clear")
        self._add_button(_DELETE_TOKEN, row=6, column=2, columnspan=2, label="Del")

    def _add_button(
        self,
        token: str,
        *,
        row: int,
        column: int,
        columnspan: int = 1,
        label: str | None = None,
    ) -> None:
        """Create a single button bound to ``token`` and register it.

        Args:
            token: The input token this button emits when clicked.
            row: Grid row.
            column: Grid column.
            columnspan: Number of columns the button spans.
            label: Optional display text; defaults to the token itself.
        """
        # Buttons are built from ``tk.Label`` rather than ``tk.Button``: on
        # macOS the native Aqua ``tk.Button`` ignores the ``bg`` option and
        # always paints a white face, which makes light theme text invisible in
        # Dark mode. A ``Label`` honors ``bg``/``fg``/``font`` on every
        # platform, so theming works reliably. Relief and padding give it a
        # button-like appearance and it is bound to a click handler.
        button = tk.Label(
            self.root,
            text=label if label is not None else token,
            relief="raised",
            borderwidth=2,
            padx=12,
            pady=12,
            cursor="hand2",
        )
        button.grid(row=row, column=column, columnspan=columnspan, sticky="nsew")
        button.bind("<Button-1>", self._make_handler(token))
        self.buttons[token] = button

    def _make_handler(self, token: str) -> Callable[[object], None]:
        """Return a click-event callback that dispatches ``token``."""
        return lambda _event=None: self._on_button(token)

    # --- controller ---------------------------------------------------------

    def _on_button(self, token: str) -> None:
        """Map a button token to a ``CalculatorState`` transition, then refresh.

        The state is immutable; each transition returns a new state which
        replaces ``self.state``. After applying the transition the Display is
        refreshed so it reflects the current expression, result, or error
        (Requirements 5.3, 5.4, 5.5).

        Args:
            token: The input token emitted by the clicked button.
        """
        if token in _DIGIT_TOKENS:
            self.state = self.state.press_digit(token)
        elif token == _DECIMAL_TOKEN:
            self.state = self.state.press_decimal()
        elif token in _OPERATOR_TOKENS:
            self.state = self.state.press_operator(_OPERATOR_TOKENS[token])
        elif token == _EQUALS_TOKEN:
            self.state = self.state.press_equals()
        elif token == _CLEAR_TOKEN:
            self.state = self.state.press_clear()
        elif token == _DELETE_TOKEN:
            self.state = self.state.press_delete()
        else:
            # Unknown token: leave state untouched.
            return

        self._refresh_display()

    def _refresh_display(self) -> None:
        """Write ``self.state.display_string()`` to the Display widget."""
        self.display.configure(text=self.state.display_string())

    def _on_theme_selected(self, theme_name: str) -> None:
        """Apply the selected theme without modifying calculator state.

        Routes the selection to the ``ThemeManager``, which restyles the
        Display, all buttons, and the selector, then updates the active-theme
        indicator (Requirements 6.3-6.5, 6.8). Calculator state and the current
        Display text are left untouched (Requirement 6.6).

        Args:
            theme_name: One of ``"Classic"``, ``"Dark"``, or ``"Fun"``.
        """
        self.theme_manager.apply(theme_name, self)

        # Keep the selector variable and active indicator in sync (Req 6.8).
        if self.theme_var.get() != theme_name:
            self.theme_var.set(theme_name)
        self.theme_indicator.configure(text=f"Active: {self.theme_manager.active}")
