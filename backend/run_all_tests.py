"""
Run every backend test suite and print one combined total.

Individually running seven files and adding up the numbers by hand is
the kind of thing that quietly goes wrong. This does it in one command
and exits non-zero if anything failed, so it can be used as a single
"is the project healthy?" check.

    cd backend
    ./venv/Scripts/python.exe run_all_tests.py

The suites are independent of each other on purpose - each creates and
removes its own accounts and products. That matters: if they shared
state, a failure in one would look like a failure in another, which is
exactly the bug this project hit once already (see PROJECT-REPORT.md
section 9.3).
"""

import re
import subprocess
import sys

# Order matters only for readability - cheapest first.
SUITES = [
    ("test_auth.py", "Registration, login, password hashing"),
    ("test_products.py", "Product CRUD, roles, ownership fencing"),
    ("test_cart.py", "Cart, stock capping, cart privacy"),
    ("test_orders.py", "Checkout, stock refusal, status workflow"),
    ("test_reviews.py", "Reviews, the purchase gate, averages"),
    ("test_recommendations.py", "The TF-IDF engine and its fallbacks"),
    ("test_admin.py", "Admin panel, and what it refuses"),
]

RESULT_PATTERN = re.compile(r"RESULT:\s*(\d+)\s*passed,\s*(\d+)\s*failed")


def main():
    print("=" * 70)
    print("SMARTCART - FULL BACKEND TEST RUN")
    print("=" * 70)

    total_passed = 0
    total_failed = 0
    results = []

    for filename, description in SUITES:
        print(f"\n>>> {filename}  ({description})")
        print("-" * 70)

        try:
            process = subprocess.run(
                [sys.executable, filename],
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            print(f"    TIMED OUT after 300 seconds")
            results.append((filename, None, None))
            total_failed += 1
            continue

        output = process.stdout + process.stderr

        # Print only the failure lines and the summary. Printing all the
        # [PASS] lines for every suite buries the thing you are looking
        # for - which is whether anything went wrong.
        for line in output.splitlines():
            stripped = line.strip()

            if "[FAIL]" in stripped or "Traceback" in stripped:
                print(f"    {stripped}")

        if process.returncode != 0 and "RESULT:" not in output:
            print(f"    CRASHED (exit {process.returncode})")
            tail = output.strip().splitlines()[-6:]
            for line in tail:
                print(f"      {line}")

        match = RESULT_PATTERN.search(output)

        if match:
            passed = int(match.group(1))
            failed = int(match.group(2))

            total_passed += passed
            total_failed += failed

            results.append((filename, passed, failed))

            mark = "OK  " if failed == 0 else "FAIL"
            print(f"    [{mark}] {passed} passed, {failed} failed")
        else:
            results.append((filename, None, None))
            print("    [FAIL] no RESULT line - the suite did not finish")

    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for filename, passed, failed in results:
        if passed is None:
            print(f"  {filename:<28} DID NOT COMPLETE")
        else:
            status = "pass" if failed == 0 else "FAIL"
            print(f"  {filename:<28} {passed:>4} passed, {failed} failed   [{status}]")

    print("-" * 70)
    print(f"  {'TOTAL':<28} {total_passed:>4} passed, {total_failed} failed")
    print("=" * 70)

    if total_failed == 0:
        print("\nEverything passed.")
        print("\nNote: these suites are self-cleaning, so your database is")
        print("unchanged. To build the demo shop, run seed_demo_data.py.")
        return 0

    print(f"\n{total_failed} assertion(s) failed - review the output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
