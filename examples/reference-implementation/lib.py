"""Shared helpers for care-coordinator.

Python 3 standard library only, deliberately. No requirements.txt, no venv, no
install step. This should still run untouched in five years. Please keep it that
way -- the value of this tool is that it is boring and does not rot.

State lives OUTSIDE this skill directory. The skill is code and is shareable;
the state is personal and is not. See reference/state-format.md.
"""

import csv
import os
import re
import sys
from datetime import date, datetime

# ---------------------------------------------------------------- locations

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ITEM_FIELDS = [
    "id",
    "title",
    "category",
    "ball",
    "status",
    "opened_date",
    "last_movement_date",
    "expected_by",
    "institution",
    "channel",
    "provenance",
    "confidence",
    "notes_ref",
    "next_check_date",
    "blocked_by",
]

MOVEMENT_FIELDS = ["item_id", "date", "actor", "ball_after", "note"]

BALLS = ("patient", "clinic", "external", "waiting")
STATUSES = ("open", "in_progress", "blocked", "done", "abandoned")
# Items in these statuses are finished; nothing about them can go dormant.
CLOSED = ("done", "abandoned")


def state_dir():
    """Where the personal state lives. Never inside the skill directory.

    Set CARE_COORDINATOR_STATE to point at it. The default is deliberately
    generic so this skill carries no one's private paths.
    """
    d = os.environ.get("CARE_COORDINATOR_STATE") or os.path.expanduser(
        "~/.care-coordinator"
    )
    return os.path.abspath(os.path.expanduser(d))


def state_path(name):
    return os.path.join(state_dir(), name)


def require_state():
    """Fail loudly and usefully rather than pretending an empty board is a clean one."""
    d = state_dir()
    if not os.path.isdir(d):
        die(
            "No state directory at %s\n"
            "Set CARE_COORDINATOR_STATE to your coordinator directory, or run:\n"
            "  python3 %s/scripts/init_state.py" % (d, SKILL_DIR)
        )
    return d


def die(msg, code=2):
    sys.stderr.write("care-coordinator: %s\n" % msg)
    raise SystemExit(code)


# ---------------------------------------------------------------------- tsv
#
# TSV, not CSV: task and clinical text is full of commas, and quoting is exactly
# where hand-editing breaks at 11pm. Hard rule -- no tabs inside a field, ever.
# That keeps these files awk-able, grep-able, spreadsheet-openable, and
# survivable by a human with vim.


def read_tsv(path, fields=None):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for raw in reader:
            row = {(k or ""): (v if v is not None else "") for k, v in raw.items()}
            if fields:
                # Forward compatible: a file written before a column existed
                # simply reads that column as empty.
                for f in fields:
                    row.setdefault(f, "")
            rows.append(row)
    return rows


def write_tsv(path, rows, fields):
    for row in rows:
        for key, val in row.items():
            if "\t" in str(val):
                die("tab character in field %r of row %r" % (key, row.get("id", "?")))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=fields, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({f: row.get(f, "") for f in fields})
    os.replace(tmp, path)


def load_items():
    return read_tsv(state_path("open-items.tsv"), ITEM_FIELDS)


def load_movements():
    return read_tsv(state_path("movements.tsv"), MOVEMENT_FIELDS)


def save_items(rows):
    write_tsv(state_path("open-items.tsv"), rows, ITEM_FIELDS)


def append_movement(item_id, actor, ball_after, note, when=None):
    """movements.tsv is append-only. It is the audit trail; never rewrite it."""
    path = state_path("movements.tsv")
    new = not os.path.exists(path)
    if "\t" in note or "\t" in actor:
        die("tab character in movement for %s" % item_id)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=MOVEMENT_FIELDS, delimiter="\t", extrasaction="ignore"
        )
        if new:
            writer.writeheader()
        writer.writerow(
            {
                "item_id": item_id,
                "date": (when or today()).isoformat(),
                "actor": actor,
                "ball_after": ball_after,
                "note": note,
            }
        )


# --------------------------------------------------------------------- time


def today():
    return date.today()


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def days_since(s, ref=None):
    d = parse_date(s)
    if d is None:
        return None
    return ((ref or today()) - d).days


def days_until(s, ref=None):
    d = parse_date(s)
    if d is None:
        return None
    return (d - (ref or today())).days


def human_days(n):
    if n is None:
        return "unknown"
    if n < 0:
        return "in %dd" % abs(n)
    if n < 90:
        return "%dd" % n
    if n < 730:
        return "%dmo" % round(n / 30.44)
    return "%.1fyr" % (n / 365.25)


# --------------------------------------------------------------- thresholds
#
# Thresholds are DATA, not code, so they can be argued with and tuned without
# touching logic. Ship defaults here; a thresholds.tsv in the state directory
# overrides them per-person.


def load_thresholds():
    rows = read_tsv(os.path.join(SKILL_DIR, "data", "thresholds.tsv"))
    override = read_tsv(state_path("thresholds.tsv"))
    table = {}
    for row in rows + override:
        cat = (row.get("category") or "").strip()
        if not cat:
            continue
        table[cat] = row
    return table


def threshold_for(item, thresholds):
    """Days of silence before this item is considered dormant.

    The asymmetry that matters: thresholds are TIGHTER when the ball is with the
    patient, not looser. Clinics chase their own queues at least sometimes --
    recalls, schedulers, reminder calls. Nobody chases the patient. A naive
    implementation gets this backwards and lets patient-side items rot for years.
    """
    row = thresholds.get(item.get("category") or "other") or thresholds.get("other")
    if not row:
        return 30
    key = "patient_days" if item.get("ball") == "patient" else "other_days"
    try:
        return int(row.get(key) or row.get("other_days") or 30)
    except ValueError:
        return 30


def threshold_note(item, thresholds):
    row = thresholds.get(item.get("category") or "other") or {}
    return (row.get("note") or "").strip()


# ---------------------------------------------------------------- dormancy


def blocker_resolved(item, by_id):
    """A blocker is an item id that is now closed, or a date that has passed.

    Returns None when the item is not blocked or the blocker is still active.
    """
    ref = (item.get("blocked_by") or "").strip()
    if not ref:
        return None
    when = parse_date(ref)
    if when is not None:
        return "blocker date %s passed" % ref if when <= today() else None
    other = by_id.get(ref)
    if other and other.get("status") in CLOSED:
        return "blocker %s is %s" % (ref, other.get("status"))
    return None


def assess(items, thresholds, ref=None):
    """Classify every item. One pass, so every consumer agrees on the verdict.

    Returns (dormant, unblocked, due, waiting_ok, quiet, closed).
    """
    ref = ref or today()
    by_id = {i.get("id"): i for i in items}
    dormant, unblocked, due, waiting_ok, quiet, closed = [], [], [], [], [], []

    for item in items:
        status = item.get("status") or "open"
        if status in CLOSED:
            closed.append(item)
            continue

        # A blocked item is gated on something else, not stalled. Silence is
        # expected and is not a signal. The useful alarm is the opposite one:
        # the blocker cleared and nobody noticed the item is now actionable.
        if status == "blocked":
            why = blocker_resolved(item, by_id)
            if why:
                item["_reason"] = why
                unblocked.append(item)
            continue

        overdue = days_until(item.get("expected_by"), ref)
        if overdue is not None and overdue <= 0:
            item["_overdue"] = abs(overdue)
            due.append(item)
            continue

        # ball=waiting means legitimately queued somewhere with a date attached.
        # It is not dormant until that date passes -- which the branch above
        # already caught.
        if item.get("ball") == "waiting" and item.get("expected_by"):
            waiting_ok.append(item)
            continue

        silent = days_since(item.get("last_movement_date"), ref)
        if silent is None:
            silent = days_since(item.get("opened_date"), ref)
        limit = threshold_for(item, thresholds)
        if silent is not None and silent > limit:
            item["_silent"] = silent
            item["_limit"] = limit
            # How far past the line, proportionally. An item 10x past its
            # threshold is a different animal from one a day over.
            item["_ratio"] = silent / float(limit) if limit else 0.0
            dormant.append(item)
        else:
            item["_silent"] = silent
            quiet.append(item)

    dormant.sort(key=lambda i: i.get("_ratio", 0), reverse=True)
    due.sort(key=lambda i: i.get("_overdue", 0), reverse=True)
    return dormant, unblocked, due, waiting_ok, quiet, closed


# ------------------------------------------------------------- corpus dates


ZIP_DATE = re.compile(r"-all-visit-records-(\d{4}-\d{2}-\d{2})\.zip$")


def snapshot_ages():
    """Age of each record export, PER INSTITUTION.

    Never report a global max. Two institutions refresh independently and one
    can be six months stale while the newest makes the whole corpus look fresh
    -- which hides exactly the staleness worth knowing about.

    Returns [] when CARE_COORDINATOR_RECORDS is unset; freshness is then simply
    unknown, and callers say so rather than implying currency.
    """
    root = os.environ.get("CARE_COORDINATOR_RECORDS")
    if not root:
        return []
    root = os.path.abspath(os.path.expanduser(root))
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        m = ZIP_DATE.search(name)
        if not m:
            continue
        inst = name[: m.start()] or name
        out.append({"institution": inst, "date": m.group(1), "age": days_since(m.group(1))})
    return out


def freshness_lines(warn=90, fail=180):
    """Human-readable freshness, loudest when stale.

    Thresholds are a starting point, not a rule: a quiet year needs less
    refreshing than an active month. The output says so.
    """
    ages = snapshot_ages()
    if not ages:
        return ["corpus freshness unknown (CARE_COORDINATOR_RECORDS not set)"]
    lines = []
    for a in ages:
        mark = "  "
        if a["age"] is None:
            mark = "??"
        elif a["age"] > fail:
            mark = "!!"
        elif a["age"] > warn:
            mark = " !"
        lines.append(
            "%s %-12s exported %s (%s ago)"
            % (mark, a["institution"], a["date"], human_days(a["age"]))
        )
    return lines


# ------------------------------------------------------------------ display


def rule(char="-", width=72):
    return char * width


def fmt_item(item, extra=""):
    return "  %-9s %-11s %-8s %s%s" % (
        item.get("id", "?"),
        (item.get("category") or "")[:11],
        (item.get("ball") or "")[:8],
        (item.get("title") or "").strip(),
        (" [%s]" % extra) if extra else "",
    )
