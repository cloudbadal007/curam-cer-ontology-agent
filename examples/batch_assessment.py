#!/usr/bin/env python3
"""
Batch eligibility assessment example.

Processes multiple households in one run.
"""

from curam_cer_agent.agent.eligibility_agent import CaseData, EligibilityAgent


def main() -> None:
    cases = [
        CaseData(
            household_id="BATCH-01",
            program_code="SNAP",
            household_size=1,
            gross_monthly_income=1500,
            state="CA",
            identity_verified=True,
        ),
        CaseData(
            household_id="BATCH-02",
            program_code="SNAP",
            household_size=4,
            gross_monthly_income=4000,
            state="TX",
            identity_verified=True,
        ),
        CaseData(
            household_id="BATCH-03",
            program_code="SNAP",
            household_size=2,
            gross_monthly_income=1800,
            state="NY",
            identity_verified=False,
        ),
    ]
    agent = EligibilityAgent()
    decisions = agent.batch_assess(cases)
    print("Batch assessment results:")
    for d in decisions:
        print(f"  {d.household_id}: {d.status.value}")


if __name__ == "__main__":
    main()
