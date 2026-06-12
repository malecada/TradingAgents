"""Conftest for agents tests.

Pre-stubs heavy package __init__ chains so individual agent modules
can be imported without requiring all LLM provider dependencies.
"""
from __future__ import annotations

import sys
import types


def _stub_package(name: str) -> types.ModuleType:
    """Create a bare stub module and register it in sys.modules."""
    if name in sys.modules:
        return sys.modules[name]
    stub = types.ModuleType(name)
    stub.__path__ = []  # make it a package
    stub.__package__ = name
    sys.modules[name] = stub
    return stub


def _ensure_parent_stubs(dotted_name: str) -> None:
    """Ensure all parent package stubs exist for a dotted module name."""
    parts = dotted_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            _stub_package(parent)
