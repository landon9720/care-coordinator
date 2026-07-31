#!/usr/bin/env python3
"""What has gone quiet and should not have.

This is the core of the tool. Not deadlines -- dormancy. Most things that rot in
outpatient care have no deadline at all, which is precisely why they rot: nothing
in any system is watching elapsed time.

Its healthy output is usually nothing. That makes silence ambiguous -- a broken
detector looks exactly like a quiet week. So this never prints nothing. When
there is no alarm it prints a RECEIPT: it ran, it checked N items, the oldest
untouched thing is X days old. That is what makes "nothing today" trustworthy.

Usage:
  dormant.py            report
  dormant.py --quiet    print only if something crossed a threshold (exit 1 if so)
"""

import sys

import lib


def main(argv):
    only_alarms = "--quiet" in argv
    lib.require_state()

    items = lib.load_items()
    thresholds = lib.load_thresholds()
    dormant, unblocked, due, waiting_ok, quiet, closed = lib.assess(items, thresholds)

    active = len(items) - len(closed)
    alarms = len(dormant) + len(unblocked)

    if only_alarms and not alarms:
        return 0

    out = []

    if dormant:
        out.append("DORMANT -- open, no movement, nobody watching")
        out.append(lib.rule())
        for item in dormant:
            note = "%s silent, threshold %dd" % (
                lib.human_days(item["_silent"]),
                item["_limit"],
            )
            out.append(lib.fmt_item(item, note))
            why = lib.threshold_note(item, thresholds)
            if item.get("_ratio", 0) >= 3 and why:
                out.append("            %s" % why)
        out.append("")

    if unblocked:
        # The inverse alarm, and the more interesting one. A blocked item is
        # gated, not stalled -- its silence is expected and means nothing. What
        # matters is the moment the gate opens and nobody notices.
        out.append("NEWLY ACTIONABLE -- was blocked, blocker has cleared")
        out.append(lib.rule())
        for item in unblocked:
            out.append(lib.fmt_item(item, item.get("_reason", "")))
        out.append("")

    # --- the receipt -----------------------------------------------------
    #
    # Printed whether or not anything fired. Without it, the best case and the
    # failure mode are the same empty string.
    oldest = None
    for item in dormant + quiet:
        silent = item.get("_silent")
        if silent is not None and (oldest is None or silent > oldest):
            oldest = silent

    out.append("RECEIPT")
    out.append(lib.rule())
    out.append("  checked        %d active items (%d closed, not checked)" % (active, len(closed)))
    out.append("  dormant        %d" % len(dormant))
    out.append("  newly actionable %d" % len(unblocked))
    out.append("  overdue        %d  (see due.py)" % len(due))
    out.append("  blocked        %d  gated, silence expected" % (
        active - len(dormant) - len(quiet) - len(due) - len(waiting_ok)
    ))
    out.append("  oldest untouched item  %s" % lib.human_days(oldest))
    if not alarms:
        out.append("  nothing crossed a threshold. this ran and found nothing.")
    out.append("")
    out.extend(lib.freshness_lines())

    sys.stdout.write("\n".join(out) + "\n")
    return 1 if (only_alarms and alarms) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
