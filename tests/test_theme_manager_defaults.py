"""Unit tests for Theme_Manager default state.

Covers the initial-condition example tests called out in the design's
Unit / Example Tests section:
  - A freshly constructed ThemeManager initializes with active == "Classic"
    (Requirement 6.1).
  - ThemeManager.THEMES keys are exactly {"Classic", "Dark", "Fun"}
    (Requirement 6.2).
"""

from calculator.theme_manager import ThemeManager, THEMES


def test_active_defaults_to_classic_on_init():
    """A fresh ThemeManager starts with the Classic theme active (Req 6.1)."""
    manager = ThemeManager()
    assert manager.active == "Classic"


def test_themes_keys_are_exactly_the_three_named_themes():
    """THEMES offers exactly the three selectable themes (Req 6.2)."""
    assert set(ThemeManager.THEMES.keys()) == {"Classic", "Dark", "Fun"}


def test_module_themes_matches_class_themes():
    """The module-level THEMES and the class attribute refer to the same set."""
    assert set(THEMES.keys()) == {"Classic", "Dark", "Fun"}
    assert ThemeManager.THEMES is THEMES


def test_each_theme_name_matches_its_key():
    """Each Theme's name field matches its dict key (Req 6.2)."""
    for key, theme in ThemeManager.THEMES.items():
        assert theme.name == key
