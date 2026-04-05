"""Audit logging for MCP tool invocations.

Provides structured logging of every tool call (name, parameters, status,
duration) for audit-trail purposes.  Parameters are sanitised so that large
text values (e.g. full note contents) are truncated.
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastmcp import FastMCP

# Dedicated audit logger — callers can attach their own handlers / formatters
# without affecting the rest of the application's logging.
audit_logger = logging.getLogger("mdvault_mcp.audit")

# Truncation threshold for individual parameter values (characters).
_MAX_PARAM_VALUE_LEN = 200


def _sanitise_params(params: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *params* with long string values truncated."""
    sanitised: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, str) and len(value) > _MAX_PARAM_VALUE_LEN:
            sanitised[key] = value[:_MAX_PARAM_VALUE_LEN] + f"... ({len(value)} chars)"
        else:
            sanitised[key] = value
    return sanitised


def _build_call_params(fn, args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Map positional + keyword arguments back to parameter names."""
    sig = inspect.signature(fn)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def _wrap_tool_fn(tool_name: str, original_fn):
    """Return a wrapper that logs before/after every call to *original_fn*."""

    @functools.wraps(original_fn)
    def wrapper(*args, **kwargs):
        params = _build_call_params(original_fn, args, kwargs)
        safe_params = _sanitise_params(params)

        audit_logger.info(
            "tool_call tool=%s params=%s",
            tool_name,
            json.dumps(safe_params, default=str),
        )

        start = time.monotonic()
        try:
            result = original_fn(*args, **kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000
            audit_logger.info(
                "tool_result tool=%s status=ok duration_ms=%.1f",
                tool_name,
                elapsed_ms,
            )
            return result
        except Exception:
            elapsed_ms = (time.monotonic() - start) * 1000
            audit_logger.warning(
                "tool_result tool=%s status=error duration_ms=%.1f",
                tool_name,
                elapsed_ms,
                exc_info=True,
            )
            raise

    return wrapper


def install_audit_logging(mcp: FastMCP) -> None:
    """Wrap every registered tool's ``fn`` with audit logging.

    Call this **after** all ``register_*_tools()`` calls so that every tool
    is already present in the tool manager.
    """
    tools = mcp._tool_manager._tools
    for name, tool in tools.items():
        tool.fn = _wrap_tool_fn(name, tool.fn)
    audit_logger.debug("audit logging installed for %d tools", len(tools))
