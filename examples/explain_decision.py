#!/usr/bin/env python3
"""
Explain eligibility decision example.

Generates audience-specific explanations (case worker, applicant, auditor).
"""

from curam_cer_agent.agent.eligibility_agent import CaseData, EligibilityAgent
from curam_cer_agent.mcp.tools import explain_eligibility_decision


def main() -> None:
    case = CaseData(
        household_id="EXPLAIN-001",
        program_code="SNAP",
        household_size=2,
        gross_monthly_income=2000,
        state="CA",
        identity_verified=True,
    )
    agent = EligibilityAgent()
    decision = agent.assess(case)
    decision_dict = decision.to_dict()

    for audience in ["case_worker", "applicant", "auditor"]:
        out = explain_eligibility_decision(
            decision_id=decision.decision_id,
            audience=audience,
            decision_data=decision_dict,
        )
        print(f"\n--- Explanation for {audience} ---")
        print(out.get("explanation", ""))
        if out.get("next_steps"):
            print("Next steps:", out["next_steps"])


if __name__ == "__main__":
    main()
