"""
Configuration management for curam-cer-ontology-agent.

Loads settings from environment variables and .env file.
All configuration is centralized here for consistency.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env — prefer cwd (project root when running from repo)
_project_root = Path.cwd()
_load_path = Path(__file__).resolve().parent.parent.parent.parent
if (_load_path / ".env").exists():
    load_dotenv(_load_path / ".env")
else:
    load_dotenv(_project_root / ".env")


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.environ.get(key, default)


def get_env_required(key: str) -> str:
    """Get required environment variable; raises if missing."""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def get_ontology_path() -> Path:
    """Path to the core ontology file."""
    path_str = get_env("ONTOLOGY_PATH", "./ontology/eligibility_core.ttl")
    p = Path(path_str)
    if not p.is_absolute():
        # Try cwd first (project root when running from repo)
        base = Path.cwd() / p
        if base.exists():
            return base
        # Fallback: package layout src/curam_cer_agent/... so ontology is sibling of src
        pkg_root = Path(__file__).resolve().parent.parent.parent.parent
        alt = pkg_root / "ontology" / "eligibility_core.ttl"
        if alt.exists():
            return alt
        p = base
    return p


def get_mcp_server_port() -> int:
    """MCP server port (default 8080)."""
    return int(get_env("MCP_SERVER_PORT", "8080"))


def get_mcp_server_host() -> str:
    """MCP server host (default localhost)."""
    return get_env("MCP_SERVER_HOST", "localhost")


def get_log_level() -> str:
    """Logging level (default INFO)."""
    return get_env("LOG_LEVEL", "INFO")


def get_audit_log_path() -> Path:
    """Path to audit log file."""
    path_str = get_env("AUDIT_LOG_PATH", "./logs/audit.log")
    p = Path(path_str)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p


def get_llm_provider() -> str:
    """LLM provider: openai or anthropic."""
    return get_env("LLM_PROVIDER", "openai")


def get_llm_model() -> str:
    """LLM model name (e.g., gpt-4o, claude-sonnet-4-6)."""
    return get_env("LLM_MODEL", "gpt-4o")
