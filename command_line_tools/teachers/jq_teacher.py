#!/usr/bin/env python3
"""Interactive jq teacher - practice jq against realistic JSONL app logs."""

import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

# ── ANSI colours ─────────────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def bold(t: str) -> str:
    return _c("1", t)


def green(t: str) -> str:
    return _c("32", t)


def red(t: str) -> str:
    return _c("31", t)


def yellow(t: str) -> str:
    return _c("33", t)


def cyan(t: str) -> str:
    return _c("36", t)


def dim(t: str) -> str:
    return _c("2", t)


# ── Log data generation ───────────────────────────────────────────────────────

SERVICES = ["auth", "payments", "orders", "inventory", "notifications"]
ENDPOINTS = {
    "auth": ["/login", "/logout", "/refresh", "/register"],
    "payments": ["/charge", "/refund", "/balance", "/methods"],
    "orders": ["/create", "/list", "/detail", "/cancel"],
    "inventory": ["/stock", "/reserve", "/release", "/adjust"],
    "notifications": ["/send", "/list", "/mark-read", "/preferences"],
}
LEVELS = ["info", "info", "info", "warn", "error"]  # weighted
METHODS = ["GET", "GET", "POST", "POST", "PUT", "DELETE"]
USER_IDS = [f"u{i:04d}" for i in range(1, 41)]  # 40 users
REQUEST_ID_CHARS = "abcdef0123456789"


def _req_id() -> str:
    return "".join(random.choices(REQUEST_ID_CHARS, k=8))


def generate_logs(n: int = 200) -> list[dict]:
    rng = random.Random(42)
    logs = []
    base_ts = 1_700_000_000
    for i in range(n):
        service = rng.choice(SERVICES)
        endpoint = rng.choice(ENDPOINTS[service])
        level = rng.choice(LEVELS)
        status = (
            rng.choice([200, 200, 200, 201, 204])
            if level == "info"
            else (
                rng.choice([400, 401, 403, 404, 429])
                if level == "warn"
                else rng.choice([500, 502, 503, 504])
            )
        )
        duration = round(rng.lognormvariate(4.5, 1.0), 1)  # ms, realistic spread
        user = rng.choice(USER_IDS + [None, None])  # some null users
        logs.append(
            {
                "timestamp": base_ts + i * rng.randint(1, 30),
                "level": level,
                "service": service,
                "endpoint": endpoint,
                "method": rng.choice(METHODS),
                "status_code": status,
                "duration_ms": duration,
                "user_id": user,
                "request_id": _req_id(),
                "metadata": {
                    "region": rng.choice(["us-east", "eu-west", "ap-south"]),
                    "retries": rng.choice([0, 0, 0, 1, 2]),
                    "cache_hit": rng.choice([True, True, False]),
                },
            }
        )
    return logs


# ── Problem definitions ───────────────────────────────────────────────────────
# Each problem is resolved against the actual generated log data at runtime.
# `answer_expr` is the reference jq expression (shown on skip/correct).
# `expected_fn` is a Python callable that computes the true answer from the logs.
# `sort_before_compare` controls whether order matters in comparison.


def _make_problems(logs: list[dict]) -> list[dict]:

    def run(expr: str) -> object:
        """Run a jq expression over logs serialised as a JSON array."""
        data = json.dumps(logs)
        result = subprocess.run(
            ["jq", "-c", expr],
            input=data,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [l for l in result.stdout.strip().splitlines() if l]
        if len(lines) == 1:
            return json.loads(lines[0])
        return [json.loads(l) for l in lines]

    # Precompute expected answers using jq itself (source of truth).
    problems = [
        {
            "title": "Count all log entries",
            "question": "Count the total number of log entries in the file.",
            "answer_expr": "jq '[.[]] | length' <LOGFILE>",
            "expected": run("[.[]] | length"),
            "sort_before_compare": False,
        },
        {
            "title": "Filter errors",
            "question": 'Output all log entries where level is "error" (full objects).',
            "answer_expr": "jq '.[] | select(.level == \"error\")' <LOGFILE>",
            "expected": run('[.[] | select(.level == "error")]'),
            "sort_before_compare": True,
        },
        {
            "title": "Unique services",
            "question": "List all unique service names (as a JSON array, any order).",
            "answer_expr": "jq '[.[].service] | unique' <LOGFILE>",
            "expected": run("[.[].service] | unique"),
            "sort_before_compare": True,
        },
        {
            "title": "Count errors per service",
            "question": (
                "Produce an object mapping each service name to the count of "
                "error-level entries for that service."
            ),
            "answer_expr": (
                'jq \'[.[] | select(.level=="error")] | '
                "group_by(.service) | map({(.[0].service): length}) | add' <LOGFILE>"
            ),
            "expected": run(
                '[.[] | select(.level=="error")] | '
                "group_by(.service) | map({(.[0].service): length}) | add"
            ),
            "sort_before_compare": False,
        },
        {
            "title": "Average duration",
            "question": "Calculate the average duration_ms across all log entries (rounded to 2 decimal places).",
            "answer_expr": (
                "jq '([.[].duration_ms] | add) / length | "
                ". * 100 | round / 100' <LOGFILE>"
            ),
            "expected": run(
                "([.[].duration_ms] | add) / length | . * 100 | round / 100"
            ),
            "sort_before_compare": False,
        },
        {
            "title": "Top 5 slowest requests",
            "question": (
                "Return an array of the 5 slowest requests (highest duration_ms), "
                "each as an object with only request_id and duration_ms, "
                "ordered slowest first."
            ),
            "answer_expr": (
                "jq '[.[] | {request_id, duration_ms}] | "
                "sort_by(.duration_ms) | reverse | .[0:5]' <LOGFILE>"
            ),
            "expected": run(
                "[.[] | {request_id, duration_ms}] | "
                "sort_by(.duration_ms) | reverse | .[0:5]"
            ),
            "sort_before_compare": False,
        },
        {
            "title": "Entries with null user_id",
            "question": "Count the number of log entries where user_id is null.",
            "answer_expr": "jq '[.[] | select(.user_id == null)] | length' <LOGFILE>",
            "expected": run("[.[] | select(.user_id == null)] | length"),
            "sort_before_compare": False,
        },
        {
            "title": "Drill into metadata region",
            "question": (
                "List all unique region values found inside the metadata object "
                "(as a JSON array, any order)."
            ),
            "answer_expr": "jq '[.[].metadata.region] | unique' <LOGFILE>",
            "expected": run("[.[].metadata.region] | unique"),
            "sort_before_compare": True,
        },
        {
            "title": "Status codes >= 500",
            "question": (
                "Output an array of distinct status_code values that are 500 or above, "
                "sorted ascending."
            ),
            "answer_expr": (
                "jq '[.[] | select(.status_code >= 500) | .status_code] "
                "| unique | sort' <LOGFILE>"
            ),
            "expected": run(
                "[.[] | select(.status_code >= 500) | .status_code] | unique | sort"
            ),
            "sort_before_compare": False,
        },
        {
            "title": "Flatten all endpoints",
            "question": (
                "Produce a flat array of every endpoint value that appears in "
                "the logs (duplicates included), preserving log order."
            ),
            "answer_expr": "jq '[.[].endpoint]' <LOGFILE>",
            "expected": run("[.[].endpoint]"),
            "sort_before_compare": False,
        },
        {
            "title": "Requests with retries",
            "question": (
                "Return an array of request_ids where metadata.retries > 0, "
                "in any order."
            ),
            "answer_expr": (
                "jq '[.[] | select(.metadata.retries > 0) | .request_id]' <LOGFILE>"
            ),
            "expected": run("[.[] | select(.metadata.retries > 0) | .request_id]"),
            "sort_before_compare": True,
        },
        {
            "title": "Transform to key pairs",
            "question": (
                "Produce an array of objects each containing only "
                "service, endpoint, and status_code from every log entry."
            ),
            "answer_expr": ("jq '[.[] | {service, endpoint, status_code}]' <LOGFILE>"),
            "expected": run("[.[] | {service, endpoint, status_code}]"),
            "sort_before_compare": True,
        },
        {
            "title": "Count cache hits",
            "question": (
                "Count how many log entries have metadata.cache_hit equal to true."
            ),
            "answer_expr": (
                "jq '[.[] | select(.metadata.cache_hit == true)] | length' <LOGFILE>"
            ),
            "expected": run("[.[] | select(.metadata.cache_hit == true)] | length"),
            "sort_before_compare": False,
        },
        {
            "title": "Max duration per service",
            "question": (
                "Produce an object mapping each service name to its maximum "
                "duration_ms value."
            ),
            "answer_expr": (
                "jq 'group_by(.service) | "
                "map({(.[0].service): ([.[].duration_ms] | max)}) | add' <LOGFILE>"
            ),
            "expected": run(
                "group_by(.service) | "
                "map({(.[0].service): ([.[].duration_ms] | max)}) | add"
            ),
            "sort_before_compare": False,
        },
        {
            "title": "Non-null users on errors",
            "question": (
                "List the unique user_ids (excluding null) who triggered at least "
                "one error-level entry, sorted alphabetically."
            ),
            "answer_expr": (
                'jq \'[.[] | select(.level=="error" and .user_id != null) '
                "| .user_id] | unique | sort' <LOGFILE>"
            ),
            "expected": run(
                '[.[] | select(.level=="error" and .user_id != null) '
                "| .user_id] | unique | sort"
            ),
            "sort_before_compare": False,
        },
    ]
    return problems


# ── Comparison ────────────────────────────────────────────────────────────────


def _normalise(val: object) -> object:
    """Recursively sort lists for order-insensitive comparison."""
    match val:
        case list():
            return sorted(
                (_normalise(v) for v in val),
                key=lambda x: json.dumps(x, sort_keys=True),
            )
        case dict():
            return {k: _normalise(v) for k, v in val.items()}
        case _:
            return val


def answers_match(expected: object, actual: object, sort_before_compare: bool) -> bool:
    if sort_before_compare:
        return _normalise(expected) == _normalise(actual)
    return expected == actual


# ── Running user commands ─────────────────────────────────────────────────────


def run_user_command(command: str, log_path: Path) -> tuple[bool, object | None, str]:
    """
    Execute the user's jq command. Returns (ok, parsed_output, error_msg).
    We substitute <LOGFILE> placeholder in case they copy from the hint.
    """
    cmd = command.replace("<LOGFILE>", str(log_path))
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, None, "Command timed out after 10 seconds."

    if result.returncode != 0:
        return False, None, result.stderr.strip()

    raw = result.stdout.strip()
    if not raw:
        return False, None, "Command produced no output."

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fall back to newline-delimited JSON (streaming jq output)
        lines = [l for l in raw.splitlines() if l]
        try:
            parsed = [json.loads(l) for l in lines]
        except json.JSONDecodeError as e:
            return False, None, f"Could not parse output as JSON: {e}"

    return True, parsed, ""


# ── Display helpers ───────────────────────────────────────────────────────────


def print_separator() -> None:
    print(dim("─" * 60))


def show_sample_entries(log_path: Path) -> None:
    all_lines = log_path.read_text().splitlines()
    sample = random.sample(all_lines, min(2, len(all_lines)))
    print(cyan("  Sample log entries:"))
    for line in sample:
        obj = json.loads(line)
        print(dim("  " + json.dumps(obj, indent=2).replace("\n", "\n  ")))


# ── Main session loop ─────────────────────────────────────────────────────────


def run_session(log_path: Path, problems: list[dict]) -> None:
    shuffled = problems.copy()
    random.shuffle(shuffled)
    total = len(shuffled)

    solved = 0
    skipped = 0
    wrong_attempts = 0

    for idx, problem in enumerate(shuffled, start=1):
        print()
        print_separator()
        print(bold(f"Problem {idx}/{total}: {problem['title']}"))
        print_separator()
        print(f"\n{problem['question']}\n")
        print(cyan(f"  Log file: {log_path}"))
        print()
        show_sample_entries(log_path)
        print()
        print(dim("  Type your jq command, or 'skip' to see the answer."))
        print()

        while True:
            try:
                user_input = input(bold("  > ")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                raise

            if not user_input:
                continue

            if user_input.lower() == "skip":
                skipped += 1
                ref = problem["answer_expr"].replace("<LOGFILE>", str(log_path))
                print(yellow(f"\n  Reference answer:\n  {ref}"))
                print(dim(f"  Expected output: {json.dumps(problem['expected'])}"))
                break

            ok, parsed, err = run_user_command(user_input, log_path)
            if not ok:
                wrong_attempts += 1
                print(red(f"\n  Error: {err}"))
                print(dim("  Try again, or type 'skip'.\n"))
                continue

            pretty_actual = json.dumps(parsed, indent=2)
            pretty_expected = json.dumps(problem["expected"], indent=2)

            if answers_match(
                problem["expected"], parsed, problem["sort_before_compare"]
            ):
                solved += 1
                print(green("\n  Correct!"))
                ref = problem["answer_expr"].replace("<LOGFILE>", str(log_path))
                print(dim(f"  Reference answer: {ref}"))
                print(cyan("\n  Your output:"))
                print(dim("  " + pretty_actual.replace("\n", "\n  ")))
                print(cyan("  Expected:"))
                print(dim("  " + pretty_expected.replace("\n", "\n  ")))
                break
            else:
                wrong_attempts += 1
                print(red("\n  Not quite - output doesn't match expected."))
                print(cyan("  Your output:"))
                print(dim("  " + pretty_actual.replace("\n", "\n  ")))
                print(cyan("  Expected:"))
                print(dim("  " + pretty_expected.replace("\n", "\n  ")))
                print(dim("\n  Try again, or type 'skip'.\n"))

    print()
    print_separator()
    print(bold("Session complete!"))
    print_separator()
    print(
        f"  {green(f'Solved: {solved}/{total}')}  |  "
        f"{yellow(f'Skipped: {skipped}')}  |  "
        f"{red(f'Wrong attempts: {wrong_attempts}')}"
    )
    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive jq teacher using realistic JSONL app logs.",
    )
    parser.add_argument(
        "--entries",
        type=int,
        default=200,
        metavar="N",
        help="Number of log entries to generate (default: 200).",
    )
    parser.parse_args()  # validates flags; extend here as needed

    # Check jq is available.
    try:
        subprocess.run(["jq", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(red("Error: 'jq' is not installed or not on PATH."), file=sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    logs = generate_logs(args.entries)

    # Write JSONL to a temp file; guarantee cleanup on any exit.
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, prefix="jq_teacher_"
    )
    log_path = Path(tmp.name)

    try:
        with log_path.open("w") as fh:
            for entry in logs:
                fh.write(json.dumps(entry) + "\n")

        print(bold("\n  jq Teacher"))
        print(dim("  Practise jq against real-looking HTTP API service logs.\n"))

        problems = _make_problems(logs)
        run_session(log_path, problems)

    except KeyboardInterrupt:
        print(dim("\n\n  Session interrupted. Goodbye!"))
    finally:
        log_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
