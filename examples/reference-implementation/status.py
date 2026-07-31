#!/usr/bin/env python3
"""The board. Everything open, grouped by who has the ball.

This is the most common invocation -- a human or an agent just wanting to see
where things stand. It is meant to be read directly, so it is grouped and
aligned rather than dumped.

Grouped by BALL rather than by category or urgency, because the operative
question in care coordination is not "how bad is this" but "whose move is it,
and has anyone made it".

Usage:
  status.py              everything open
  status.py --ball X     just one column of the board
  status.py --all        include closed items
"""

import sys

import lib

BALL_HEADINGS = [
    ("patient", "YOUR MOVE -- nothing happens unless you do it"),
    ("clinic", "THEIRS -- placed, awaiting them"),
    ("external", "OUTSIDE PARTY -- another institution owes something"),
    ("waiting", "LEGITIMATELY QUEUED -- has a date, not yet due"),
]


def main(argv):
    lib.require_state()
    show_all = "--all" in argv
    only_ball = None
    if "--ball" in argv:
        i = argv.index("--ball")
        if i + 1 < len(argv):
            only_ball = argv[i + 1]

    items = lib.load_items()
    thresholds = lib.load_thresholds()
    dormant, unblocked, due, waiting_ok, quiet, closed = lib.assess(items, thresholds)

    flagged = {}
    for item in dormant:
        flagged[item["id"]] = "dormant %s" % lib.human_days(item["_silent"])
    for item in due:
        flagged[item["id"]] = "OVERDUE %s" % lib.human_days(item["_overdue"])
    for item in unblocked:
        flagged[item["id"]] = "unblocked"

    active = [i for i in items if i.get("status") not in lib.CLOSED]
    out = []

    for ball, heading in BALL_HEADINGS:
        if only_ball and ball != only_ball:
            continue
        group = [i for i in active if (i.get("ball") or "") == ball]
        if not group:
            continue
        group.sort(key=lambda i: (i.get("status") == "blocked", i.get("id")))
        out.append("%s  (%d)" % (heading, len(group)))
        out.append(lib.rule())
        for item in group:
            marks = []
            if item.get("status") == "blocked":
                marks.append("blocked")
            if item["id"] in flagged:
                marks.append(flagged[item["id"]])
            if (item.get("confidence") or "") == "low":
                marks.append("low confidence")
            out.append(lib.fmt_item(item, ", ".join(marks)))
        out.append("")

    if show_all and closed:
        out.append("CLOSED  (%d)" % len(closed))
        out.append(lib.rule())
        for item in sorted(closed, key=lambda i: i.get("id")):
            out.append(lib.fmt_item(item, item.get("status", "")))
        out.append("")

    ball_counts = {}
    for item in active:
        ball_counts[item.get("ball") or "?"] = ball_counts.get(item.get("ball") or "?", 0) + 1

    out.append("SUMMARY")
    out.append(lib.rule())
    out.append(
        "  %d open  ·  %s"
        % (
            len(active),
            "  ".join("%s %d" % (b, n) for b, n in sorted(ball_counts.items())),
        )
    )
    out.append(
        "  %d dormant  ·  %d overdue  ·  %d newly actionable"
        % (len(dormant), len(due), len(unblocked))
    )
    out.append("")
    out.extend(lib.freshness_lines())

    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
