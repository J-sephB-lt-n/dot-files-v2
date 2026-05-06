#!/usr/bin/env python3
"""
Personal time tracker: display a GUI popup to log hourly time entries for a given date.

Data is stored in ~/time-tracking/<YYYY-MM-DD>.json. Each file contains exactly
24 entries, one per hour (00:00–23:00), each with a project name and free-text
description.

Example usage:
$ personal_time_tracker
$ personal_time_tracker --date 2026-05-01

Place this script (without .py) in /usr/local/bin/ to make it globally available:
  sudo cp personal_time_tracker.py /usr/local/bin/personal_time_tracker
  sudo chmod +x /usr/local/bin/personal_time_tracker
"""

import argparse
import json
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from datetime import date, datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR = Path.home() / "time-tracking"
HOURS = [f"{h:02d}:00" for h in range(24)]
HISTORY_DAYS = 90


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def get_file_path(target_date: date) -> Path:
    """Return the JSON file path for the given date."""
    return DATA_DIR / f"{target_date.isoformat()}.json"


def ensure_data_dir() -> None:
    """Create ~/time-tracking/ if it does not already exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def blank_entries() -> list[dict]:
    """Return a list of 24 blank hourly entries."""
    return [{"hour": h, "project": "", "description": ""} for h in HOURS]


def load_entries(file_path: Path) -> list[dict]:
    """
    Load entries from the JSON file at file_path.

    If the file does not exist, create it with 24 blank entries and return them.

    Raises:
        OSError: On file read/write failures.
        json.JSONDecodeError: If the file contains malformed JSON.
        TypeError: If the top-level JSON value is not a list of dicts.
        KeyError: If an entry dict is missing the 'hour' key.
    """
    if not file_path.exists():
        entries = blank_entries()
        save_entries(file_path, entries)
        return entries

    with file_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Ensure all 24 hours are present (defensive: back-fill any missing hours)
    existing = {e["hour"]: e for e in data}
    return [
        existing.get(h, {"hour": h, "project": "", "description": ""}) for h in HOURS
    ]


def save_entries(file_path: Path, entries: list[dict]) -> None:
    """Write the 24 entries to the JSON file, creating it if necessary."""
    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)


def collect_historical_projects() -> list[str]:
    """
    Return a sorted list of unique project names found across all JSON files
    in ~/time-tracking/ dated within the last 90 days (inclusive of today).
    """
    cutoff = date.today() - timedelta(days=HISTORY_DAYS - 1)
    projects: set[str] = set()

    if not DATA_DIR.exists():
        return []

    for json_file in DATA_DIR.glob("*.json"):
        stem = json_file.stem
        try:
            file_date = date.fromisoformat(stem)
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        try:
            with json_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            for entry in data:
                name = entry.get("project", "").strip()
                if name:
                    projects.add(name)
        except (OSError, json.JSONDecodeError):
            continue

    return sorted(projects, key=str.casefold)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------


class TimeTrackerApp:
    """Main application window for the personal time tracker."""

    def __init__(self, root: tk.Tk, entries: list[dict], file_path: Path) -> None:
        """
        Initialise the time tracker popup.

        Args:
            root:      The tkinter root window.
            entries:   List of 24 hourly entry dicts loaded from disk.
            file_path: Path to the JSON file being edited.
        """
        self.root = root
        self.file_path = file_path
        self.entries = entries
        self.projects = collect_historical_projects()

        self._build_window()
        self._build_header()
        self._build_scrollable_rows()
        self._build_footer()
        self._scroll_to_current_hour()
        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ------------------------------------------------------------------
    # Window construction
    # ------------------------------------------------------------------

    def _build_window(self) -> None:
        """Configure the root window geometry and title."""
        self.root.title(f"Time Tracker — {self.file_path.stem}")
        self.root.attributes("-topmost", True)
        self.root.resizable(True, True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = 800
        win_h = int(screen_h * 0.80)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    def _build_header(self) -> None:
        """Build the column header row."""
        header = tk.Frame(self.root, padx=10, pady=6)
        header.pack(fill="x", side="top")

        tk.Label(
            header, text="Hour", width=6, anchor="w", font=("TkDefaultFont", 10, "bold")
        ).pack(side="left")
        tk.Label(
            header,
            text="Project",
            width=28,
            anchor="w",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(side="left", padx=(4, 0))
        tk.Label(
            header, text="Description", anchor="w", font=("TkDefaultFont", 10, "bold")
        ).pack(side="left", padx=(8, 0))

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", side="top")

    def _build_scrollable_rows(self) -> None:
        """Build the scrollable canvas containing one row per hour."""
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True, side="top")

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(canvas, padx=10)
        self.canvas_window = canvas.create_window(
            (0, 0), window=self.inner_frame, anchor="nw"
        )

        # Resize inner frame width when canvas resizes
        def _on_canvas_configure(event: tk.Event) -> None:
            canvas.itemconfig(self.canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)

        self.inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        # Mouse-wheel scrolling — scoped to when the cursor is over the canvas
        def _on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll(event: tk.Event) -> None:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _unbind_scroll(event: tk.Event) -> None:
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_scroll)
        canvas.bind("<Leave>", _unbind_scroll)

        self.canvas = canvas

        # Build one row per hour
        self.project_vars: list[tk.StringVar] = []
        self.desc_vars: list[tk.StringVar] = []
        self.row_frames: list[tk.Frame] = []

        for entry in self.entries:
            self._build_row(entry)

    def _build_row(self, entry: dict) -> None:
        """Build a single hourly entry row."""
        row = tk.Frame(self.inner_frame, pady=3)
        row.pack(fill="x")
        self.row_frames.append(row)

        # Hour label
        tk.Label(
            row, text=entry["hour"], width=6, anchor="w", font=("TkDefaultFont", 11)
        ).pack(side="left")

        # Project combobox
        project_var = tk.StringVar(value=entry["project"])
        combo = ttk.Combobox(
            row, textvariable=project_var, values=self.projects, width=26
        )
        combo.pack(side="left", padx=(4, 0))
        self.project_vars.append(project_var)

        # Description entry
        desc_var = tk.StringVar(value=entry["description"])
        desc_entry = tk.Entry(row, textvariable=desc_var, font=("TkDefaultFont", 11))
        desc_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.desc_vars.append(desc_var)

    def _build_footer(self) -> None:
        """Build the Submit and Cancel buttons at the bottom."""
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", side="top")

        footer = tk.Frame(self.root, padx=10, pady=10)
        footer.pack(fill="x", side="bottom")

        tk.Button(
            footer,
            text="Submit",
            width=12,
            font=("TkDefaultFont", 11),
            command=self._on_submit,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            footer,
            text="Cancel",
            width=12,
            font=("TkDefaultFont", 11),
            command=self._on_cancel,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    def _scroll_to_current_hour(self) -> None:
        """Scroll the view so the current hour's row is centred in the viewport."""
        current_hour = datetime.now().hour

        def _do_scroll() -> None:
            self.root.update_idletasks()
            total_rows = len(self.row_frames)
            if total_rows == 0:
                return
            # Fraction of total content height at which the target row starts.
            row_fraction = current_hour / total_rows
            # Approximate the viewport height as a fraction of total content height
            # so we can subtract half of it and centre the target row.
            content_h = self.canvas.bbox("all")
            if content_h:
                viewport_fraction = self.canvas.winfo_height() / content_h[3]
                fraction = max(0.0, row_fraction - viewport_fraction / 2)
            else:
                fraction = row_fraction
            self.canvas.yview_moveto(fraction)

        self.root.after(50, _do_scroll)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _collect_entries(self) -> list[dict]:
        """Read current widget state and return a list of 24 entry dicts."""
        return [
            {
                "hour": HOURS[i],
                "project": self.project_vars[i].get(),
                "description": self.desc_vars[i].get(),
            }
            for i in range(24)
        ]

    def _on_submit(self) -> None:
        """Save all entries to disk and close the window."""
        entries = self._collect_entries()
        try:
            save_entries(self.file_path, entries)
        except OSError as exc:
            messagebox.showerror(
                "Save Error",
                f"Could not save to {self.file_path}:\n{exc}",
            )
            return
        self.root.destroy()

    def _on_cancel(self) -> None:
        """Prompt for confirmation then discard changes and close."""
        confirmed = messagebox.askyesno(
            "Discard changes?",
            "Are you sure you want to cancel? All unsaved changes will be lost.",
        )
        if confirmed:
            self.root.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_date(value: str) -> date:
    """
    Parse a date string in YYYY-MM-DD format.

    Args:
        value: The date string to parse.

    Returns:
        A datetime.date object.

    Raises:
        argparse.ArgumentTypeError: If the string is not a valid date.
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format: YYYY-MM-DD"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log hourly time entries for a given day."
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="Date to edit (default: today)",
    )
    args = parser.parse_args()

    target_date: date = args.date if args.date is not None else date.today()

    ensure_data_dir()
    file_path = get_file_path(target_date)

    try:
        entries = load_entries(file_path)
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        # Can't show a GUI yet if tkinter hasn't started; fall back to stderr
        import sys

        print(f"Error loading {file_path}: {exc}", file=sys.stderr)
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror("Load Error", f"Could not load {file_path}:\n{exc}")
        root_err.destroy()
        return

    root = tk.Tk()
    TimeTrackerApp(root, entries, file_path)
    root.mainloop()


if __name__ == "__main__":
    main()
