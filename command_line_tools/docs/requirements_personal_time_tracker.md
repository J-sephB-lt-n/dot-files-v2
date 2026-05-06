# Requirements Document — `personal_time_tracker`

---

## 1) Project Needs (Project Drivers)

### 1.1 The Purpose of the Project

A personal command-line utility that, when run on a schedule, presents a GUI popup allowing the user to log what they worked on during each hour of the day. The tool captures and persists daily time-tracking data in a structured JSON format. It addresses the need for lightweight, low-friction time tracking without reliance on any external service or application.

### 1.2 Stakeholders

| Stakeholder | Role |
|---|---|
| josephbbolton | Sole user and developer; personal productivity tooling |

### 1.3 Relevant Facts and Assumptions

- Environment: Linux, Python 3, `tkinter` available
- Script is invoked on a schedule (e.g. cron), approximately 4 times per day
- Multiple simultaneous instances are permitted; no file locking is required
- The `~/time-tracking/` directory is the sole data store
- "Last 3 months" means a rolling 90-day window from today's date
- Concurrent writes from multiple instances use last-write-wins; this is an accepted risk

---

## 2) Project Requirements

### 2a) Project Constraints

- Language: Python 3, standard library only (`tkinter`, `json`, `argparse`, `os`, `datetime`, `pathlib`)
- No third-party dependencies
- Source file: `~/command_line_tools/personal_time_tracker.py`
- Deployed globally as `personal_time_tracker` in `/usr/local/bin/` (no `.py`), made executable via `chmod +x`
- Must follow conventions of `popup_msg.py`: type hints, docstrings, `main()` entry point, `if __name__ == "__main__"` guard
- Data directory: `~/time-tracking/`
- Data file naming: `<YYYY-MM-DD>.json` (today's date, or date passed via `--date`)

---

### 2b) Functional Requirements

#### Scope of the Work

Management of a personal daily time log: creating, loading, displaying, editing, and saving hourly time entries for a given date.

#### Business Data Model / Data Dictionary

**File:** `~/time-tracking/<YYYY-MM-DD>.json`

**Structure:** A JSON array of exactly 24 entry objects, one per hour of the day.

```json
[
  { "hour": "00:00", "project": "", "description": "" },
  { "hour": "01:00", "project": "", "description": "" },
  ...
  { "hour": "23:00", "project": "", "description": "" }
]
```

| Field | Type | Description |
|---|---|---|
| `hour` | string | Zero-padded 24h time, e.g. `"09:00"`. Fixed; not user-editable. |
| `project` | string | Project name. Empty string when unpopulated. |
| `description` | string | Free-text description of work done. Empty string when unpopulated. |

#### Scope of the Product

**In scope:**
- Creating and reading daily JSON time-tracking files
- GUI popup for editing and saving entries
- Project name suggestions sourced from historical files

**Out of scope:**
- Reporting, aggregation, visualisation, or querying of time data
- Any form of authentication or multi-user support
- Notifications or reminders (scheduling is handled externally)

---

#### List of Atomic Functional Requirements

| ID | Requirement | Fit Criterion |
|---|---|---|
| FR-01 | The script accepts an optional `--date YYYY-MM-DD` CLI argument | Running with `--date 2026-01-15` opens the file for 2026-01-15. Omitting `--date` opens today's file. |
| FR-02 | An invalid `--date` value is rejected with a clear argparse error message | Running with `--date abc` or `--date 2026-13-01` prints an error and exits without opening the GUI |
| FR-03 | If `~/time-tracking/` does not exist, it is created on launch | After first run on a clean system, the directory exists |
| FR-04 | If the target date's JSON file does not exist, it is created with 24 blank entries (`"project": ""`, `"description": ""`) before the popup opens | A new file is present and valid after first launch for a given date |
| FR-05 | If the target date's JSON file already exists, its data is loaded into the popup on open | Existing project and description values are pre-populated in the GUI fields |
| FR-06 | The popup displays a scrollable list of all 24 hourly entries (`00:00`–`23:00`) | All 24 rows are accessible by scrolling; none are hidden or omitted |
| FR-07 | On open, the popup scrolls to the row corresponding to the current hour | Opening at 14:35 results in the `14:00` row being visible without manual scrolling |
| FR-08 | Each row displays the hour label (non-editable), an editable combobox for project, and an editable free-text field for description | All three elements are present and correctly labelled in each row |
| FR-09 | All 24 entries are fully editable regardless of time of day | The user can edit the `23:00` entry at `09:00` without restriction |
| FR-10 | The project combobox is pre-populated with an alphabetically sorted list of all unique project names found in JSON files within the rolling 90-day window (including today's file if it exists) | Opening the dropdown shows all distinct project names from the last 90 days, in alphabetical order |
| FR-11 | The user can type a new project name directly into the project combobox that does not exist in the historical list | Typing a novel name and submitting saves that name as the project for that entry |
| FR-12 | The popup window scales to approximately 80% of screen height and is centred on screen | Window is visually centred and tall enough to show ~8–10 rows without scrolling |
| FR-13 | A **Submit** button saves the current state of all 24 entries to the target JSON file and closes the popup | After clicking Submit, the file on disk reflects exactly what was shown in the popup at the time of clicking |
| FR-14 | A **Cancel** button discards all changes; a confirmation dialog is shown before discarding | Clicking Cancel shows a confirmation prompt; confirming closes the popup without writing to disk |
| FR-15 | On any file read/write error, a tkinter error dialog is shown and the operation is aborted cleanly | Simulating a permission error on the target file produces a visible error dialog rather than a crash |

---

### 2c) Non-Functional Requirements

| Category | Requirement |
|---|---|
| Look & Feel | Matches `popup_msg.py` style: tkinter defaults, no custom theming or third-party widget libraries |
| Usability | All arguments self-documented via `--help`; popup is operable with keyboard and mouse |
| Performance | Scanning up to 90 JSON files on launch is acceptable; no caching required |
| Operational | Runs on Linux; invocable from cron or any shell |
| Maintainability | Single self-contained `.py` file; no build step required |
| Security | No sensitive data handling; no special security requirements |
| Legal/Compliance | None |

---

## 3) Project Issues

### 3.1 Open Issues

None.

### 3.2 Off-the-Shelf Solutions

Evaluated and rejected in favour of a lightweight custom script (no external dependencies, fits existing tooling conventions).

### 3.3 New Problems

None identified.

### 3.4 Tasks

1. Write `personal_time_tracker.py` per these requirements
2. Deploy to `/usr/local/bin/personal_time_tracker` and `chmod +x`

### 3.5 Migration / Cut-over Activities

None — no existing data to migrate.

### 3.6 Risks

| Risk | Mitigation |
|---|---|
| Two instances submit simultaneously, one overwrites the other | Accepted; last-write-wins. User is aware. |

### 3.7 Costs

None beyond developer time.

### 3.8 User Documentation and Training

Script is self-documenting via `--help`. No additional documentation required.

### 3.9 Waiting Room

- Potential future: `--date` could accept relative values (e.g. `--date yesterday`)
- Potential future: reporting/export tool operating on the same JSON format

### 3.10 Ideas for Solutions

- Use `ttk.Combobox` (from `tkinter.ttk`) for editable dropdowns — supports both selection and free-text entry natively
- Use a `tk.Canvas` with a scrollbar for the scrollable list of 24 rows

---

## 4) Naming Conventions and Definitions

### Glossary

| Term | Definition |
|---|---|
| Entry | A single hour's time log record within a daily JSON file |
| Project | A named category of work; user-defined, reusable across days |
| Daily file | The JSON file for a specific date, named `<YYYY-MM-DD>.json` |
| Rolling 90-day window | All dates from today minus 89 days up to and including today |
| Combobox | A widget combining a dropdown list with a free-text input field |

### Data Dictionary

| Field | Type | Format | Empty state | Notes |
|---|---|---|---|---|
| `hour` | string | `HH:MM` (zero-padded, 24h) | N/A — always present | Fixed values `00:00`–`23:00`; one per entry |
| `project` | string | Any UTF-8 text | `""` | User-defined; sourced from history or typed freely |
| `description` | string | Any UTF-8 text | `""` | Free-text; no length constraint defined |
