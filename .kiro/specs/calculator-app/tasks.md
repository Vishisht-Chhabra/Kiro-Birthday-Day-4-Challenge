# Implementation Plan: Calculator App

## Overview

This plan builds the Calculator_App from the inside out, following the design's strict dependency direction. It starts with the pure, framework-independent logic (`Arithmetic_Engine`, then `CalculatorState`), layers the `Theme_Manager`, and finishes with the thin Tkinter `GUI` and application entry point that wires everything together. Property-based tests (Hypothesis) are placed immediately after the pure logic they validate so correctness issues surface early, while UI, theming, and timing concerns are covered with smoke, integration, and timed example tests. Each of the 14 design properties maps to exactly one property-based test.

## Tasks

- [x] 1. Set up project structure and testing framework
  - Create the package directory structure (e.g. `calculator/` for source, `tests/` for tests)
  - Add `__init__.py` files and a `requirements.txt`/`pyproject.toml` pinning `pytest` and `hypothesis`
  - Configure pytest so both pure-logic tests and GUI tests can be discovered and run
  - _Requirements: 5.1_

- [x] 2. Implement the Arithmetic_Engine
  - [x] 2.1 Implement the pure arithmetic engine
    - Create `calculator/arithmetic_engine.py` defining `Operator`, `EvalError`, frozen `Ok`/`Err` dataclasses, the `EvalResult` alias, and `evaluate(left, operator, right)`
    - Compute add/subtract/multiply/divide; return `Err(EvalError.DIVIDE_BY_ZERO)` when dividing by zero instead of raising
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 3.1_

  - [x] 2.2 Write property test for arithmetic evaluation
    - **Property 6: Evaluation matches the reference operation**
    - **Validates: Requirements 2.5, 2.6, 5.5**
    - Use Hypothesis (min 100 iterations) over operand and operator strategies; tag with `# Feature: calculator-app, Property 6: ...`

- [x] 3. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement CalculatorState data model and numeric input
  - [x] 4.1 Create the state model and digit/decimal entry
    - Create `calculator/calculator_state.py` with `Mode`, the `MAX_OPERAND_DIGITS`/`MAX_SIGNIFICANT_DIGITS` constants, and the frozen `CalculatorState` dataclass
    - Implement `press_digit` (append with 15-digit cap) and `press_decimal` (single decimal, leading-zero rule)
    - Implement a `display_string()` that renders EDITING states (empty → `"0"`, otherwise `left` + operator symbol + `right`)
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 4.1, 5.2_

  - [x] 4.2 Write property test for digit entry
    - **Property 1: Digit append respects the 15-digit cap**
    - **Validates: Requirements 1.1, 1.6**

  - [x] 4.3 Write property test for decimal handling
    - **Property 2: Decimal point handling**
    - **Validates: Requirements 1.2, 1.3, 1.5**

- [x] 5. Implement operator entry
  - [x] 5.1 Implement `press_operator`
    - Record the selected operator when there is at least one operand and no pending operator
    - Replace the recorded operator when one exists but no second operand has been entered
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7_

  - [x] 5.2 Write property test for operator recording
    - **Property 4: Operator recording**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 5.3 Write property test for operator replacement
    - **Property 5: Operator replacement when no second operand exists**
    - **Validates: Requirements 2.7**

- [x] 6. Implement equals, evaluation, and terminal-display transitions
  - [x] 6.1 Implement `press_equals` and result/error handling
    - Guard equals so it only computes with exactly two operands and one operator (otherwise return unchanged)
    - Parse operands to `float`, call `Arithmetic_Engine.evaluate`, format `Ok` results to ≤10 significant digits, and transition to `Mode.RESULT`
    - On `Err(DIVIDE_BY_ZERO)`, transition to `Mode.ERROR` and make `display_string()` return `"Cannot divide by zero"`, retaining the state until clear/digit
    - Update `press_digit` so that pressing a digit in RESULT or ERROR mode starts a fresh EDITING expression containing only that digit
    - Extend `display_string()` to render RESULT and ERROR modes
    - _Requirements: 1.4, 2.5, 2.6, 2.8, 3.1, 3.2, 3.3, 3.5, 5.5_

  - [x] 6.2 Write property test for fresh expression from a terminal display
    - **Property 3: Digit from a terminal display starts a fresh expression**
    - **Validates: Requirements 1.4, 3.5**

  - [x] 6.3 Write property test for equals on incomplete expressions
    - **Property 7: Equals is a no-op on incomplete expressions**
    - **Validates: Requirements 2.8**

  - [x] 6.4 Write property test for division by zero
    - **Property 8: Division by zero yields an error, never a numeric result**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 7. Implement clear and delete
  - [x] 7.1 Implement `press_clear` and `press_delete`
    - `press_clear`: reset to an empty expression from any mode; display shows a single zero
    - `press_delete`: in EDITING mode remove the most recent character, flooring at `"0"` for empty/single-character expressions; in RESULT mode leave the result unchanged
    - _Requirements: 3.4, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 7.2 Write property test for clear
    - **Property 9: Clear resets to a single zero from any state**
    - **Validates: Requirements 4.1, 3.4**

  - [x] 7.3 Write property test for delete
    - **Property 10: Delete removes the last character with a floor at zero**
    - **Validates: Requirements 4.2, 4.3, 4.4**

  - [x] 7.4 Write property test for delete on a displayed result
    - **Property 11: Delete does not alter a displayed result**
    - **Validates: Requirements 4.5**

  - [x] 7.5 Write property test for total display rendering
    - **Property 12: Display rendering is total**
    - **Validates: Requirements 5.4**
    - Generate reachable states via sequences of transitions and assert `display_string()` always returns a non-empty string without raising

- [x] 8. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement the Theme_Manager
  - [x] 9.1 Implement `Theme` and `ThemeManager`
    - Create `calculator/theme_manager.py` with the frozen `Theme` dataclass and a `THEMES` dict containing exactly `Classic`, `Dark`, and `Fun`
    - Initialize `active` to `"Classic"` and implement `apply(theme_name, widgets)` to set colors/fonts on the Display, all buttons, and the selector, updating `active` without touching calculator state
    - _Requirements: 6.1, 6.2, 6.7_

  - [x] 9.2 Write property test for theme state preservation
    - **Property 13: Applying a theme preserves calculator state**
    - **Validates: Requirements 6.6**

  - [x] 9.3 Write property test for single active theme
    - **Property 14: Exactly one theme is active**
    - **Validates: Requirements 6.7**

  - [x] 9.4 Write unit tests for Theme_Manager defaults
    - Assert `active == "Classic"` on init and `THEMES` keys are exactly `{"Classic", "Dark", "Fun"}`
    - _Requirements: 6.1, 6.2_

- [x] 10. Implement the Tkinter GUI
  - [x] 10.1 Build the GUI view/controller
    - Create `calculator/gui.py` with `CalculatorGUI` that renders the Display, a button for each digit 0–9, decimal, four operators, equals, clear, delete, and a three-option theme selector
    - Own a single `CalculatorState`; map button clicks to state transitions via `_on_button` and reflect state through `_refresh_display`
    - Initialize the Display to zero, apply the Classic theme by default, and route selector changes to `Theme_Manager` via `_on_theme_selected`, showing the active-theme indicator
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.8_

  - [x] 10.2 Write smoke test for GUI construction
    - Construct the GUI and assert the Display and a button for every token (digits 0–9, decimal, four operators, equals, clear, delete) exist
    - _Requirements: 5.1_

  - [x] 10.3 Write integration tests for theme application
    - Apply Classic, Dark, and Fun and assert representative widget option values (background, foreground, font) match each theme on the Display, buttons, and selector
    - _Requirements: 6.3, 6.4, 6.5, 6.8_

  - [x] 10.4 Write timing example tests
    - Assert equals computes within 200 ms, button-to-display update within 200 ms, theme apply within 1 s, and startup render within 3 s
    - _Requirements: 2.5, 5.1, 5.3, 6.3, 6.4, 6.5_

- [x] 11. Wire the application entry point
  - [x] 11.1 Implement `main()`
    - Create `calculator/__main__.py` (or `main.py`) that constructs the Tk root, instantiates `CalculatorGUI`, and starts the main loop
    - _Requirements: 5.1, 5.2, 6.1_

- [x] 12. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation tasks are never optional.
- Each task references specific requirements for traceability, and each property test references its design property number.
- Property-based tests use Hypothesis with a minimum of 100 iterations and are tagged with the required `# Feature: calculator-app, Property {n}: ...` comment.
- Pure-logic tests (Properties 1–11, and Property 12 over `CalculatorState`) have no display dependency; GUI smoke/integration/timing tests require a display server (use `xvfb` in headless CI).
- Checkpoints ensure incremental validation at natural boundaries.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "9.1"] },
    { "id": 2, "tasks": ["2.2", "4.1", "9.2", "9.3", "9.4"] },
    { "id": 3, "tasks": ["4.2", "4.3", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3", "6.4", "7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3", "7.4", "7.5", "10.1"] },
    { "id": 7, "tasks": ["10.2", "10.3", "10.4", "11.1"] }
  ]
}
```
