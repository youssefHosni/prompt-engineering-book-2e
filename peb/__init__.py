"""Shared helpers for the book's runnable examples.

The book prints the Anthropic version of `ask()` (Appendix A). That is what you
should use. This package adds one thing the book's listing leaves out: a fallback
to OpenRouter, because that is how the measurements in the book were actually
gathered, and Chapter 2 §2.5 is honest about the tradeoff.
"""
from .client import ask, run_tools, MODELS, backend

__all__ = ["ask", "run_tools", "MODELS", "backend"]
