#!/usr/bin/env python3
"""What has a date attached: overdue now, or coming up.

Deadlines are the easy half of this problem -- something else in the system is
usually watching them too. dormant.py handles the hard half.

The exception worth caring about is the PREP WINDOW: a thing that must happen
some number of days before an encounter. It is silently time-boxed and
unrecoverable once missed, and that property -- not importance -- is the real
test of whether something deserves an interrupt.

Usage:
  due.py           overdue plus the next 30 days
  due.py --days N  change the horizon
"""

import sys

import lib


def main(argv):
    lib.require_state()
    horizon = 30
    if "--days" in argv:
        i = argv.index("--days")
        if i + 1 < len(argv):
            try:
                horizon = int(argv[i + 1])
            except ValueError:
                lib.die("--days needs a number")

    items = lib.load_items()
    thresholds = lib.load_thresholds()
    dormant, unblocked, due, waiting_ok, quiet, closed = lib.assess(items, thresholds)

    upcoming = []
    for item in items:
        if item.get("status") in lib.CLOSED:
            continue
        left = lib.days_until(item.get("expected_by"))
        if left is not None and 0 < left <= horizon:
            item["_left"] = left
            upcoming.append(item)
    upcoming.sort(key=lambda i: i["_left"])

    prep = [i for i in upcoming if i.get("category") == "prep_window"]

    out = []

    if due:
        out.append("OVERDUE -- the date has passed")
        out.append(lib.rule())
        for item in due:
            out.append(lib.fmt_item(item, "%s late" % lib.human_days(item["_overdue"])))
        out.append("")

    if prep:
        out.append("PREP WINDOWS -- time-boxed, unrecoverable once missed")
        out.append(lib.rule())
        for item in prep:
            out.append(lib.fmt_item(item, "in %s" % lib.human_days(item["_left"])))
        out.append("")

    rest = [i for i in upcoming if i.get("category") != "prep_window"]
    if rest:
        out.append("COMING UP -- next %d days" % horizon)
        out.append(lib.rule())
        for item in rest:
            out.append(lib.fmt_item(item, "in %s" % lib.human_days(item["_left"])))
        out.append("")

    if not (due or upcoming):
        out.append("RECEIPT")
        out.append(lib.rule())
        out.append("  nothing dated is overdue or falls within %d days." % horizon)
        out.append(
            "  note: %d open items carry NO date at all. dated is not the same"
            % len([i for i in items if i.get("status") not in lib.CLOSED and not i.get("expected_by")])
        )
        out.append("  as safe -- run dormant.py for the ones nothing is watching.")
        out.append("")

    out.extend(lib.freshness_lines())
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
