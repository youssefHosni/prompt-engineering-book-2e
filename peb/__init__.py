"""Shared helpers for the book's runnable examples.

The book prints the Anthropic version of `ask()` (Appendix A), and that is what
you should use. Its three guard clauses and its `system=` parameter are the same
here; the only difference is a fallback to OpenRouter, because that is how the
measurements in the book were gathered. §2.5 and Appendix A both disclose it,
and §2.5 is the argument for not shipping against it.
"""
from .client import ask, run_tools, MODELS, backend

__all__ = ["ask", "run_tools", "MODELS", "backend"]
