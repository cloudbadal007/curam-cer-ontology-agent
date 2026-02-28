"""
MCP (Model Context Protocol) server for eligibility tools.

Exposes assess_household_eligibility, check_period_eligibility,
explain_eligibility_decision, get_applicable_programs, and
validate_evidence_completeness as MCP tools. Runs on port 8080
by default (configurable via .env). Includes health check endpoint.
"""

import contextlib
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from curam_cer_agent.mcp.tools import (
    assess_household_eligibility,
    check_period_eligibility,
    explain_eligibility_decision,
    get_applicable_programs,
    validate_evidence_completeness,
)
from curam_cer_agent.utils.config import get_mcp_server_host, get_mcp_server_port

logger = logging.getLogger(__name__)

def _create_mcp() -> FastMCP:
    """Create and configure the FastMCP server with all tools."""
    mcp = FastMCP(
        name="curam-cer-eligibility",
        instructions="Eligibility determination tools for government benefit programs. Use ontology-backed rules only.",
        json_response=True,
    )

    @mcp.tool()
    def assess_household_eligibility_tool(
        household_id: str,
        program_code: str,
        assessment_date: str,
        household: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Assess household eligibility for a program.

        Input: household_id, program_code (e.g. SNAP, MEDICAID), assessment_date (ISO),
        household dict with size, gross_monthly_income, state, identity_verified.
        Output: EligibilityDecision with full audit trail.
        """
        return assess_household_eligibility(
            household_id=household_id,
            program_code=program_code,
            assessment_date=assessment_date,
            household=household,
        )

    @mcp.tool()
    def check_period_eligibility_tool(
        household_id: str,
        program_code: str,
        period_start: str,
        period_end: str,
        household: dict[str, Any],
    ) -> list[dict]:
        """
        Check eligibility for a date range (period-by-period).

        Replicates Cúram week-by-week period eligibility. Input: household_id,
        program_code, period_start, period_end, household dict.
        Output: List of period-level determinations.
        """
        return check_period_eligibility(
            household_id=household_id,
            program_code=program_code,
            period_start=period_start,
            period_end=period_end,
            household=household,
        )

    @mcp.tool()
    def explain_eligibility_decision_tool(
        decision_id: str,
        audience: str,
        decision_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Explain an eligibility decision in plain English.

        audience: case_worker | applicant | auditor. decision_data: full
        decision object from assess_household_eligibility.
        """
        return explain_eligibility_decision(
            decision_id=decision_id,
            audience=audience,
            decision_data=decision_data,
        )

    @mcp.tool()
    def get_applicable_programs_tool(
        state: str,
        household_size: int,
        monthly_income: float,
    ) -> list[dict]:
        """
        Get programs the household may qualify for.

        Input: state (2-letter), household_size, monthly_income.
        Output: List of programs where income threshold could be met.
        """
        return get_applicable_programs(
            state=state,
            household_size=household_size,
            monthly_income=monthly_income,
        )

    @mcp.tool()
    def validate_evidence_completeness_tool(
        household_id: str,
        program_code: str,
        evidence_submitted: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate evidence completeness before determination.

        Returns list of missing evidence types. Input: household_id,
        program_code, evidence_submitted (dict of type -> bool/list).
        """
        return validate_evidence_completeness(
            household_id=household_id,
            program_code=program_code,
            evidence_submitted=evidence_submitted or {},
        )

    return mcp


async def health_check(_request: object) -> JSONResponse:
    """Health check endpoint for load balancers and monitoring."""
    return JSONResponse({"status": "ok", "service": "curam-cer-eligibility-mcp"})


def run_server() -> None:
    """Run the MCP server with health check on configured host/port."""
    host = get_mcp_server_host()
    port = get_mcp_server_port()
    mcp = _create_mcp()
    mcp.settings.host = host
    mcp.settings.port = port

    # Mount MCP at /mcp and health at /
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    app = Starlette(
        routes=[
            Route("/health", health_check),
            Mount("/mcp", app=mcp.streamable_http_app()),
        ],
        lifespan=lifespan,
    )

    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
