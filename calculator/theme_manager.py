"""Theme_Manager component for the Calculator_App.

Applies a named :class:`Theme` (colors and fonts) to the GUI widgets and tracks
the single active theme. This module is intentionally decoupled from calculator
logic: it MUST NOT import or depend on ``CalculatorState`` or the
``Arithmetic_Engine``. Applying a theme is a purely visual operation and never
mutates calculator state (Requirement 6.6).

The ``apply`` method is written tolerantly so it works both with real Tkinter
widgets and with lightweight mock/stub widgets used in tests: unknown widget
options are skipped rather than raising.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Theme:
    """A named set of visual styling values applied to the GUI.

    Attributes:
        name: Human-readable theme name (matches the ``THEMES`` key).
        display_bg: Background color of the Display.
        display_fg: Foreground (text) color of the Display.
        button_bg: Background color of the buttons.
        button_fg: Foreground (text) color of the buttons.
        accent: Accent color used for the theme selector / active indicator.
        font_family: Font family applied to Display, buttons, and selector.
        font_size: Font size applied to Display, buttons, and selector.
    """

    name: str
    display_bg: str
    display_fg: str
    button_bg: str
    button_fg: str
    accent: str
    font_family: str
    font_size: int


# Exactly three themes (Requirement 6.2):
#   Classic -> light default (light bg, dark text) (Requirement 6.1)
#   Dark    -> the Kiro theme (dark bg, light text)
#   Fun     -> colorful/playful palette
THEMES: dict[str, Theme] = {
    "Classic": Theme(
        name="Classic",
        display_bg="#ffffff",
        display_fg="#1a1a1a",
        button_bg="#f0f0f0",
        button_fg="#1a1a1a",
        accent="#4a90d9",
        font_family="Helvetica",
        font_size=16,
    ),
    "Dark": Theme(
        name="Dark",
        display_bg="#1e1e1e",
        display_fg="#f5f5f5",
        button_bg="#2d2d2d",
        button_fg="#f5f5f5",
        accent="#8b5cf6",
        font_family="Helvetica",
        font_size=16,
    ),
    "Fun": Theme(
        name="Fun",
        display_bg="#fff0f6",
        display_fg="#d6336c",
        button_bg="#ffd43b",
        button_fg="#5f3dc4",
        accent="#ff6b6b",
        font_family="Comic Sans MS",
        font_size=18,
    ),
}


def _configure_widget(widget: Any, options: dict[str, Any]) -> None:
    """Apply widget options tolerantly.

    Tries ``widget.configure(**options)`` first. If that fails (for example a
    widget does not accept one of the options), each option is applied
    individually and any option the widget rejects is silently skipped. Widgets
    without a ``configure``/``config`` method are ignored. This keeps ``apply``
    robust across real Tkinter widgets and test doubles.
    """
    if widget is None:
        return

    configure = getattr(widget, "configure", None) or getattr(widget, "config", None)
    if configure is None:
        return

    try:
        configure(**options)
        return
    except Exception:
        pass

    # Fall back to applying each option in isolation so a single unsupported
    # option does not prevent the rest from being applied.
    for key, value in options.items():
        try:
            configure(**{key: value})
        except Exception:
            continue


def _iter_buttons(buttons: Any) -> Iterable[Any]:
    """Yield individual button widgets from a buttons container.

    Accepts a list/tuple/iterable of buttons, a dict of buttons, or ``None``.
    """
    if buttons is None:
        return []
    if isinstance(buttons, dict):
        return list(buttons.values())
    if isinstance(buttons, (list, tuple, set)):
        return list(buttons)
    # Fall back to treating it as an iterable; if it is not iterable, wrap it.
    try:
        return list(buttons)
    except TypeError:
        return [buttons]


class ThemeManager:
    """Applies themes to GUI widgets and tracks the single active theme."""

    THEMES: dict[str, Theme] = THEMES

    def __init__(self) -> None:
        # Classic is the default active theme at startup (Requirement 6.1).
        self.active: str = "Classic"

    def apply(self, theme_name: str, widgets: Any) -> None:
        """Apply a theme's colors and fonts to the GUI widgets.

        Applies the named theme to the Display, all buttons, and the theme
        selector, then records ``theme_name`` as the single active theme
        (Requirement 6.3-6.5, 6.7). Does not modify calculator state
        (Requirement 6.6).

        Args:
            theme_name: One of ``"Classic"``, ``"Dark"``, or ``"Fun"``.
            widgets: A container of widget references. May expose ``display``,
                ``buttons`` (iterable/dict), and ``selector`` attributes, or the
                equivalent mapping keys. Missing widgets are tolerated.

        Raises:
            KeyError: If ``theme_name`` is not a known theme.
        """
        theme = self.THEMES[theme_name]

        font = (theme.font_family, theme.font_size)

        display = _get_widget(widgets, "display")
        buttons = _get_widget(widgets, "buttons")
        selector = _get_widget(widgets, "selector")

        _configure_widget(
            display,
            {
                "bg": theme.display_bg,
                "fg": theme.display_fg,
                "font": font,
            },
        )

        # Buttons are tk.Label widgets (see gui.py) which honor bg/fg/font on
        # every platform, including macOS.
        for button in _iter_buttons(buttons):
            _configure_widget(
                button,
                {
                    "bg": theme.button_bg,
                    "fg": theme.button_fg,
                    "font": font,
                },
            )

        # The selector is a Menubutton-based OptionMenu; highlightbackground is
        # set alongside bg so the accent color renders on macOS as well.
        _configure_widget(
            selector,
            {
                "bg": theme.accent,
                "fg": theme.button_fg,
                "font": font,
                "highlightbackground": theme.accent,
                "activebackground": theme.accent,
                "activeforeground": theme.button_fg,
            },
        )

        # Exactly one theme is active at any time (Requirement 6.7).
        self.active = theme_name


def _get_widget(widgets: Any, key: str) -> Any:
    """Fetch a widget reference from either an attribute or a mapping key."""
    if widgets is None:
        return None
    value = getattr(widgets, key, None)
    if value is not None:
        return value
    if isinstance(widgets, dict):
        return widgets.get(key)
    try:
        return widgets[key]
    except (TypeError, KeyError, IndexError):
        return None
