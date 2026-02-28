#!/usr/bin/env python3
"""
Period eligibility check example.

Assesses eligibility for a date range (e.g., month-by-month).
"""

from curam_cer_agent.mcp.tools import check_period_eligibility


def main() -> None:
    household = {
        "household_size": 2,
        "gross_monthly_income": 2000,
        "state": "CA",
        "identity_verified": True,
    }
    periods = check_period_eligibility(
        household_id="DEMO-002",
        program_code="SNAP",
        period_start="2026-02-01",
        period_end="2026-02-28",
        household=household,
    )
    print("Period eligibility results:")
    for p in periods:
        print(f"  {p['period_start']} to {p['period_end']}: {p['status']}")
        print(f"    {p['explanation']}")


if __name__ == "__main__":
    main()
