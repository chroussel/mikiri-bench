#!/usr/bin/env python3
"""Score mikiri-bench results against ground truth manifests."""
import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).parent
CASES_DIR = BENCH_DIR / "cases"
RESULTS_DIR = BENCH_DIR / "results"


def load_manifest(case_dir: Path) -> dict:
    with open(case_dir / "manifest.json") as f:
        return json.load(f)


def load_result(result_dir: Path) -> dict | None:
    output = result_dir / "output.json"
    if not output.exists():
        return None
    with open(output) as f:
        return json.load(f)


def match_issue(expected: dict, findings: list[dict]) -> bool:
    """Check if an expected issue was detected in mikiri's output.

    Matches on endpoint and issue type. This is intentionally loose —
    refine as the output format stabilizes.
    """
    endpoint = expected["endpoint"]
    issue_type = expected["type"]

    for finding in findings:
        # Match against optimization_targets or similar output structures
        finding_str = json.dumps(finding).lower()
        # Check if the endpoint appears in the finding
        # Normalize endpoint patterns: /api/users/{user_id}/orders -> /api/users/*/orders
        endpoint_normalized = endpoint.replace("{user_id}", "").replace("{id}", "")
        endpoint_parts = [p for p in endpoint_normalized.split("/") if p]

        endpoint_match = all(part in finding_str for part in endpoint_parts)
        type_match = issue_type.replace("_", " ") in finding_str or issue_type in finding_str

        if endpoint_match and type_match:
            return True

    return False


def score_case(case_name: str) -> dict:
    case_dir = CASES_DIR / case_name
    result_dir = RESULTS_DIR / case_name

    manifest = load_manifest(case_dir)
    result = load_result(result_dir)

    issues = manifest["issues"]
    total = len(issues)

    if result is None:
        return {
            "case": case_name,
            "total": total,
            "detected": 0,
            "missed": total,
            "status": "no_result",
            "details": [],
        }

    # Extract findings from mikiri output
    # The structure depends on mikiri's --json output format
    findings = result.get("optimization_targets", [])
    if not findings:
        # Try alternative paths in the output
        findings = result.get("findings", [])
        if not findings:
            # Flatten the entire result as a single finding for loose matching
            findings = [result]

    detected = 0
    details = []
    for issue in issues:
        found = match_issue(issue, findings)
        if found:
            detected += 1
        details.append({
            "type": issue["type"],
            "endpoint": issue["endpoint"],
            "severity": issue["severity"],
            "detected": found,
        })

    return {
        "case": case_name,
        "total": total,
        "detected": detected,
        "missed": total - detected,
        "status": "ok",
        "details": details,
    }


def print_table(scores: list[dict]):
    """Print a summary table."""
    total_issues = sum(s["total"] for s in scores)
    total_detected = sum(s["detected"] for s in scores)

    print()
    print(f"mikiri-bench scorecard")
    print(f"={'=' * 55}")
    print(f"{'Case':<30} {'Issues':>6} {'Found':>6} {'Missed':>6}")
    print(f"{'-' * 30} {'-' * 6} {'-' * 6} {'-' * 6}")

    for s in scores:
        status = "" if s["status"] == "ok" else f" ({s['status']})"
        print(f"{s['case']:<30} {s['total']:>6} {s['detected']:>6} {s['missed']:>6}{status}")

    print(f"{'-' * 30} {'-' * 6} {'-' * 6} {'-' * 6}")
    print(f"{'TOTAL':<30} {total_issues:>6} {total_detected:>6} {total_issues - total_detected:>6}")
    print()

    if total_issues > 0:
        rate = total_detected / total_issues * 100
        print(f"Detection rate: {total_detected}/{total_issues} ({rate:.1f}%)")
    print()


def main():
    fmt = "table"
    if "--json" in sys.argv:
        fmt = "json"

    case_dirs = sorted(CASES_DIR.iterdir())
    scores = []

    for case_dir in case_dirs:
        if not case_dir.is_dir():
            continue
        manifest_path = case_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        scores.append(score_case(case_dir.name))

    if fmt == "json":
        scorecard = {
            "total_issues": sum(s["total"] for s in scores),
            "total_detected": sum(s["detected"] for s in scores),
            "detection_rate": (
                sum(s["detected"] for s in scores) / sum(s["total"] for s in scores)
                if sum(s["total"] for s in scores) > 0
                else 0
            ),
            "cases": scores,
        }
        print(json.dumps(scorecard, indent=2))
    else:
        print_table(scores)


if __name__ == "__main__":
    main()
