# Starting from zero

Guidance, not a specification. Nothing here is required, and none of it is the
only way. If the person already has an arrangement that works, read it and adapt
rather than reorganizing their files around this document.

## 1. Get the records

You are entitled to them. Two legal anchors worth knowing, because they change
how a request should be phrased:

- **HIPAA right of access**: your records within **30 days**. Statutory.
- **21st Century Cures Act** information blocking rule: this is why patient API
  access exists, and why "we can't do that" is usually not a valid answer.

Most portals have a bulk export buried in a records or documents section, often
worded as requesting or downloading your record rather than exporting it. What
comes back is usually **C-CDA XML inside a zip**, sometimes a **FHIR JSON
bundle**, occasionally only PDFs.

Practical notes:

- **Download links expire**, often in about a week. The zip is the durable
  artifact. Keep it.
- **Request from every institution separately.** They do not share records, and
  they do not share identifiers.
- **An export is a dated snapshot.** Nothing refreshes on its own.
- **Absence is not evidence of absence.** Exports carry explicit incompleteness
  notices. Missing means unknown, not no.
- Imaging **reports** usually come through; the **images** (DICOM) usually do
  not, and are requested separately from the radiology department.

## 2. Make it readable

Raw interchange formats are unusable directly, for people and for models. Convert
once, then work from the result. See `converters/` in the repository.

What tends to be worth producing:

- **One file per encounter**, in markdown. Reads, greps, and diffs well.
- **A timeline** of everything in date order. This is usually the single most
  useful derived file.
- **Tables for repeated measurements.** Labs, medications, immunizations, and
  procedures are series; a CSV or TSV lets you sort and chart without parsing.
- **An index** of what documents exist and where they came from.

## 3. Organize it however makes sense

The only distinction that really matters is **source versus derived**:

- **Sources** are the original exports and anything the person wrote themselves.
  Never regenerated, never overwritten, kept safe.
- **Derived** is everything a script produced. Disposable by design. Regenerate
  it rather than editing it.

Hand-editing a derived file creates a second source of truth that will silently
diverge from the first. When a derived file and an export disagree, the export
wins.

⚠️ **Keep self-written material outside the derived tree.** If a refresh can
overwrite it, the layout is wrong. This is not obvious until the day it nearly
happens, and by then the only copy of something is gone.

One arrangement that works, offered as an example and not a rule:

```
records/
  <institution>-<YYYY-MM-DD>.zip     source of truth, kept
  <institution>-extracted/           unpacked, disposable
  readable/                          all derived, safe to delete
    timeline.md
    labs.csv  diagnoses.csv  medications.csv
    <institution>/encounters/<year>/<date>_<facility>.md
self-reported.md                     a SOURCE. outside readable/ on purpose.
```

Date-prefixing encounter files and foldering by year makes chronological sorting
free and per-year globbing trivial. Dating analysis files in the filename rather
than overwriting them means you never lose an earlier read of the same material.

Whatever the layout, **the agent should read what is there rather than imposing
this.**

## 3a. If you put any of this in version control

Version control is genuinely useful here. Records accrete, derived files get
regenerated, and being able to see what changed between two exports answers real
questions. But a repository holding medical records has failure modes worth
naming before the first commit, not after.

- ⚠️ **Private means private forever, and that is a setting someone can change.**
  If a repository holds real records, treat making it public as unrecoverable.
  Git history keeps what the working tree no longer shows, so deleting a file
  later does not remove it.
- ⚠️ **Check the commit author identity before the first commit.** A global
  `~/.gitconfig` stamps a real name and email onto every commit, and this is
  invisible in the working tree — there is nothing to notice while you work.

  ```
  git config user.name
  git config user.email
  ```

  Set a repository-local identity if the global one isn't what you want
  published. Once pushed, commit metadata is not practically removable.
- **Never commit a store that mixes tracking with clinical content.** Keeping
  the two apart is what makes the tracking file safe to share, paste, or back up
  somewhere less careful.
- **Consider whether the derived tree belongs in history at all.** It is
  regenerable by definition. Committing the source export and ignoring
  everything derived keeps the repository small and reduces how many copies of
  the same content exist.

⚠️ **The state most likely to leak is the state nobody chose to create.** Commit
authorship comes from a global config you set up years ago. Deploy tooling writes
project and organization identifiers into a dotfile as a side effect of the first
deploy. Neither is visible while you work, and both are permanent once pushed.
Ignore rules for that kind of file have to exist *before* the tool runs, not
after, because by then the file already exists and you had no reason to look for
it.

None of this argues against version control. It argues for deciding these
questions deliberately, once, at the start, when they are still cheap.

## 4. Decide what "open" means

This is where coordination starts and where most of the value is. For anything
that got started, the question is: **whose move is it, and how long has it been
their move?**

Four properties are enough: what it is, whose court the ball is in, when it last
moved, and whether a date is attached.

How that gets stored is genuinely open. A markdown list a person maintains by
hand is fine. So is a TSV, if it earns its place. Prefer whatever the person will
actually keep current, and prefer something hand-editable at 11pm over something
elegant. If a structured file starts to help, propose it then, rather than
requiring it up front.

Two things worth getting right whatever the format:

- **Keep an append-only log of movements** separately from current state. It is
  the audit trail, and "when did this last move" is the question the whole system
  turns on.
- **Keep clinical content out of it.** Name the action, never the reason. It
  keeps the working file safe to show someone, paste into a message, or back up.

## 5. Refresh deliberately

Nothing here updates itself, which is a feature. Re-export when there has been
activity, not on a schedule.

Track freshness **per institution**, never as a single number. Sources refresh
independently, and one recent export makes a stale one look current. Read the
date off the export filename and say it out loud rather than implying the data
is current.
