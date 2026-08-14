#!/usr/bin/env python3
"""Interactive grep/ripgrep teacher - practise searching a realistic multi-file corpus."""

import argparse
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

# ── ANSI colours ──────────────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def bold(t: str) -> str:   return _c("1", t)
def green(t: str) -> str:  return _c("32", t)
def red(t: str) -> str:    return _c("31", t)
def yellow(t: str) -> str: return _c("33", t)
def cyan(t: str) -> str:   return _c("36", t)
def dim(t: str) -> str:    return _c("2", t)
def magenta(t: str) -> str: return _c("35", t)


# ── Fixed corpus ──────────────────────────────────────────────────────────────
# Each entry: (relative_path, content)
# Hand-crafted so problem answers are deterministic.

CORPUS: list[tuple[str, str]] = [

    ("logs/app.log", dedent("""\
        2024-01-15 08:00:01 INFO  Starting application server on port 8080
        2024-01-15 08:00:02 INFO  Database connection established
        2024-01-15 08:00:05 WARN  Config value 'max_retries' not set, using default 3
        2024-01-15 08:01:12 INFO  Request GET /api/users 200 45ms user=alice
        2024-01-15 08:01:13 INFO  Request POST /api/orders 201 120ms user=bob
        2024-01-15 08:02:44 ERROR Failed to connect to cache: connection refused
        2024-01-15 08:02:45 INFO  Falling back to database for cache miss
        2024-01-15 08:03:01 WARN  Response time 850ms exceeds threshold for GET /api/reports
        2024-01-15 08:03:55 ERROR Unhandled exception in worker thread: NullPointerException
        2024-01-15 08:04:10 INFO  Request DELETE /api/sessions/42 204 12ms user=alice
        2024-01-15 08:04:11 INFO  Request GET /api/users 200 38ms user=carol
        2024-01-15 08:05:00 ERROR Disk usage at 91%: /var/data
        2024-01-15 08:05:30 INFO  Scheduled job 'cleanup' completed in 2340ms
        2024-01-15 08:06:00 WARN  Deprecated API endpoint /api/v1/ping called by user=bob
        2024-01-15 08:06:45 INFO  Request GET /api/orders 200 67ms user=carol
        2024-01-15 08:07:00 ERROR Payment gateway timeout after 30000ms
        2024-01-15 08:07:01 INFO  Retrying payment request (attempt 2/3)
        2024-01-15 08:07:03 INFO  Payment request succeeded on retry
        2024-01-15 08:08:00 INFO  Request POST /api/users 201 88ms user=admin
        2024-01-15 08:09:15 WARN  JWT token expiring soon for user=alice
        2024-01-15 08:10:00 INFO  Graceful shutdown initiated
        2024-01-15 08:10:02 INFO  Database connection closed
        2024-01-15 08:10:03 INFO  Application server stopped
    """)),

    ("logs/access.log", dedent("""\
        192.168.1.10 - alice [15/Jan/2024:08:01:12] "GET /api/users HTTP/1.1" 200 1542
        192.168.1.11 - bob [15/Jan/2024:08:01:13] "POST /api/orders HTTP/1.1" 201 892
        10.0.0.5 - - [15/Jan/2024:08:01:50] "GET /health HTTP/1.1" 200 18
        192.168.1.10 - alice [15/Jan/2024:08:04:10] "DELETE /api/sessions/42 HTTP/1.1" 204 0
        192.168.1.12 - carol [15/Jan/2024:08:04:11] "GET /api/users HTTP/1.1" 200 1542
        10.0.0.5 - - [15/Jan/2024:08:04:30] "GET /health HTTP/1.1" 200 18
        192.168.1.11 - bob [15/Jan/2024:08:06:00] "GET /api/v1/ping HTTP/1.1" 200 4
        192.168.1.12 - carol [15/Jan/2024:08:06:45] "GET /api/orders HTTP/1.1" 200 3201
        192.168.1.20 - admin [15/Jan/2024:08:08:00] "POST /api/users HTTP/1.1" 201 910
        10.0.0.5 - - [15/Jan/2024:08:09:00] "GET /health HTTP/1.1" 200 18
        192.168.1.99 - - [15/Jan/2024:08:09:45] "GET /etc/passwd HTTP/1.1" 403 112
        192.168.1.99 - - [15/Jan/2024:08:09:46] "GET /../../../etc/shadow HTTP/1.1" 400 98
        192.168.1.10 - alice [15/Jan/2024:08:10:00] "GET /api/orders HTTP/1.1" 200 3201
    """)),

    ("logs/worker.log", dedent("""\
        2024-01-15 08:00:10 INFO  Worker pool started: 4 workers
        2024-01-15 08:00:11 INFO  Worker-1 ready
        2024-01-15 08:00:11 INFO  Worker-2 ready
        2024-01-15 08:00:11 INFO  Worker-3 ready
        2024-01-15 08:00:11 INFO  Worker-4 ready
        2024-01-15 08:01:00 INFO  Worker-1 processing job_id=9a3f email_dispatch
        2024-01-15 08:01:05 INFO  Worker-2 processing job_id=9a40 report_generate
        2024-01-15 08:01:10 INFO  Worker-1 completed job_id=9a3f in 9800ms
        2024-01-15 08:02:00 INFO  Worker-3 processing job_id=9a41 data_export
        2024-01-15 08:02:30 ERROR Worker-3 failed job_id=9a41: export destination unreachable
        2024-01-15 08:02:31 WARN  Job job_id=9a41 will be retried (attempt 1/3)
        2024-01-15 08:03:00 INFO  Worker-4 processing job_id=9a42 invoice_generate
        2024-01-15 08:03:45 INFO  Worker-2 completed job_id=9a40 in 160500ms
        2024-01-15 08:04:00 INFO  Worker-3 processing job_id=9a41 data_export (retry)
        2024-01-15 08:04:30 INFO  Worker-3 completed job_id=9a41 in 30000ms
        2024-01-15 08:05:00 INFO  Worker-4 completed job_id=9a42 in 120000ms
        2024-01-15 08:05:30 INFO  Worker-1 processing job_id=9a43 cleanup
        2024-01-15 08:05:30 INFO  Scheduled job 'cleanup' completed in 2340ms
        2024-01-15 08:06:00 WARN  Worker pool queue depth: 12 (high)
        2024-01-15 08:09:00 INFO  Worker pool draining
        2024-01-15 08:09:55 INFO  Worker pool stopped
    """)),

    ("config/app.conf", dedent("""\
        # Application configuration
        [server]
        host = 0.0.0.0
        port = 8080
        workers = 4
        debug = false

        [database]
        host = db.internal
        port = 5432
        name = appdb
        user = appuser
        # password stored in vault
        pool_size = 10
        max_overflow = 5
        connect_timeout = 30

        [cache]
        host = cache.internal
        port = 6379
        ttl = 3600
        enabled = true

        [logging]
        level = INFO
        format = json
        output = /var/log/app/app.log

        [features]
        new_dashboard = false
        beta_api = false
        dark_mode = true
    """)),

    ("config/database.yaml", dedent("""\
        database:
          primary:
            host: db-primary.internal
            port: 5432
            name: appdb
            user: appuser
            password: "{{ vault:db/primary/password }}"
            ssl: true
            pool:
              min: 2
              max: 10
              timeout: 30

          replica:
            host: db-replica.internal
            port: 5432
            name: appdb
            user: appuser_ro
            password: "{{ vault:db/replica/password }}"
            ssl: true
            pool:
              min: 1
              max: 5
              timeout: 30

        migrations:
          directory: ./migrations
          table: schema_migrations
          auto_run: false
    """)),

    ("config/workers.toml", dedent("""\
        [worker_pool]
        size = 4
        max_queue_depth = 100
        drain_timeout_seconds = 30

        [jobs.email_dispatch]
        queue = "email"
        max_retries = 3
        timeout_seconds = 60
        priority = high

        [jobs.report_generate]
        queue = "reports"
        max_retries = 2
        timeout_seconds = 300
        priority = normal

        [jobs.data_export]
        queue = "exports"
        max_retries = 3
        timeout_seconds = 120
        priority = normal

        [jobs.invoice_generate]
        queue = "billing"
        max_retries = 5
        timeout_seconds = 90
        priority = high

        [jobs.cleanup]
        queue = "maintenance"
        max_retries = 1
        timeout_seconds = 60
        priority = low
    """)),

    ("data/users.csv", dedent("""\
        id,username,email,role,active,created_at
        1,alice,alice@example.com,admin,true,2023-01-10
        2,bob,bob@example.com,user,true,2023-02-14
        3,carol,carol@example.com,user,true,2023-03-22
        4,dave,dave@example.com,user,false,2023-04-01
        5,eve,eve@example.com,moderator,true,2023-05-18
        6,frank,frank@example.com,user,false,2023-06-30
        7,grace,grace@example.com,admin,true,2023-07-11
        8,henry,henry@example.com,user,true,2023-08-25
        9,ivan,ivan@example.com,user,true,2023-09-03
        10,judy,judy@example.com,moderator,false,2023-10-17
    """)),

    ("data/products.csv", dedent("""\
        id,name,category,price,stock,sku
        101,Wireless Headphones,electronics,79.99,150,SKU-WH-001
        102,USB-C Hub,electronics,34.99,300,SKU-UC-002
        103,Mechanical Keyboard,electronics,129.99,75,SKU-MK-003
        104,Desk Lamp,furniture,45.00,200,SKU-DL-004
        105,Standing Desk,furniture,499.99,20,SKU-SD-005
        106,Notebook A5,stationery,4.99,1000,SKU-NA-006
        107,Ballpoint Pens (10pk),stationery,3.49,800,SKU-BP-007
        108,Monitor Stand,furniture,89.99,60,SKU-MS-008
        109,Webcam HD,electronics,59.99,120,SKU-WC-009
        110,Mouse Pad XL,accessories,19.99,400,SKU-MP-010
    """)),

    ("data/errors.json", dedent("""\
        {"id": "e001", "code": "DB_CONN_REFUSED", "message": "connection refused", "service": "api", "ts": "2024-01-15T08:02:44Z"}
        {"id": "e002", "code": "NULL_POINTER", "message": "NullPointerException in worker thread", "service": "worker", "ts": "2024-01-15T08:03:55Z"}
        {"id": "e003", "code": "DISK_FULL", "message": "Disk usage at 91%: /var/data", "service": "monitor", "ts": "2024-01-15T08:05:00Z"}
        {"id": "e004", "code": "GW_TIMEOUT", "message": "Payment gateway timeout after 30000ms", "service": "payments", "ts": "2024-01-15T08:07:00Z"}
        {"id": "e005", "code": "EXPORT_UNREACHABLE", "message": "export destination unreachable", "service": "worker", "ts": "2024-01-15T08:02:30Z"}
    """)),

    ("src/api/handlers.py", dedent("""\
        \"\"\"HTTP request handlers for the API.\"\"\"
        import logging
        from typing import Optional
        from .models import User, Order
        from .auth import require_auth
        from .db import get_session

        logger = logging.getLogger(__name__)


        def get_users(request) -> list[User]:
            \"\"\"Return all active users.\"\"\"
            with get_session() as session:
                users = session.query(User).filter(User.active == True).all()
                logger.info("get_users called, returned %d users", len(users))
                return users


        @require_auth
        def create_user(request) -> User:
            \"\"\"Create a new user account.\"\"\"
            data = request.json()
            # TODO: validate email uniqueness
            user = User(
                username=data["username"],
                email=data["email"],
                role=data.get("role", "user"),
            )
            with get_session() as session:
                session.add(user)
                session.commit()
                logger.info("User created: %s", user.username)
                return user


        @require_auth
        def delete_session(request, session_id: int) -> None:
            \"\"\"Invalidate an existing session.\"\"\"
            with get_session() as db:
                db.query(Session).filter(Session.id == session_id).delete()
                logger.info("Session %d deleted", session_id)


        def get_orders(request, user_id: Optional[int] = None) -> list[Order]:
            \"\"\"Return orders, optionally filtered by user.\"\"\"
            with get_session() as session:
                query = session.query(Order)
                if user_id is not None:
                    query = query.filter(Order.user_id == user_id)
                orders = query.all()
                logger.info("get_orders returned %d orders", len(orders))
                return orders


        @require_auth
        def create_order(request) -> Order:
            \"\"\"Place a new order.\"\"\"
            data = request.json()
            # TODO: check stock availability before committing
            order = Order(
                user_id=data["user_id"],
                items=data["items"],
                total=data["total"],
            )
            with get_session() as session:
                session.add(order)
                session.commit()
                logger.info("Order created for user %s", data["user_id"])
                return order
        """)),

    ("src/api/auth.py", dedent("""\
        \"\"\"Authentication and authorisation helpers.\"\"\"
        import hashlib
        import hmac
        import logging
        import time
        from functools import wraps
        from typing import Callable

        logger = logging.getLogger(__name__)

        SECRET_KEY = "change-me-in-production"
        TOKEN_TTL = 3600  # seconds


        def hash_password(password: str) -> str:
            \"\"\"Return a bcrypt hash of the given password.\"\"\"
            import bcrypt
            return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


        def verify_password(password: str, hashed: str) -> bool:
            \"\"\"Verify a plaintext password against its stored hash.\"\"\"
            import bcrypt
            return bcrypt.checkpw(password.encode(), hashed.encode())


        def generate_token(user_id: int) -> str:
            \"\"\"Generate a signed JWT-like token for the given user.\"\"\"
            payload = f"{user_id}:{int(time.time()) + TOKEN_TTL}"
            sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
            logger.debug("Token generated for user_id=%d", user_id)
            return f"{payload}.{sig}"


        def validate_token(token: str) -> int | None:
            \"\"\"Validate a token and return user_id, or None if invalid/expired.\"\"\"
            try:
                payload, sig = token.rsplit(".", 1)
                expected = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig, expected):
                    logger.warning("Token signature mismatch")
                    return None
                user_id_str, expiry_str = payload.split(":")
                if int(expiry_str) < int(time.time()):
                    logger.warning("Token expired for user_id=%s", user_id_str)
                    return None
                return int(user_id_str)
            except Exception as exc:
                logger.error("Token validation error: %s", exc)
                return None


        def require_auth(fn: Callable) -> Callable:
            \"\"\"Decorator that enforces authentication on a handler.\"\"\"
            @wraps(fn)
            def wrapper(request, *args, **kwargs):
                token = request.headers.get("Authorization", "").removeprefix("Bearer ")
                user_id = validate_token(token)
                if user_id is None:
                    raise PermissionError("Unauthorised")
                request.user_id = user_id
                return fn(request, *args, **kwargs)
            return wrapper
        """)),

    ("src/workers/jobs.py", dedent("""\
        \"\"\"Background job definitions.\"\"\"
        import logging
        import smtplib
        from email.mime.text import MIMEText
        from pathlib import Path

        logger = logging.getLogger(__name__)


        def email_dispatch(job) -> None:
            \"\"\"Send a transactional email.\"\"\"
            msg = MIMEText(job.payload["body"])
            msg["Subject"] = job.payload["subject"]
            msg["From"] = "noreply@example.com"
            msg["To"] = job.payload["to"]
            # TODO: move SMTP config to environment variables
            with smtplib.SMTP("smtp.internal", 587) as smtp:
                smtp.sendmail(msg["From"], [msg["To"]], msg.as_string())
                logger.info("Email sent to %s subject=%r", msg["To"], msg["Subject"])


        def report_generate(job) -> None:
            \"\"\"Generate and store a scheduled report.\"\"\"
            report_id = job.payload["report_id"]
            output_path = Path(f"/var/reports/{report_id}.pdf")
            logger.info("Generating report %s -> %s", report_id, output_path)
            # TODO: implement actual report rendering
            output_path.write_bytes(b"placeholder")
            logger.info("Report %s complete", report_id)


        def data_export(job) -> None:
            \"\"\"Export data to a remote destination.\"\"\"
            dest = job.payload["destination"]
            logger.info("Starting data export to %s", dest)
            # TODO: implement chunked upload for large datasets
            raise NotImplementedError("data_export not yet implemented")


        def invoice_generate(job) -> None:
            \"\"\"Generate an invoice PDF for an order.\"\"\"
            order_id = job.payload["order_id"]
            logger.info("Generating invoice for order %s", order_id)
            # TODO: pull order details from DB
            output_path = Path(f"/var/invoices/inv_{order_id}.pdf")
            output_path.write_bytes(b"placeholder")
            logger.info("Invoice generated: %s", output_path)


        def cleanup(job) -> None:
            \"\"\"Remove stale temp files and expired sessions.\"\"\"
            logger.info("Starting cleanup job")
            # TODO: parameterise max_age
            removed = 0
            for p in Path("/tmp").glob("app_tmp_*"):
                p.unlink()
                removed += 1
            logger.info("Cleanup removed %d temp files", removed)
        """)),

    ("docs/runbook.md", dedent("""\
        # Operations Runbook

        ## Restarting Services

        To restart the application server:

            systemctl restart app-server

        To restart the worker pool:

            systemctl restart app-workers

        Always check logs after restart:

            journalctl -u app-server -n 50 --no-pager

        ## Investigating Errors

        ### Database connection errors

        If you see `DB_CONN_REFUSED` in the error log, check:

        1. Database pod is running: `kubectl get pods -n db`
        2. Network policy allows app -> db on port 5432
        3. Connection pool not exhausted (check `pool_size` in app.conf)

        ### Payment gateway timeouts

        Error code: `GW_TIMEOUT`

        The payment gateway has a hard timeout of 30 seconds. If timeouts
        persist, check the gateway status page and escalate to the payments team.
        Do NOT increase the timeout value without approval.

        ## Deployment

        Deployments are managed via GitHub Actions. To trigger a manual deploy:

            gh workflow run deploy.yml --ref main

        ### Rollback procedure

        If a deployment causes errors:

        1. Identify the last good release tag: `git tag --list 'v*' | sort -V | tail -5`
        2. Trigger rollback: `gh workflow run rollback.yml -f tag=<TAG>`
        3. Monitor error rate in Grafana for 10 minutes post-rollback

        ## Alerts

        | Alert                | Threshold      | Action                        |
        |----------------------|----------------|-------------------------------|
        | ErrorRateHigh        | >1% per minute | Page on-call, check app.log   |
        | DiskUsageHigh        | >85%           | Run cleanup job manually      |
        | WorkerQueueDepthHigh | >50 jobs       | Scale worker pool             |
        | PaymentGWTimeout     | >3 per hour    | Escalate to payments team     |
    """)),

    ("docs/api.md", dedent("""\
        # API Reference

        Base URL: `https://api.example.com`

        ## Authentication

        All endpoints except `/health` require a Bearer token in the
        `Authorization` header:

            Authorization: Bearer <token>

        Tokens are obtained via `POST /auth/login` and expire after 3600 seconds.

        ## Endpoints

        ### GET /api/users

        Returns a list of active users. Requires `admin` role.

        **Response 200:**
        ```json
        [{"id": 1, "username": "alice", "role": "admin"}]
        ```

        ### POST /api/users

        Create a new user. Requires `admin` role.

        **Request body:**
        ```json
        {"username": "newuser", "email": "newuser@example.com", "role": "user"}
        ```

        ### GET /api/orders

        Returns orders for the authenticated user (or all orders for admins).

        ### POST /api/orders

        Place a new order.

        **Request body:**
        ```json
        {"items": [{"product_id": 101, "qty": 2}], "total": 159.98}
        ```

        ### DELETE /api/sessions/{id}

        Invalidate a session by ID.

        ## Error codes

        | Code              | HTTP | Description                        |
        |-------------------|------|------------------------------------|
        | DB_CONN_REFUSED   | 503  | Database unreachable               |
        | GW_TIMEOUT        | 504  | Payment gateway timed out          |
        | NULL_POINTER      | 500  | Unhandled exception                |
        | DISK_FULL         | 507  | Insufficient storage               |
        | EXPORT_UNREACHABLE| 503  | Export destination unreachable     |
    """)),

    ("scripts/deploy.sh", dedent("""\
        #!/usr/bin/env bash
        set -euo pipefail

        # deploy.sh - Build, test, and deploy the application
        # Usage: ./deploy.sh [--env ENV] [--tag TAG] [--dry-run]

        ENV=${ENV:-production}
        TAG=${TAG:-$(git describe --tags --abbrev=0)}
        DRY_RUN=false

        while [[ $# -gt 0 ]]; do
            case "$1" in
                --env)   ENV="$2"; shift 2 ;;
                --tag)   TAG="$2"; shift 2 ;;
                --dry-run) DRY_RUN=true; shift ;;
                *) echo "Unknown flag: $1"; exit 1 ;;
            esac
        done

        echo "Deploying version $TAG to $ENV"

        # Build
        docker build -t "myapp:$TAG" .
        docker tag "myapp:$TAG" "registry.internal/myapp:$TAG"
        docker tag "myapp:$TAG" "registry.internal/myapp:latest"

        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Dry run: skipping push and deploy"
            exit 0
        fi

        # Push
        docker push "registry.internal/myapp:$TAG"
        docker push "registry.internal/myapp:latest"

        # Deploy
        kubectl set image deployment/app app="registry.internal/myapp:$TAG" -n "$ENV"
        kubectl rollout status deployment/app -n "$ENV" --timeout=300s

        echo "Deploy complete: $TAG -> $ENV"
        # TODO: notify Slack on successful deploy
    """)),

    ("scripts/backup.sh", dedent("""\
        #!/usr/bin/env bash
        set -euo pipefail

        # backup.sh - Dump the database and upload to S3
        # Usage: ./backup.sh [--db DB_NAME] [--bucket S3_BUCKET]

        DB_NAME=${DB_NAME:-appdb}
        S3_BUCKET=${S3_BUCKET:-s3://backups.example.com}
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="/tmp/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

        echo "Starting backup of $DB_NAME"
        pg_dump "$DB_NAME" | gzip > "$BACKUP_FILE"
        echo "Backup written to $BACKUP_FILE"

        aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/db/$DB_NAME/$TIMESTAMP.sql.gz"
        echo "Uploaded to $S3_BUCKET"

        # Retain only last 30 backups
        aws s3 ls "$S3_BUCKET/db/$DB_NAME/" \
            | sort \
            | head -n -30 \
            | awk '{print $4}' \
            | xargs -I{} aws s3 rm "$S3_BUCKET/db/$DB_NAME/{}"

        rm -f "$BACKUP_FILE"
        echo "Backup complete"
        # TODO: send alert if backup size is unexpectedly small
    """)),
]


# ── Corpus helpers ────────────────────────────────────────────────────────────


def write_corpus(base: Path) -> None:
    for rel_path, content in CORPUS:
        dest = base / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)


def corpus_files(base: Path) -> list[Path]:
    return sorted(base.rglob("*") if False else [base / p for p, _ in CORPUS])


# ── Run a shell command and capture output ────────────────────────────────────


def run_cmd(cmd: str, cwd: Path | None = None) -> tuple[bool, str, str]:
    """Run a shell command. Returns (ok, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(cwd) if cwd else None,
        )
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 10 seconds."
    ok = result.returncode == 0
    return ok, result.stdout, result.stderr.strip()


# ── Problem definitions ───────────────────────────────────────────────────────
#
# Each problem dict:
#   title           - short name
#   question        - what the user is asked to do
#   hint            - which file(s) to search (shown with question)
#   grep_answer     - canonical grep command (uses <CORPUS> placeholder for base dir)
#   rg_answer       - canonical rg command
#   expected        - the exact expected stdout (computed against written corpus)
#   compare         - "exact" | "set" | "count" | "fileset"
#
# All commands use <CORPUS> as a placeholder for the corpus base directory.
# We resolve expected output by running the rg_answer command at startup.


def _resolve(base: Path, cmd: str) -> str:
    """Run a command with <CORPUS> replaced, return stripped stdout.
    Exit code 1 from grep/rg means 'no matches' - that is valid output."""
    resolved = cmd.replace("<CORPUS>", str(base))
    try:
        result = subprocess.run(
            resolved,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Reference command timed out:\n  cmd: {resolved}")
    # exit 0 = matches found, exit 1 = no matches (valid), exit 2+ = error
    if result.returncode >= 2:
        raise RuntimeError(f"Reference command failed (exit {result.returncode}):\n  cmd: {resolved}\n  err: {result.stderr.strip()}")
    return result.stdout.strip()


def make_problems(base: Path) -> list[dict]:
    """Build problem list, resolving expected answers against the written corpus."""

    def p(title, question, hint, grep_answer, rg_answer, compare,
          grep_question=None, rg_question=None):
        """
        grep_question / rg_question: optional phase-specific question overrides.
        If omitted, both phases use the same `question`.
        Expected output is computed independently per tool so rg-specific flags
        (--stats, -S, etc.) don't need to match grep's output exactly.
        """
        grep_expected = _resolve(base, grep_answer)
        rg_expected   = _resolve(base, rg_answer)
        return dict(
            title=title,
            question=question,
            grep_question=grep_question or question,
            rg_question=rg_question or question,
            hint=hint,
            grep_answer=grep_answer,
            rg_answer=rg_answer,
            grep_expected=grep_expected,
            rg_expected=rg_expected,
            compare=compare,
        )

    problems = [
        # 1 ── Basic match ─────────────────────────────────────────────────────
        p(
            title="Find all ERROR lines",
            question="Print every line in app.log that contains the word ERROR.",
            hint="logs/app.log",
            grep_answer="grep 'ERROR' <CORPUS>/logs/app.log",
            rg_answer="rg 'ERROR' <CORPUS>/logs/app.log",
            compare="set",
        ),
        # 2 ── Case-insensitive ────────────────────────────────────────────────
        p(
            title="Case-insensitive search",
            question=(
                "Find all lines in the runbook (docs/runbook.md) that contain the word "
                "'error' in any capitalisation (error, Error, ERROR, etc.)."
            ),
            hint="docs/runbook.md",
            grep_answer="grep -i 'error' <CORPUS>/docs/runbook.md",
            rg_answer="rg -i 'error' <CORPUS>/docs/runbook.md",
            compare="set",
        ),
        # 3 ── Invert match ────────────────────────────────────────────────────
        p(
            title="Invert match - non-comment config lines",
            question=(
                "Print all lines in config/app.conf that do NOT start with a '#' "
                "and are not blank."
            ),
            hint="config/app.conf",
            grep_answer="grep -v '^#' <CORPUS>/config/app.conf | grep -v '^$'",
            rg_answer="rg -v '^#' <CORPUS>/config/app.conf | rg -v '^$'",
            compare="set",
        ),
        # 4 ── Line numbers ────────────────────────────────────────────────────
        p(
            title="Match with line numbers",
            question=(
                "Show every line in logs/worker.log that contains 'ERROR' or 'WARN', "
                "prefixed by its line number."
            ),
            hint="logs/worker.log",
            grep_answer="grep -n 'ERROR\\|WARN' <CORPUS>/logs/worker.log",
            rg_answer="rg -n 'ERROR|WARN' <CORPUS>/logs/worker.log",
            compare="set",
        ),
        # 5 ── Count matches ───────────────────────────────────────────────────
        p(
            title="Count matching lines",
            question="How many lines in logs/access.log contain a 200 status code? Print just the count.",
            hint="logs/access.log",
            grep_answer="grep -c '\" 200 ' <CORPUS>/logs/access.log",
            rg_answer="rg -c '\" 200 ' <CORPUS>/logs/access.log",
            compare="exact",
        ),
        # 6 ── Filenames only (-l) ─────────────────────────────────────────────
        p(
            title="List matching filenames only",
            question=(
                "Search the entire corpus recursively and print only the names of files "
                "that contain the word 'TODO'."
            ),
            hint="<CORPUS>/ (recursive)",
            grep_answer="grep -rl 'TODO' <CORPUS>",
            rg_answer="rg -l 'TODO' <CORPUS>",
            compare="fileset",
        ),
        # 7 ── Files WITHOUT a match (-L / --files-without-match) ───────────────
        p(
            title="List files without a match",
            question=(
                "Print the names of files under docs/ that do NOT contain the word 'TODO'."
            ),
            hint="docs/",
            grep_answer="grep -rL 'TODO' <CORPUS>/docs",
            rg_answer="rg --files-without-match 'TODO' <CORPUS>/docs",
            compare="fileset",
        ),
        # 8 ── Recursive search ────────────────────────────────────────────────
        p(
            title="Recursive search across logs/",
            question=(
                "Recursively search all files under logs/ and print every line "
                "that mentions a specific user: 'alice'."
            ),
            hint="logs/ (recursive)",
            grep_answer="grep -r 'alice' <CORPUS>/logs",
            rg_answer="rg 'alice' <CORPUS>/logs",
            compare="set",
        ),
        # 9 ── Fixed string (-F) ───────────────────────────────────────────────
        p(
            title="Fixed-string search",
            question=(
                "Search config/app.conf for the literal string 'pool_size = 10' "
                "(treat it as a fixed string, not a regex)."
            ),
            hint="config/app.conf",
            grep_answer="grep -F 'pool_size = 10' <CORPUS>/config/app.conf",
            rg_answer="rg -F 'pool_size = 10' <CORPUS>/config/app.conf",
            compare="exact",
        ),
        # 10 ── Word boundary (-w) ─────────────────────────────────────────────
        p(
            title="Whole-word match",
            question=(
                "Find lines in data/users.csv where the role is exactly 'admin' "
                "(whole word - must not match 'administrator' etc.)."
            ),
            hint="data/users.csv",
            grep_answer="grep -w 'admin' <CORPUS>/data/users.csv",
            rg_answer="rg -w 'admin' <CORPUS>/data/users.csv",
            compare="set",
        ),
        # 11 ── Extended regex ─────────────────────────────────────────────────
        p(
            title="Extended regex - HTTP 4xx or 5xx",
            question=(
                "Find all lines in logs/access.log where the HTTP status code is "
                "4xx or 5xx (i.e. starts with 4 or 5, followed by two digits)."
            ),
            hint="logs/access.log",
            grep_answer="grep -E '\" [45][0-9]{2} ' <CORPUS>/logs/access.log",
            rg_answer="rg '\" [45][0-9]{2} ' <CORPUS>/logs/access.log",
            compare="set",
        ),
        # 12 ── Anchors ────────────────────────────────────────────────────────
        p(
            title="Anchor to line start",
            question=(
                "Find all lines in config/workers.toml that start with '[' "
                "(i.e. TOML section headers)."
            ),
            hint="config/workers.toml",
            grep_answer="grep '^\\[' <CORPUS>/config/workers.toml",
            rg_answer="rg '^\\[' <CORPUS>/config/workers.toml",
            compare="set",
        ),
        # 13 ── Context lines (-A) ─────────────────────────────────────────────
        p(
            title="Context lines after match",
            question=(
                "In docs/runbook.md, find the line containing 'GW_TIMEOUT' and "
                "show that line plus the 2 lines after it."
            ),
            hint="docs/runbook.md",
            grep_answer="grep -A 2 'GW_TIMEOUT' <CORPUS>/docs/runbook.md",
            rg_answer="rg -A 2 'GW_TIMEOUT' <CORPUS>/docs/runbook.md",
            compare="exact",
        ),
        # 14 ── Context lines (-B) ─────────────────────────────────────────────
        p(
            title="Context lines before match",
            question=(
                "In docs/runbook.md, find the line containing 'Rollback procedure' "
                "and show the 2 lines before it as well."
            ),
            hint="docs/runbook.md",
            grep_answer="grep -B 2 'Rollback procedure' <CORPUS>/docs/runbook.md",
            rg_answer="rg -B 2 'Rollback procedure' <CORPUS>/docs/runbook.md",
            compare="exact",
        ),
        # 15 ── Context lines (-C) ─────────────────────────────────────────────
        p(
            title="Context lines around match",
            question=(
                "In logs/app.log, find the line about 'Payment gateway timeout' and "
                "show 1 line of context on each side."
            ),
            hint="logs/app.log",
            grep_answer="grep -C 1 'Payment gateway timeout' <CORPUS>/logs/app.log",
            rg_answer="rg -C 1 'Payment gateway timeout' <CORPUS>/logs/app.log",
            compare="exact",
        ),
        # 16 ── Multiple patterns (-e) ─────────────────────────────────────────
        p(
            title="Multiple patterns",
            question=(
                "Find all lines in data/errors.json that contain either "
                "'DB_CONN_REFUSED' or 'GW_TIMEOUT'."
            ),
            hint="data/errors.json",
            grep_answer="grep -e 'DB_CONN_REFUSED' -e 'GW_TIMEOUT' <CORPUS>/data/errors.json",
            rg_answer="rg 'DB_CONN_REFUSED|GW_TIMEOUT' <CORPUS>/data/errors.json",
            compare="set",
        ),
        # 17 ── rg --type ──────────────────────────────────────────────────────
        p(
            title="Search only Python files",
            question=(
                "Search the entire corpus for 'TODO' but only in Python (.py) files."
            ),
            grep_question=(
                "Search the entire corpus for 'TODO' but only in Python (.py) files. "
                "Use grep's --include flag."
            ),
            rg_question=(
                "Now do the same with rg, using its --type flag instead of --include."
            ),
            hint="<CORPUS>/ (recursive)",
            grep_answer="grep -r --include='*.py' 'TODO' <CORPUS>",
            rg_answer="rg --type py 'TODO' <CORPUS>",
            compare="set",
        ),
        # 18 ── rg --glob ──────────────────────────────────────────────────────
        p(
            title="Glob include pattern",
            question=(
                "Search the entire corpus for 'password' but only in files whose name "
                "ends in .yaml or .yml."
            ),
            grep_question=(
                "Search the entire corpus for 'password' but only in .yaml/.yml files. "
                "Use grep's --include flag (you'll need it twice)."
            ),
            rg_question=(
                "Now do the same with rg, using a single -g glob pattern instead."
            ),
            hint="<CORPUS>/ (recursive)",
            grep_answer="grep -r --include='*.yaml' --include='*.yml' 'password' <CORPUS>",
            rg_answer="rg -g '*.y*ml' 'password' <CORPUS>",
            compare="set",
        ),
        # 19 ── rg --glob exclude ──────────────────────────────────────────────
        p(
            title="Glob exclude pattern",
            question=(
                "Search the entire corpus for 'logger' but EXCLUDE any files under docs/."
            ),
            grep_question=(
                "Search the entire corpus for 'logger' but exclude the docs/ directory. "
                "Use grep's --exclude-dir flag."
            ),
            rg_question=(
                "Now do the same with rg, using a -g '!...' glob exclusion pattern."
            ),
            hint="<CORPUS>/ (exclude docs/)",
            grep_answer="grep -r --exclude-dir=docs 'logger' <CORPUS>",
            rg_answer="rg -g '!docs/*' 'logger' <CORPUS>",
            compare="set",
        ),
        # 20 ── rg smart-case ──────────────────────────────────────────────────
        p(
            title="Smart case search",
            question=(
                "Search logs/app.log for 'warn' matching any capitalisation."
            ),
            grep_question=(
                "Search logs/app.log for 'warn' matching any capitalisation. "
                "Use grep's -i flag."
            ),
            rg_question=(
                "Now do the same with rg's smart-case flag (-S). "
                "Smart-case is case-insensitive when the pattern is all lowercase, "
                "case-sensitive when it contains any uppercase - try it both ways."
            ),
            hint="logs/app.log",
            grep_answer="grep -i 'warn' <CORPUS>/logs/app.log",
            rg_answer="rg -S 'warn' <CORPUS>/logs/app.log",
            compare="set",
        ),
        # 21 ── rg --stats ─────────────────────────────────────────────────────
        p(
            title="Stats summary",
            question=(
                "Search the entire corpus for 'error' (case-insensitive). "
                "We only check that you produce non-empty output."
            ),
            grep_question=(
                "Search the entire corpus for 'error' case-insensitively with grep -ri."
            ),
            rg_question=(
                "Now do the same with rg, but add --stats to get a summary of total "
                "matches and files searched printed at the end."
            ),
            hint="<CORPUS>/ (recursive, case-insensitive)",
            grep_answer="grep -ri 'error' <CORPUS>",
            rg_answer="rg -i --stats 'error' <CORPUS>",
            compare="nonempty",
        ),
        # 22 ── Multiline rg (-U) ──────────────────────────────────────────────
        p(
            title="Multiline match",
            question=(
                "Find the lines in logs/app.log where 'Retrying payment' appears on one "
                "line immediately followed by a line containing 'succeeded'."
            ),
            grep_question=(
                "Find the lines in logs/app.log where 'Retrying payment' appears on one "
                "line immediately followed by a line containing 'succeeded'. "
                "Use grep -A 1 piped into a second grep."
            ),
            rg_question=(
                "Now do the same with rg's multiline mode (-U), using a single pattern "
                "that spans the newline between the two lines."
            ),
            hint="logs/app.log",
            grep_answer="grep -A 1 'Retrying payment' <CORPUS>/logs/app.log | grep -B 1 'succeeded'",
            rg_answer="rg -U 'Retrying payment.*\\nsucceeded' <CORPUS>/logs/app.log",
            compare="set",
        ),
        # 23 ── PCRE2 named groups ─────────────────────────────────────────────
        p(
            title="Named capture groups",
            question=(
                "Extract just the IP addresses from the start of each line in "
                "logs/access.log using a named capture group (?P<ip>...)."
            ),
            grep_question=(
                "Extract just the IP addresses from the start of each line in "
                "logs/access.log. Use grep -oP with a named capture group (?P<ip>...)."
            ),
            rg_question=(
                "Now do the same with rg -oP. The named group syntax is identical - "
                "notice how rg highlights the named group differently."
            ),
            hint="logs/access.log",
            grep_answer="grep -oP '^(?P<ip>[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)' <CORPUS>/logs/access.log",
            rg_answer="rg -oP '^(?P<ip>[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)' <CORPUS>/logs/access.log",
            compare="set",
        ),
        # 24 ── Only matching (-o) ─────────────────────────────────────────────
        p(
            title="Print only the matching part",
            question=(
                "In logs/access.log, extract and print only the IP addresses "
                "(the first field on each line). Use the -o flag to print only the match."
            ),
            hint="logs/access.log",
            grep_answer="grep -oE '^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+' <CORPUS>/logs/access.log",
            rg_answer="rg -o '^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+' <CORPUS>/logs/access.log",
            compare="set",
        ),
        # 25 ── Recursive + filename in output ─────────────────────────────────
        p(
            title="Recursive search with filename prefix",
            question=(
                "Recursively search the src/ directory for any line containing "
                "'logger.error' or 'logger.warning', printing the filename and line "
                "number for each match."
            ),
            hint="src/ (recursive)",
            grep_answer="grep -rnE 'logger\\.(error|warning)' <CORPUS>/src",
            rg_answer="rg -n 'logger\\.(error|warning)' <CORPUS>/src",
            compare="set",
        ),
        # 26 ── Count per file ─────────────────────────────────────────────────
        p(
            title="Count matches per file",
            question=(
                "Recursively search the scripts/ directory for the word 'echo' and "
                "print the count of matching lines per file."
            ),
            hint="scripts/",
            grep_answer="grep -rc 'echo' <CORPUS>/scripts",
            rg_answer="rg -c 'echo' <CORPUS>/scripts",
            compare="set",
        ),
        # 27 ── Character classes ──────────────────────────────────────────────
        p(
            title="Character class - job IDs",
            question=(
                "In logs/worker.log, find all lines that contain a job_id value "
                "(pattern: 'job_id=' followed by exactly 4 hex characters)."
            ),
            hint="logs/worker.log",
            grep_answer="grep -E 'job_id=[0-9a-f]{4}' <CORPUS>/logs/worker.log",
            rg_answer="rg 'job_id=[0-9a-f]{4}' <CORPUS>/logs/worker.log",
            compare="set",
        ),
        # 28 ── Null-separated output for piping (-Z) ──────────────────────────
        p(
            title="Search shell scripts for set -e",
            question=(
                "Find all lines in scripts/ that contain 'set -e' (the bash strict "
                "mode directive), showing both the filename and line content."
            ),
            hint="scripts/",
            grep_answer="grep -r 'set -e' <CORPUS>/scripts",
            rg_answer="rg 'set -e' <CORPUS>/scripts",
            compare="set",
        ),
        # 29 ── Grep across CSV column ─────────────────────────────────────────
        p(
            title="Filter CSV by column value",
            question=(
                "In data/users.csv, find all rows where the user is inactive "
                "(the 'active' column is 'false')."
            ),
            hint="data/users.csv",
            grep_answer="grep -E ',false,' <CORPUS>/data/users.csv",
            rg_answer="rg ',false,' <CORPUS>/data/users.csv",
            compare="set",
        ),
        # 30 ── Combining flags ─────────────────────────────────────────────────
        p(
            title="High-priority jobs in TOML",
            question=(
                "In config/workers.toml, find all lines that set priority to 'high' "
                "and show 1 line of context before each match so you can see which job "
                "section it belongs to."
            ),
            hint="config/workers.toml",
            grep_answer="grep -B 1 'priority = high' <CORPUS>/config/workers.toml",
            rg_answer="rg -B 1 'priority = high' <CORPUS>/config/workers.toml",
            compare="exact",
        ),
        # 31 ── Anchor end of line ─────────────────────────────────────────────
        p(
            title="Anchor to line end",
            question=(
                "In config/app.conf, find all lines that end with 'true' or 'false' "
                "(boolean values)."
            ),
            hint="config/app.conf",
            grep_answer="grep -E '(true|false)$' <CORPUS>/config/app.conf",
            rg_answer="rg '(true|false)$' <CORPUS>/config/app.conf",
            compare="set",
        ),
        # 32 ── Search compressed / binary awareness ───────────────────────────
        p(
            title="Find decorated Python functions",
            question=(
                "In src/api/handlers.py, find all lines that start with '@' "
                "(Python decorator lines)."
            ),
            hint="src/api/handlers.py",
            grep_answer="grep '^@' <CORPUS>/src/api/handlers.py",
            rg_answer="rg '^@' <CORPUS>/src/api/handlers.py",
            compare="set",
        ),
        # 33 ── rg replace ─────────────────────────────────────────────────────
        p(
            title="Replace match in output",
            question=(
                "In data/users.csv, replace the email domain '@example.com' with "
                "'@corp.io' in the output (without modifying the file)."
            ),
            grep_question=(
                "In data/users.csv, extract all email addresses and replace the domain "
                "'@example.com' with '@corp.io'. Use grep -oE to extract emails, "
                "then pipe to sed for the substitution."
            ),
            rg_question=(
                "Now do the same with rg in a single command, using rg's -o and "
                "--replace (-r) flags."
            ),
            hint="data/users.csv",
            grep_answer="grep -oE '[a-z]+@example\\.com' <CORPUS>/data/users.csv | sed 's/@example\\.com/@corp.io/'",
            rg_answer="rg -o '@example\\.com' -r '@corp.io' <CORPUS>/data/users.csv",
            compare="set",
        ),
    ]

    return problems


# ── Comparison ────────────────────────────────────────────────────────────────


def normalise_paths(text: str, base: Path) -> str:
    """Replace absolute corpus paths with a stable placeholder."""
    return text.replace(str(base), "<CORPUS>")


def compare_outputs(expected: str, actual: str, mode: str) -> bool:
    if mode == "exact":
        return expected.strip() == actual.strip()
    if mode == "set":
        return sorted(expected.strip().splitlines()) == sorted(actual.strip().splitlines())
    if mode == "count":
        return expected.strip() == actual.strip()
    if mode == "fileset":
        def extract(s): return sorted(line.strip() for line in s.strip().splitlines() if line.strip())
        return extract(expected) == extract(actual)
    if mode == "nonempty":
        return bool(actual.strip())
    return expected.strip() == actual.strip()


# ── Tool detection ────────────────────────────────────────────────────────────


def detect_tool(command: str) -> str:
    """Return 'rg', 'grep', or 'unknown' based on the first token."""
    first = command.strip().split()[0] if command.strip() else ""
    if first in ("rg", "ripgrep"):
        return "rg"
    if first in ("grep", "egrep", "fgrep"):
        return "grep"
    return "unknown"


# ── Display helpers ───────────────────────────────────────────────────────────


def print_separator(char: str = "─", width: int = 65) -> None:
    print(dim(char * width))


def show_answer(label: str, cmd: str, base: Path) -> None:
    resolved = cmd.replace("<CORPUS>", str(base))
    print(f"  {bold(label):<6}  {dim(resolved)}")


def show_both_answers(problem: dict, base: Path) -> None:
    print(yellow("\n  Solutions:"))
    show_answer("grep", problem["grep_answer"], base)
    show_answer("rg", problem["rg_answer"], base)


def _phase_loop(
    problem: dict,
    base: Path,
    phase: str,               # "grep" or "rg"
    phase_label: str,         # e.g. "grep  [phase 1/2]"
    wrong_attempts_ref: list, # single-element list used as mutable int
) -> tuple[bool, bool]:
    """
    Run one interactive phase (grep or rg).
    Returns (solved, skipped).
    """
    expected = problem[f"{phase}_expected"]
    question = problem[f"{phase}_question"]
    required_tool = phase  # enforce correct tool

    print()
    print(cyan(f"  --- {phase_label} ---"))
    print(f"\n  {question}\n")
    print(cyan(f"  File(s): {problem['hint'].replace('<CORPUS>', str(base))}"))
    print(dim("  Corpus:  " + str(base)))
    print()
    print(dim(f"  Use {phase}. You can use <CORPUS> as a placeholder for the corpus root."))
    print(dim("  Type 'skip' to see the answer and move on."))
    print()

    while True:
        try:
            user_input = input(bold(f"  [{phase}] > ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise

        if not user_input:
            continue

        if user_input.lower() == "skip":
            ref = problem[f"{phase}_answer"].replace("<CORPUS>", str(base))
            print(yellow(f"\n  Answer: {dim(ref)}"))
            preview = normalise_paths(expected, base)
            print(dim("  Expected output (first 6 lines):"))
            for line in preview.splitlines()[:6]:
                print(dim("    " + line))
            return False, True  # solved=False, skipped=True

        resolved = user_input.replace("<CORPUS>", str(base))
        tool = detect_tool(resolved)

        if tool not in (phase, "unknown"):
            print(red(f"\n  Use {phase} for this phase, not {tool}."))
            print(dim("  Try again, or type 'skip'.\n"))
            continue

        ok, stdout, stderr = run_cmd(resolved)
        if not ok and not stdout.strip():
            wrong_attempts_ref[0] += 1
            print(red(f"\n  Error: {stderr or 'Command returned non-zero with no output.'}"))
            print(dim("  Try again, or type 'skip'.\n"))
            continue

        actual = stdout.strip()
        matched = compare_outputs(expected, actual, problem["compare"])

        if matched:
            print(green(f"\n  Correct!"))
            return True, False  # solved=True, skipped=False
        else:
            wrong_attempts_ref[0] += 1
            print(red("\n  Not quite."))
            print(cyan("  Your output (first 5 lines):"))
            for line in actual.splitlines()[:5]:
                print(dim("    " + normalise_paths(line, base)))
            print(cyan("  Expected (first 5 lines):"))
            for line in expected.splitlines()[:5]:
                print(dim("    " + normalise_paths(line, base)))
            print(dim("\n  Try again, or type 'skip'.\n"))


# ── Main session loop ─────────────────────────────────────────────────────────


def run_session(base: Path, problems: list[dict]) -> None:
    shuffled = problems.copy()
    random.shuffle(shuffled)
    total = len(shuffled)

    grep_solved = grep_skipped = 0
    rg_solved   = rg_skipped   = 0
    wrong_attempts = [0]  # mutable ref passed into phase loops

    for idx, problem in enumerate(shuffled, start=1):
        print()
        print_separator()
        print(bold(f"Problem {idx}/{total}: {problem['title']}"))
        print_separator()
        print(f"\n{problem['question']}")

        # ── Phase 1: grep ────────────────────────────────────────────────────
        solved, skipped = _phase_loop(
            problem, base,
            phase="grep",
            phase_label="grep  [phase 1/2]",
            wrong_attempts_ref=wrong_attempts,
        )
        if solved:
            grep_solved += 1
        if skipped:
            grep_skipped += 1

        # ── Phase 2: rg ──────────────────────────────────────────────────────
        solved, skipped = _phase_loop(
            problem, base,
            phase="rg",
            phase_label="rg    [phase 2/2]",
            wrong_attempts_ref=wrong_attempts,
        )
        if solved:
            rg_solved += 1
        if skipped:
            rg_skipped += 1

        # ── Show both solutions after both phases complete ───────────────────
        show_both_answers(problem, base)
        print()

    print()
    print_separator("═")
    print(bold("  Session complete!"))
    print_separator("═")
    grep_label = green(f"grep solved: {grep_solved}/{total}") + (f"  skipped: {grep_skipped}" if grep_skipped else "")
    rg_label   = green(f"rg   solved: {rg_solved}/{total}")   + (f"  skipped: {rg_skipped}"   if rg_skipped   else "")
    print(f"  {grep_label}")
    print(f"  {rg_label}")
    print(f"  {red(f'Wrong attempts: {wrong_attempts[0]}')}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive grep/ripgrep teacher using a realistic multi-file corpus.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all problem titles and exit.",
    )
    parser.add_argument(
        "--problem",
        type=int,
        metavar="N",
        help="Run a single problem by its 1-based index (from --list).",
    )
    args = parser.parse_args()

    # Check tools are available
    missing = []
    for tool in ("grep", "rg"):
        ok, _, _ = run_cmd(f"{tool} --version")
        if not ok:
            missing.append(tool)
    if missing:
        print(red(f"Error: the following tools are not installed or not on PATH: {', '.join(missing)}"), file=sys.stderr)
        sys.exit(1)

    # Write corpus to a temp directory
    tmp_dir = tempfile.mkdtemp(prefix="grep_teacher_")
    base = Path(tmp_dir)

    try:
        write_corpus(base)

        print(bold("\n  grep / rg Teacher"))
        print(dim("  Practise grep and ripgrep against a realistic multi-file corpus.\n"))
        print(dim(f"  Corpus written to: {base}\n"))

        problems = make_problems(base)

        if args.list:
            print(bold("  Problems:"))
            for i, prob in enumerate(problems, 1):
                print(f"  {i:>2}. {prob['title']}")
            print()
            return

        if args.problem is not None:
            if not (1 <= args.problem <= len(problems)):
                print(red(f"Error: --problem must be between 1 and {len(problems)}."), file=sys.stderr)
                sys.exit(1)
            selected = [problems[args.problem - 1]]
        else:
            selected = problems

        run_session(base, selected)

    except KeyboardInterrupt:
        print(dim("\n\n  Session interrupted. Goodbye!"))
    finally:
        # Clean up corpus
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
