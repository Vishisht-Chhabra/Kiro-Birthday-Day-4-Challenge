"""Arithmetic_Engine: a pure, side-effect-free evaluation module.

Evaluates two-operand expressions and reports errors (such as division by
zero) as explicit return values rather than exceptions. This module has no
knowledge of Tkinter and performs no I/O or global state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Operator(Enum):
    """Supported arithmetic operators, keyed by their display symbol."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"


class EvalError(Enum):
    """Explicit error indicators returned by :func:`evaluate`."""

    DIVIDE_BY_ZERO = "divide_by_zero"


@dataclass(frozen=True)
class Ok:
    """A successful evaluation carrying the numeric result."""

    value: float


@dataclass(frozen=True)
class Err:
    """A failed evaluation carrying an :class:`EvalError` indicator."""

    error: EvalError


EvalResult = Ok | Err


def evaluate(left: float, operator: Operator, right: float) -> EvalResult:
    """Apply ``operator`` to the two operands.

    Returns ``Err(EvalError.DIVIDE_BY_ZERO)`` when the operator is division and
    the divisor is zero; otherwise returns ``Ok(value)`` with the computed
    result. This function never raises for the divide-by-zero case.
    """

    if operator is Operator.ADD:
        return Ok(left + right)
    if operator is Operator.SUBTRACT:
        return Ok(left - right)
    if operator is Operator.MULTIPLY:
        return Ok(left * right)
    if operator is Operator.DIVIDE:
        if right == 0:
            return Err(EvalError.DIVIDE_BY_ZERO)
        return Ok(left / right)

    raise ValueError(f"Unsupported operator: {operator!r}")
