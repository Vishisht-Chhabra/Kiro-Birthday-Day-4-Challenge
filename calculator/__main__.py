"""Application entry point for the Calculator_App.

Running ``python -m calculator`` constructs the Tk root window, instantiates
:class:`~calculator.gui.CalculatorGUI` (which renders the Display, buttons, and
theme selector, initializes the Display to zero, and applies the Classic theme
by default), and starts the Tk main loop.

Importing this module has no side effects: the Tk root is only created and the
main loop only started when :func:`main` is called, which happens under the
``if __name__ == "__main__"`` guard.

Requirements: 5.1 (render Display and buttons on startup), 5.2 (Display shows
zero on startup), 6.1 (Classic theme applied by default).
"""

from __future__ import annotations

import tkinter as tk

from calculator.gui import CalculatorGUI


def main() -> None:
    """Construct the Tk root, build the GUI, and run the main loop."""
    root = tk.Tk()
    CalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
