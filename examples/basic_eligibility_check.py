#!/usr/bin/env python3
"""
Basic eligibility check example.

Assesses a single household for SNAP eligibility using the agent.
No MCP server required — uses direct tool calls.
"""

from curam_cer_agent.agent.eligibility_agent import CaseData, EligibilityAgent


def main() -> None:
    case = CaseData(
        household_id="DEMO-001",
        program_code="SNAP",
        household_size=3,
        gross_monthly_income=2500.0,
        state="CA",
        identity_verified=True,
        assessment_date="2026-02-23",
    )
    agent = EligibilityAgent()
    decision = agent.assess(case)
    print("Eligibility Decision:")
    print(f"  Status: {decision.status.value}")
    print(f"  Program: {decision.program_code}")
    print(f"  Household: {decision.household_id}")
    print(f"  Explanation: {decision.explanation}")
    print(f"  Requires human review: {decision.requires_human_review}")
    print("  Rule executions:")
    for r in decision.rule_executions:
        print(f"    - {r.rule_id}: {'PASS' if r.rule_result else 'FAIL'} — {r.rule_reason}")


if __name__ == "__main__":
    main()
