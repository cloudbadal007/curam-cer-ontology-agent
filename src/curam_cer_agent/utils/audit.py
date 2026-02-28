"""
Audit trail generation for eligibility determinations.

Logs tool invocations and decisions for compliance and debugging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from curam_cer_agent.utils.config import get_audit_log_path

logger = logging.getLogger(__name__)


def log_tool_invocation(
    tool_name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    duration_ms: float | None = None,
) -> None:
    """
    Log an MCP tool invocation for audit purposes.

    Writes to both the application logger and the audit log file
    (when AUDIT_LOG_PATH is configured).
    """
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "arguments": arguments,
        "result_summary": {
            "status": result.get("status", "unknown"),
            "decision_id": result.get("decision_id"),
        }
        if "status" in result or "decision_id" in result
        else {"keys": list(result.keys())},
        "duration_ms": duration_ms,
    }
    logger.info("Tool invocation: %s", json.dumps(audit_entry, default=str))

    audit_path = get_audit_log_path()
    try:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry, default=str) + "\n")
    except OSError as e:
        logger.warning("Could not write to audit log %s: %s", audit_path, e)
