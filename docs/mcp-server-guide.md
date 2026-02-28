# MCP Server Guide

## Overview

The eligibility MCP server exposes five tools for AI agents and other clients.

## Tools

| Tool                         | Inputs                                             | Output                  |
|------------------------------|----------------------------------------------------|-------------------------|
| assess_household_eligibility | household_id, program_code, assessment_date, household | EligibilityDecision      |
| check_period_eligibility     | household_id, program_code, period_start, period_end, household | List of period results  |
| explain_eligibility_decision | decision_id, audience, decision_data              | Explanation text        |
| get_applicable_programs      | state, household_size, monthly_income             | List of programs        |
| validate_evidence_completeness | household_id, program_code, evidence_submitted  | Missing evidence list   |

## Running the Server

```bash
python -m curam_cer_agent.mcp.server
```

Configurable via .env: `MCP_SERVER_PORT`, `MCP_SERVER_HOST`.

## Health Check

`GET http://localhost:8080/health` returns `{"status":"ok"}`.

## Connecting from a Client

Use Streamable HTTP transport. Connect to `http://localhost:8080/mcp`.

## Tool Invocation Example

```json
{
  "tool": "assess_household_eligibility",
  "arguments": {
    "household_id": "H1",
    "program_code": "SNAP",
    "assessment_date": "2026-02-23",
    "household": {
      "household_size": 3,
      "gross_monthly_income": 2500,
      "state": "CA",
      "identity_verified": true
    }
  }
}
```
