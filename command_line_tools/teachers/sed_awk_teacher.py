#!/usr/bin/env python3
"""Interactive sed + awk teacher - drill idiomatic sed, awk, and combined pipelines.

Each problem is best solved with sed, awk, or an efficient combination of the two.
You type a real shell command; it runs against a hand-crafted corpus and its output
is compared to a reference solution. Any tool is allowed (cat/echo/pipes too) - the
point is the correct output. The canonical idiomatic answer is always shown afterwards,
even when you get it right, so the pattern sticks.
"""

import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

# readline gives the input() prompt left/right arrow editing + history.
try:
    import readline  # noqa: F401
except ImportError:  # pragma: no cover - readline is stdlib on Linux/macOS
    pass

# ── ANSI colours ──────────────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def rl_prompt(text: str, code: str = "1") -> str:
    """Build a coloured input() prompt that readline measures correctly.

    ANSI escapes must be wrapped in \\001 (start-ignore) / \\002 (end-ignore) so
    readline treats them as zero-width; otherwise left/right arrow editing and
    line wrapping become janky because the cursor column is miscounted.
    """
    if not _TTY:
        return text
    return f"\001\033[{code}m\002{text}\001\033[0m\002"


def bold(t: str) -> str:    return _c("1", t)
def green(t: str) -> str:   return _c("32", t)
def red(t: str) -> str:     return _c("31", t)
def yellow(t: str) -> str:  return _c("33", t)
def cyan(t: str) -> str:    return _c("36", t)
def dim(t: str) -> str:     return _c("2", t)
def magenta(t: str) -> str: return _c("35", t)


# ── Fixed corpus ──────────────────────────────────────────────────────────────
# Hand-crafted so reference answers are deterministic. Each file targets specific
# sed/awk skills. The corpus is written to a temp dir and never mutated (in-place
# edits operate on a per-attempt scratch copy).

CORPUS: list[tuple[str, str]] = [

    ("data/employees.csv", dedent("""\
        id,name,department,salary,start_date,email,active
        1,Alice Johnson,Engineering,95000,2019-03-11,alice@example.com,true
        2,Bob Smith,Sales,62000,2020-07-01,bob@example.com,true
        3,Carol White,Engineering,88000,2018-11-23,carol@example.com,false
        4,Dave Brown,Marketing,54000,2021-01-15,dave@example.com,true
        5,Eve Davis,Sales,71000,2017-06-30,eve@example.com,true
        6,Frank Miller,Engineering,105000,2016-09-05,frank@example.com,true
        7,Grace Lee,Marketing,58000,2022-02-20,grace@example.com,false
        8,Henry Wilson,Support,47000,2020-10-12,henry@example.com,true
        9,Ivy Chen,Engineering,99000,2019-08-19,ivy@example.com,true
        10,Judy Martinez,Support,51000,2021-05-03,judy@example.com,false
    """)),

    ("data/transactions.csv", dedent("""\
        date,region,product,units,amount
        2024-01-03,us-east,widget,10,199.90
        2024-01-05,eu-west,gadget,4,159.96
        2024-01-07,us-east,gizmo,7,104.93
        2024-01-09,ap-south,widget,12,239.88
        2024-01-11,eu-west,widget,5,99.95
        2024-01-14,us-east,gadget,8,319.92
        2024-01-16,ap-south,gizmo,3,44.97
        2024-01-18,eu-west,gizmo,9,134.91
        2024-01-20,us-east,widget,6,119.94
        2024-01-23,ap-south,gadget,2,79.98
    """)),

    ("system/passwd.txt", dedent("""\
        root:x:0:0:root:/root:/bin/bash
        daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
        alice:x:1000:1000:Alice Johnson:/home/alice:/bin/bash
        bob:x:1001:1001:Bob Smith:/home/bob:/bin/zsh
        carol:x:1002:1002:Carol White:/home/carol:/bin/bash
        dave:x:1003:1003:Dave Brown:/home/dave:/usr/sbin/nologin
        eve:x:1004:1004:Eve Davis:/home/eve:/bin/bash
        svc_backup:x:1005:1005:Backup Service:/var/lib/backup:/usr/sbin/nologin
    """)),

    ("logs/access.log", dedent("""\
        192.168.1.10 - alice [15/Jan/2024:08:01:12] "GET /api/users HTTP/1.1" 200 1542
        192.168.1.11 - bob [15/Jan/2024:08:01:13] "POST /api/orders HTTP/1.1" 201 892
        10.0.0.5 - - [15/Jan/2024:08:01:50] "GET /health HTTP/1.1" 200 18
        192.168.1.12 - carol [15/Jan/2024:08:04:11] "GET /api/users HTTP/1.1" 200 1542
        192.168.1.11 - bob [15/Jan/2024:08:06:00] "GET /api/v1/ping HTTP/1.1" 404 4
        192.168.1.20 - admin [15/Jan/2024:08:08:00] "POST /api/users HTTP/1.1" 500 910
        192.168.1.99 - - [15/Jan/2024:08:09:45] "GET /admin HTTP/1.1" 403 112
        192.168.1.10 - alice [15/Jan/2024:08:10:00] "GET /api/orders HTTP/1.1" 200 3201
        10.0.0.5 - - [15/Jan/2024:08:11:00] "GET /health HTTP/1.1" 200 18
        192.168.1.12 - carol [15/Jan/2024:08:12:30] "DELETE /api/sessions/42 HTTP/1.1" 204 0
    """)),

    ("config/app.conf", dedent("""\
        # Application configuration
        # Edit with care

        [server]
        host = 0.0.0.0
        port = 8080   
        workers = 4

        [database]
        host = db.internal
        port = 5432
        # password stored in vault
        pool_size = 10

        [cache]
        host = cache.internal
        port = 6379
        enabled = true

        [features]
        dark_mode = true
        beta_api = false
    """)),

    ("text/release_notes.md", dedent("""\
        # Release Notes

        ## Version 2.4.0

        - Added dark mode support
        - Fixed login timeout bug
        - Improved query performance via REST API caching
        - Updated dependencies

        ## Version 2.3.1

        - Patched security vulnerability CVE-2024-1234
        - Fixed crash on startup
        - TODO: document new config options

        ## Version 2.3.0

        - Initial public release
        - Basic authentication
        - REST API endpoints
    """)),
]


# ── Corpus helpers ────────────────────────────────────────────────────────────


def write_corpus(base: Path) -> None:
    for rel_path, content in CORPUS:
        dest = base / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)


# ── Command execution ─────────────────────────────────────────────────────────


def execute_command(
    cmd_template: str,
    base: Path,
    scratch_rel: str | None = None,
) -> tuple[int, str, str] | None:
    """Run a command with placeholders resolved.

    <CORPUS>  -> corpus base dir.
    <SCRATCH> -> a fresh per-run copy of ``scratch_rel`` (for in-place edits).

    For scratch problems the "output" is the file contents *after* the command
    runs (in-place edits write nothing to stdout). Otherwise output is stdout.

    Returns (returncode, output, stderr) or None on timeout.
    """
    cmd = cmd_template.replace("<CORPUS>", str(base))
    scratch_path: str | None = None
    if scratch_rel is not None:
        fd, scratch_path = tempfile.mkstemp(prefix="sed_awk_scratch_")
        os.close(fd)
        shutil.copy(base / scratch_rel, scratch_path)
        cmd = cmd.replace("<SCRATCH>", scratch_path)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        if scratch_path:
            os.unlink(scratch_path)
        return None

    if scratch_path is not None:
        output = Path(scratch_path).read_text()
        os.unlink(scratch_path)
    else:
        output = result.stdout

    return result.returncode, output, result.stderr.strip()


# ── Problem definitions ───────────────────────────────────────────────────────
#
# Each problem dict:
#   tool     - "sed" | "awk" | "sed+awk"  (informational tag only; not enforced)
#   title    - short name
#   question - what to do
#   files    - relative corpus paths to preview with the question
#   answer   - canonical reference command (uses <CORPUS> / <SCRATCH> placeholders)
#   note     - one-line idiom explanation shown with the answer
#   compare  - "exact" | "set" | "count" | "nonempty"
#   scratch  - optional relative path; if set, the command edits a copy in place
#              and the resulting file contents (not stdout) are compared.


def _raw_problems() -> list[dict]:
    return [
        # ── sed ───────────────────────────────────────────────────────────────
        dict(
            tool="sed",
            title="Basic substitution (first match per line)",
            question="In text/release_notes.md, change 'REST API' to 'HTTP API'.",
            files=["text/release_notes.md"],
            answer="sed 's/REST API/HTTP API/' <CORPUS>/text/release_notes.md",
            note="s/old/new/ replaces the FIRST match on each line.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Global substitution",
            question="In data/employees.csv, replace every comma with a pipe '|'.",
            files=["data/employees.csv"],
            answer="sed 's/,/|/g' <CORPUS>/data/employees.csv",
            note="the g flag replaces ALL matches on a line, not just the first.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Case-insensitive substitution",
            question="In text/release_notes.md, replace 'todo' (any capitalisation) with 'PENDING'.",
            files=["text/release_notes.md"],
            answer="sed 's/todo/PENDING/gI' <CORPUS>/text/release_notes.md",
            note="the I flag makes the match case-insensitive (GNU sed).",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Capture groups and backreferences",
            question=(
                "In data/employees.csv, rewrite ISO dates (YYYY-MM-DD) in the "
                "day/month/year form DD/MM/YYYY."
            ),
            files=["data/employees.csv"],
            answer=(
                "sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\\3\\/\\2\\/\\1/' "
                "<CORPUS>/data/employees.csv"
            ),
            note="\\1 \\2 \\3 refer to captured () groups; -E enables extended regex.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Whole-match reference (&)",
            question="In text/release_notes.md, wrap every CVE id (e.g. CVE-2024-1234) in [square brackets].",
            files=["text/release_notes.md"],
            answer="sed -E 's/CVE-[0-9]{4}-[0-9]+/[&]/' <CORPUS>/text/release_notes.md",
            note="& in the replacement inserts the entire matched text.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Alternate s/// delimiter for paths",
            question="In system/passwd.txt, change the home path prefix '/home' to '/users'.",
            files=["system/passwd.txt"],
            answer="sed 's#/home#/users#g' <CORPUS>/system/passwd.txt",
            note="any char can delimit s (s#..#..#) - avoids escaping / in paths.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Delete lines matching a pattern",
            question="In text/release_notes.md, remove every line containing 'TODO'.",
            files=["text/release_notes.md"],
            answer="sed '/TODO/d' <CORPUS>/text/release_notes.md",
            note="/pattern/d deletes every line matching the pattern.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Delete blank lines",
            question="Strip all blank lines out of config/app.conf.",
            files=["config/app.conf"],
            answer="sed '/^$/d' <CORPUS>/config/app.conf",
            note="/^$/ matches an empty line (start immediately followed by end).",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Print only matching lines (-n + p)",
            question="Print only the passwd lines whose login shell is /bin/bash.",
            files=["system/passwd.txt"],
            answer="sed -n '/\\/bin\\/bash$/p' <CORPUS>/system/passwd.txt",
            note="-n silences auto-print; p then prints only the lines you select.",
            compare="set",
        ),
        dict(
            tool="sed",
            title="Print a line-number range",
            question="Print lines 2 through 6 (inclusive) of data/transactions.csv.",
            files=["data/transactions.csv"],
            answer="sed -n '2,6p' <CORPUS>/data/transactions.csv",
            note="N,Mp prints an inclusive line-number range (needs -n).",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Print a pattern range",
            question=(
                "In text/release_notes.md, print the block from the "
                "'## Version 2.3.1' heading down to the next blank line."
            ),
            files=["text/release_notes.md"],
            answer="sed -n '/## Version 2.3.1/,/^$/p' <CORPUS>/text/release_notes.md",
            note="/a/,/b/ selects lines from the first match through the next match of b.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Delete the header line",
            question="Print data/employees.csv WITHOUT its header row.",
            files=["data/employees.csv"],
            answer="sed '1d' <CORPUS>/data/employees.csv",
            note="Nd deletes line N; '1d' is the classic 'drop the header' trick.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Substitute only within a range",
            question=(
                "In config/app.conf, only inside the [database] section (from the "
                "[database] line to the next blank line) rename 'host' to 'hostname'."
            ),
            files=["config/app.conf"],
            answer=(
                "sed '/\\[database\\]/,/^$/s/host/hostname/' <CORPUS>/config/app.conf"
            ),
            note="prefix s with an address/range to limit which lines it edits.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Trim trailing whitespace",
            question="Remove trailing whitespace from every line of config/app.conf.",
            files=["config/app.conf"],
            answer="sed -E 's/[[:space:]]+$//' <CORPUS>/config/app.conf",
            note="$ anchors to line end; [[:space:]] is a POSIX character class.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Append a line after a match",
            question=(
                "In config/app.conf, append a new line 'timeout = 30' immediately "
                "after the [server] section header."
            ),
            files=["config/app.conf"],
            answer="sed '/\\[server\\]/a timeout = 30' <CORPUS>/config/app.conf",
            note="a\\ appends text after matching lines; i\\ inserts before them.",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="Chain edits with multiple -e",
            question=(
                "In one sed invocation on data/employees.csv: delete the header row "
                "AND replace all commas with tabs."
            ),
            files=["data/employees.csv"],
            answer="sed -e '1d' -e 's/,/\\t/g' <CORPUS>/data/employees.csv",
            note="chain edits with multiple -e scripts (or separate them with ;).",
            compare="exact",
        ),
        dict(
            tool="sed",
            title="In-place edit (-i)",
            question=(
                "Edit the file IN PLACE so every 'false' becomes 'true'. "
                "Operate on <SCRATCH> (a disposable copy of employees.csv); your "
                "in-place edit is read back to check the result."
            ),
            files=["data/employees.csv"],
            answer="sed -i 's/false/true/g' <SCRATCH>",
            note="-i writes changes back to the file instead of stdout.",
            compare="exact",
            scratch="data/employees.csv",
        ),

        # ── awk ───────────────────────────────────────────────────────────────
        dict(
            tool="awk",
            title="Print one field",
            question="Print just the username (first colon-field) from system/passwd.txt.",
            files=["system/passwd.txt"],
            answer="awk -F: '{print $1}' <CORPUS>/system/passwd.txt",
            note="-F sets the field separator; $1 is the first field.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Reorder columns",
            question="From data/employees.csv, print 'department name' (department then name) for every row.",
            files=["data/employees.csv"],
            answer="awk -F, '{print $3, $2}' <CORPUS>/data/employees.csv",
            note="print a, b joins fields with OFS (a single space by default).",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Skip the header with NR",
            question="Print every employee name EXCEPT the header row.",
            files=["data/employees.csv"],
            answer="awk -F, 'NR>1{print $2}' <CORPUS>/data/employees.csv",
            note="NR is the current line number; NR>1 skips the header.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Number every line",
            question="Print text/release_notes.md with each line prefixed by its line number (like 'NR line').",
            files=["text/release_notes.md"],
            answer="awk '{print NR, $0}' <CORPUS>/text/release_notes.md",
            note="NR holds the running line count; $0 is the whole line.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Last field with $NF",
            question="Print each user's login shell (the LAST colon-field) from passwd without hardcoding the index.",
            files=["system/passwd.txt"],
            answer="awk -F: '{print $NF}' <CORPUS>/system/passwd.txt",
            note="$NF is the last field; NF is the number of fields on the line.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Numeric field filter",
            question="Print the names of employees earning more than 90000.",
            files=["data/employees.csv"],
            answer="awk -F, '$4 > 90000 {print $2}' <CORPUS>/data/employees.csv",
            note="a bare pattern{action} runs only on matching lines; $4 compares numerically.",
            compare="set",
        ),
        dict(
            tool="awk",
            title="String-equality filter",
            question="Print the names of everyone in the Engineering department.",
            files=["data/employees.csv"],
            answer="awk -F, '$3 == \"Engineering\" {print $2}' <CORPUS>/data/employees.csv",
            note="== with a quoted string does an exact string match on the field.",
            compare="set",
        ),
        dict(
            tool="awk",
            title="Compound conditions",
            question="Print the names of Engineering employees earning over 95000.",
            files=["data/employees.csv"],
            answer=(
                "awk -F, '$3 == \"Engineering\" && $4 > 95000 {print $2}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="&& and || combine conditions in the pattern.",
            compare="set",
        ),
        dict(
            tool="awk",
            title="Regex match on a field",
            question="Print the usernames of accounts whose shell is a nologin shell (matches 'nologin').",
            files=["system/passwd.txt"],
            answer="awk -F: '$NF ~ /nologin/ {print $1}' <CORPUS>/system/passwd.txt",
            note="~ tests a field against a regex; !~ negates it.",
            compare="set",
        ),
        dict(
            tool="awk",
            title="Sum a column",
            question="Print the total 'amount' across all transactions.",
            files=["data/transactions.csv"],
            answer="awk -F, 'NR>1{sum+=$5} END{print sum}' <CORPUS>/data/transactions.csv",
            note="accumulate into a variable, then emit it in the END block.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Average of a column",
            question="Print the average salary across all employees, to 2 decimal places.",
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1{s+=$4; n++} END{printf \"%.2f\\n\", s/n}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="count rows with n++ and divide in END; printf formats the number.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Maximum of a column",
            question="Print the single highest salary in the company.",
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1 && $4>max{max=$4} END{print max}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="track a running max across lines and emit it in END.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Group-by sum (associative array)",
            question="Print the total sales 'amount' per region.",
            files=["data/transactions.csv"],
            answer=(
                "awk -F, 'NR>1{sum[$2]+=$5} END{for(r in sum) print r, sum[r]}' "
                "<CORPUS>/data/transactions.csv"
            ),
            note="arrays keyed by a field give you SQL-style group-by aggregation.",
            compare="set",
        ),
        dict(
            tool="awk",
            title="Count per key",
            question="Print how many employees are in each department.",
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1{c[$3]++} END{for(d in c) print d, c[d]}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="c[key]++ tallies occurrences per key.",
            compare="set",
        ),
        dict(
            tool="awk",
            title="Dedup, preserving first-seen order",
            question="Print the distinct departments in the order they first appear.",
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1 && !seen[$3]++ {print $3}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="!seen[x]++ is true only the first time x appears - classic dedup.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Formatted table with printf",
            question=(
                "Print a two-column table of each employee's name and salary: "
                "name left-justified in 16 columns, salary right-justified in 8."
            ),
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1{printf \"%-16s %8d\\n\", $2, $4}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="printf width/justify specifiers (%-16s, %8d) build aligned columns.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Set FS and OFS in BEGIN",
            question="Convert data/employees.csv to TAB-separated output (comma in, tab out).",
            files=["data/employees.csv"],
            answer=(
                "awk 'BEGIN{FS=\",\"; OFS=\"\\t\"} {$1=$1; print}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="assigning $1=$1 forces awk to rebuild $0 using the new OFS.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="In-field substitution with gsub",
            question="Print each employee email with the domain 'example.com' rewritten to 'corp.io'.",
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1{gsub(/example\\.com/, \"corp.io\", $6); print $6}' "
                "<CORPUS>/data/employees.csv"
            ),
            note="gsub(re, repl, target) substitutes in place within a field or variable.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="String functions (toupper)",
            question="Print every passwd username in UPPERCASE.",
            files=["system/passwd.txt"],
            answer="awk -F: '{print toupper($1)}' <CORPUS>/system/passwd.txt",
            note="toupper/tolower/length/substr are built-in string functions.",
            compare="exact",
        ),
        dict(
            tool="awk",
            title="Count lines matching a condition",
            question="Count how many access-log requests returned HTTP status 200.",
            files=["logs/access.log"],
            answer="awk '$8 == 200 {c++} END{print c}' <CORPUS>/logs/access.log",
            note="status is field 8 here; increment a counter and print it in END.",
            compare="exact",
        ),

        # ── sed + awk combined ────────────────────────────────────────────────
        dict(
            tool="sed+awk",
            title="sed cleans, awk counts",
            question=(
                "Strip comment lines (starting with #) and blank lines from "
                "config/app.conf, then count the remaining 'key = value' lines."
            ),
            files=["config/app.conf"],
            answer=(
                "sed -e '/^#/d' -e '/^$/d' <CORPUS>/config/app.conf "
                "| awk '/=/{c++} END{print c}'"
            ),
            note="let sed clean the stream, then let awk count - each tool at its best.",
            compare="exact",
        ),
        dict(
            tool="sed+awk",
            title="sed normalises the delimiter for awk",
            question=(
                "Print each user's name and UID from passwd by first turning colons "
                "into spaces with sed, then selecting fields with awk (username + UID)."
            ),
            files=["system/passwd.txt"],
            answer=(
                "sed 's/:/ /g' <CORPUS>/system/passwd.txt | awk '{print $1, $3}'"
            ),
            note="sed normalises the delimiter so awk's default whitespace split just works.",
            compare="exact",
        ),
        dict(
            tool="sed+awk",
            title="awk extracts, sed reshapes",
            question=(
                "Print just the local-part of every employee email (drop the header "
                "and strip '@domain'): pull the email column with awk, reshape with sed."
            ),
            files=["data/employees.csv"],
            answer=(
                "awk -F, 'NR>1{print $6}' <CORPUS>/data/employees.csv "
                "| sed -E 's/@.*//'"
            ),
            note="awk selects the field, sed rewrites it - a common extract-then-reshape pipe.",
            compare="exact",
        ),
        dict(
            tool="sed+awk",
            title="sed strips noise, awk tallies",
            question=(
                "Tally the number of access-log requests per HTTP method. The method "
                "sits in a quoted field (e.g. \"GET); strip the quotes with sed first, "
                "then group-count by method with awk."
            ),
            files=["logs/access.log"],
            answer=(
                "sed 's/\"//g' <CORPUS>/logs/access.log "
                "| awk '{c[$5]++} END{for(m in c) print m, c[m]}'"
            ),
            note="sed removes noise characters so awk can cleanly key on the method field.",
            compare="set",
        ),
    ]


def make_problems(base: Path) -> list[dict]:
    """Resolve each problem's expected output by running its reference command."""
    problems = _raw_problems()
    for prob in problems:
        result = execute_command(prob["answer"], base, prob.get("scratch"))
        if result is None:
            raise RuntimeError(f"Reference command timed out: {prob['title']}")
        rc, output, stderr = result
        if rc != 0:
            raise RuntimeError(
                f"Reference command failed (exit {rc}) for '{prob['title']}':\n"
                f"  cmd: {prob['answer']}\n  err: {stderr}"
            )
        prob["expected"] = output
    return problems


# ── Comparison ────────────────────────────────────────────────────────────────


def normalise_paths(text: str, base: Path) -> str:
    return text.replace(str(base), "<CORPUS>")


def compare_outputs(expected: str, actual: str, mode: str) -> bool:
    if mode == "set":
        return sorted(expected.strip().splitlines()) == sorted(actual.strip().splitlines())
    if mode == "nonempty":
        return bool(actual.strip())
    # "exact" and "count" both fall through to a stripped exact compare.
    return expected.strip() == actual.strip()


# ── Display helpers ───────────────────────────────────────────────────────────

_TOOL_COLOUR = {"sed": cyan, "awk": magenta, "sed+awk": yellow}


def tool_badge(tool: str) -> str:
    colour = _TOOL_COLOUR.get(tool, bold)
    return colour(f"[{tool}]")


def print_separator(char: str = "─", width: int = 68) -> None:
    print(dim(char * width))


def show_file_previews(problem: dict, base: Path, max_lines: int = 12) -> None:
    for rel in problem.get("files", []):
        path = base / rel
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        print(cyan(f"  {rel}:"))
        for line in lines[:max_lines]:
            print(dim(f"    {line}"))
        if len(lines) > max_lines:
            print(dim(f"    … ({len(lines) - max_lines} more lines)"))
        print()


def show_answer(problem: dict, base: Path) -> None:
    resolved = problem["answer"].replace("<CORPUS>", str(base))
    if problem.get("scratch"):
        resolved = resolved.replace("<SCRATCH>", str(base / problem["scratch"]))
    print(yellow("\n  Suggested answer:"))
    print(f"    {bold(resolved)}")
    print(dim(f"    {problem['note']}"))


def show_output_block(label: str, text: str, base: Path, max_lines: int = 8) -> None:
    print(cyan(f"  {label}"))
    lines = normalise_paths(text.strip(), base).splitlines()
    for line in lines[:max_lines]:
        print(dim(f"    {line}"))
    if len(lines) > max_lines:
        print(dim(f"    … ({len(lines) - max_lines} more lines)"))


# ── Main session loop ─────────────────────────────────────────────────────────


def run_session(base: Path, problems: list[dict]) -> None:
    shuffled = problems.copy()
    random.shuffle(shuffled)
    total = len(shuffled)

    solved = skipped = wrong_attempts = 0

    for idx, problem in enumerate(shuffled, start=1):
        print()
        print_separator()
        print(f"{bold(f'Problem {idx}/{total}')}  {tool_badge(problem['tool'])}  {bold(problem['title'])}")
        print_separator()
        print(f"\n{problem['question']}\n")
        show_file_previews(problem, base)
        print(dim("  Corpus root: " + str(base)))
        print(dim("  Use <CORPUS> as a shortcut for the corpus root. Any tool is allowed."))
        if problem.get("scratch"):
            print(dim("  Edit <SCRATCH> in place - it's a fresh copy; the result is read back."))
        print(dim("  Type 'skip' to reveal the answer and move on."))
        print()

        expected = problem["expected"]

        while True:
            try:
                user_input = input(rl_prompt("  > ")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                raise

            if not user_input:
                continue

            if user_input.lower() == "skip":
                skipped += 1
                show_answer(problem, base)
                show_output_block("Expected output:", expected, base)
                break

            result = execute_command(user_input, base, problem.get("scratch"))
            if result is None:
                wrong_attempts += 1
                print(red("\n  Command timed out after 10 seconds."))
                print(dim("  Try again, or type 'skip'.\n"))
                continue

            rc, output, stderr = result
            if rc != 0 and not output.strip():
                wrong_attempts += 1
                print(red(f"\n  Error: {stderr or 'command returned non-zero with no output.'}"))
                print(dim("  Try again, or type 'skip'.\n"))
                continue

            if compare_outputs(expected, output, problem["compare"]):
                solved += 1
                print(green("\n  Correct!"))
                show_answer(problem, base)
                break
            else:
                wrong_attempts += 1
                print(red("\n  Not quite."))
                show_output_block("Your output:", output, base)
                show_output_block("Expected:", expected, base)
                print(dim("\n  Try again, or type 'skip'.\n"))

    print()
    print_separator("═")
    print(bold("  Session complete!"))
    print_separator("═")
    print(
        f"  {green(f'Solved: {solved}/{total}')}   "
        f"{yellow(f'Skipped: {skipped}')}   "
        f"{red(f'Wrong attempts: {wrong_attempts}')}"
    )
    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    # Check required tools are present.
    missing = []
    for tool in ("sed", "awk"):
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing.append(tool)
    if missing:
        print(red(f"Error: not installed or not on PATH: {', '.join(missing)}"), file=sys.stderr)
        sys.exit(1)

    tmp_dir = tempfile.mkdtemp(prefix="sed_awk_teacher_")
    base = Path(tmp_dir)

    try:
        write_corpus(base)

        print(bold("\n  sed / awk Teacher"))
        print(dim("  Drill idiomatic sed, awk, and combined pipelines against a fixed corpus.\n"))
        print(dim(f"  Corpus written to: {base}\n"))

        problems = make_problems(base)
        run_session(base, problems)

    except KeyboardInterrupt:
        print(dim("\n\n  Session interrupted. Goodbye!"))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
