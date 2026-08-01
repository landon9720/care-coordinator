# care-coordinator

Get your medical records out of a patient portal, convert them into text you and
an AI agent can actually read, and track what is still open.

<!-- site:skip -->
**[care.landon9720.com](https://care.landon9720.com)** —
this README as a web page.
<!-- /site:skip -->

Three parts, usable independently:

| | |
|---|---|
| `converters/` | C-CDA XML → markdown and CSV. Python 3 stdlib only, no install. |
| `skill/` | A [Claude Skill](https://docs.claude.com/en/docs/claude-code/skills) telling an agent what to track and when to speak up. |
| `examples/` | An optional reference implementation of a dormancy check. |

## What it does

1. **Get the records.** The agent drives the portal itself — navigating menus,
   requesting the export, downloading and unpacking it — with the legal backing
   to insist when a system resists.
2. **Make them readable.** C-CDA XML into markdown and CSV, so a person and a
   model can both work with them.
3. **Capture what isn't charted.** Symptoms between visits, what was said in the
   room, history predating the electronic record. Stored as a first-class source.
4. **Produce things.** Messages to clinics, records requests, amendment
   requests, appointment prep, summaries for a new provider, calendar events.
5. **Track what is open.** What was started, whose move it is, and how long it
   has been sitting.

## Why track dormancy

Most things that go wrong here are not analysis errors. A clinician orders
something, completing it needs you to call and book, you don't, and nothing
anywhere notices — because items like that carry no deadline, so no alert was
ever configured to miss.

The practical consequence for anything you build: **watch elapsed time since last
movement, not just due dates**, and treat patient-side silence as more alarming
than clinic-side silence. Clinics have recall lists and schedulers. Nobody chases
the patient. (Less true in integrated and single-payer systems with organized
recall.)

## Requirements

- **Python 3.8+** for the converters. Standard library only — no `pip install`,
  no virtualenv, no `requirements.txt`.
- **Node 22.12+** only if you want to build the website. Not needed otherwise.
- An AI agent is optional. The converters are useful on their own.

## Install the skill

```bash
git clone https://github.com/landon9720/care-coordinator.git
ln -s "$PWD/care-coordinator/skill" ~/.claude/skills/care-coordinator
```

A symlink keeps it updatable with `git pull`. Copy the directory instead if you
prefer to pin it. Verify with `/skills` in Claude Code, or just ask your agent
what is still open in your care — the skill's frontmatter triggers on phrasing
like *"did I ever get that scan"* or *"what am I forgetting"*.

The skill holds **no state**. It reads whatever files you already have, in
whatever layout. Nothing below is required by it.

## Get your records out

You are legally entitled to them:

- **HIPAA right of access** — your records within **30 days**. Statutory.
- **21st Century Cures Act** information blocking rule — why patient API access
  exists, and why "we don't do that" is usually not a valid answer.

### Epic / MyChart

The only path verified end to end.

An agent with browser control can do this whole sequence. Credentials should come
from a password manager or an already-authenticated session — never plaintext in
the conversation. Portal sessions expire in roughly 15–20 minutes, and these are
heavy SPAs where the URL often does not change between steps, so build
re-authentication into any long flow.

1. Sign in to your MyChart instance. Each health system runs its own, so you need
   a separate export from each.
2. **Menu → Document Center → Requested Records**, then request a full record.
   Some instances label it *Visit Records* or *Download My Record*.
3. Choose **all visits** or the full date range rather than a single encounter.
4. Wait. Generation is asynchronous, typically minutes to hours.
5. Download the `.zip` when it appears. **The link expires, often in about a
   week.**

⚠️ **Keep the zip.** It is your source of truth and the only durable artifact —
the download link dies, and everything else regenerates from it.

Name downloads so source and date survive, e.g. `<institution>-<YYYY-MM-DD>.zip`.
Freshness matters later and the filename is the simplest place to keep it.

### Other portals

Look for a bulk export under a records, documents, or "share my record" section.
Common outputs are C-CDA XML in a zip (what `converters/` handles) or a FHIR JSON
bundle (not yet handled). See compatibility below.

## What is in the zip

An Epic export is an **IHE_XDM** package:

```
IHE_XDM/<PatientId>/DOC0001.XML     one C-CDA document per encounter
IHE_XDM/<PatientId>/DOC0002.XML
IHE_XDM/<PatientId>/STYLE.XSL       stylesheet for browser viewing
HTML/                               a browsable viewer
INDEX.HTM
README - Open for Instructions.TXT
```

`<PatientId>` is assigned by the exporting system and differs per person, so
never hardcode it. The `DOC*.XML` files are the data; everything else is
presentation.

## Convert

Unpack each zip into a directory named `<institution>-extracted`. The converters
key off that suffix to label the source, so any number of institutions work.

```bash
mkdir -p records && cd records
unzip -q ../mercy-2026-07-28.zip    -d mercy-extracted
unzip -q ../riverside-2026-07-28.zip -d riverside-extracted

python3 ../converters/01_ccda_to_markdown.py
python3 ../converters/02_extract_tables.py
python3 ../converters/03_labs_csv.py
```

Run them **from the directory holding the `*-extracted` folders**, and in order.
Each writes into `readable/`. Expect a document count, row counts per CSV, and a
count of unmapped LOINC codes.

## What you get

```
readable/
  README.md                  index of every document, by source and date
  timeline.md                all encounters chronologically, grouped by year
  labs.csv                   every numeric result as one time series
  diagnoses.csv
  medications.csv
  immunizations.csv
  procedures.csv
  <institution>/
    summary/<Title>.md       undated documents (patient summary, continuity of care)
    encounters/<YYYY>/<YYYY-MM-DD>_<Facility>.md
```

Date-prefixed filenames under year folders make chronological sort free and
per-year globbing trivial.

**Schemas**

```
labs.csv          date, source, analyte, value, unit, reference_range, flag
diagnoses.csv     date, source, facility, text
medications.csv   date, source, facility, text
immunizations.csv date, source, facility, text
procedures.csv    date, source, facility, text
```

Each encounter file opens with `Source`, `Date`, `Facility`, `Provider`, and
`Origin` (the path of the XML it came from), then the document's sections as
headings. Narrative text is verbatim — nothing rewritten, summarized, or
inferred.

### Notes on the data

- **`03_labs_csv.py` maps 44 common LOINC codes** to readable names. Anything
  unmapped comes through as `LOINC:<code>`, and the script prints how many.
  Extend the `M` dict — and please send additions upstream.
- ⚠️ **Units and reference ranges drift across decades.** The same measurand can
  appear in units differing by orders of magnitude across a long record, and two
  values sharing a nominal unit are not comparable if their ranges differ.
  Normalize before comparing or charting.
- ⚠️ **Absence from an export is not evidence of absence.** Exports carry
  explicit incompleteness notices. Missing means *unknown*, not *no*.
- **Radiology reports** usually come through; **images (DICOM) do not**, and are
  requested separately from the radiology department.
- Exports are **dated snapshots**. Nothing refreshes on its own. Track freshness
  **per institution** — one recent export makes a stale one look current.

## Working with an agent

Point it at `readable/` and ask questions. The conversion matters more than it
looks: raw C-CDA burns enormous context on namespaces, template OIDs, and
boilerplate that carry no meaning, and that noise measurably degrades reasoning
about the parts that do.

Two rules keep regeneration safe:

1. **The zip is the source of truth.** If a derived file disagrees with it, the
   export wins.
2. **Everything in `readable/` is disposable.** Regenerate rather than edit.
   Hand-editing a derived file creates a second source of truth that silently
   diverges.

Anything you write yourself is a **source, not a derivative** — notes, symptom
history, things said in a room that never got charted. Keep it *outside*
`readable/` so a refresh cannot destroy it.

When telling an agent things:

- **Qualitative self-report is reliable** and often the most valuable input you
  have. What it feels like, what makes it worse, what order things happened in.
- **Quantitative self-report is an estimate.** Durations, dates, counts,
  severities. Remembered intervals tend to run long — anchor them to a dated
  document where one exists.
- Nothing you tell an agent changes your chart. Correcting the record is a formal
  **amendment request**, and acknowledgement is not completion — check a later
  export to confirm it landed.

## Tracking what is open

Deliberately unspecified. A markdown list you maintain by hand works. So does a
TSV. Use whatever you will actually keep current.

Four properties are enough: **what it is, whose court the ball is in, when it
last moved, and whether a date is attached.** Keep an append-only log of
movements separate from current state, since "when did this last move" is the
question everything turns on.

Keep clinical content out of it. Name the action, never the reason — *"abdominal
ultrasound ordered, never completed"*, not the indication behind it. That keeps
the file safe to paste, share, or back up.

`examples/reference-implementation/` is one worked version: TSV state, dormancy
thresholds by category, and a receipt so "nothing today" is distinguishable from
a check that silently broke. An example, not a requirement.

## Compatibility

| portal / EHR | status |
|---|---|
| **Epic / MyChart** | ✅ Verified. IHE_XDM zip of C-CDA XML. |
| Oracle Health (Cerner) | ❓ Untested |
| athenahealth | ❓ Untested |
| eClinicalWorks / healow | ❓ Untested |
| NextGen, Meditech, Veradigm | ❓ Untested |
| Kaiser Permanente | ❓ Untested |
| VA / My HealtheVet | ❓ Untested — Blue Button is the likely path |

| harness | filesystem | persistent state | runs scripts |
|---|---|---|---|
| **Claude Code** | ✅ full | ✅ local files | ✅ |
| Claude Desktop + MCP | via connectors | depends | via MCP |
| API + your own code | whatever you build | whatever you build | ✅ |
| Web chat | uploads only | project files at best | ❌ |
| Mobile | ❌ | ❌ | ❌ |

❓ means nobody has reported back, not that it fails. FHIR JSON bundles have no
converter here yet and are probably the highest-value missing piece.

## Troubleshooting

**`docs: 0`, or no CSV rows** — the converters glob
`*-extracted/IHE_XDM/*/DOC*.XML` from the current directory. Check you are in the
parent of the `*-extracted` folders and that unzipping preserved the `IHE_XDM/`
level.

**`timeline.md: no dated encounters found`** — documents parsed but none carried
an `encompassingEncounter` date. Common for summary-only exports. Per-document
markdown still generates.

**Many `LOINC:<code>` entries** — normal. Only 44 codes are mapped by name; the
rest fall back to the code and remain usable.

**Everything labeled the same source** — the slug comes from the directory name
before `-extracted`. Two exports unpacked into one directory get one label.

**Putting this in git?** Check `git config user.email` *before* the first commit.
A global gitconfig stamps your real name and address onto every commit, it is
invisible in the working tree, and it is not practically removable once pushed.
See `skill/reference/getting-started.md` §3a.

## Contributing

Pull requests welcome. Most valuable is knowledge that only appears when somebody
tries this against a real institution: the exact export path through a portal,
what format it returns, a clinic's published response window, an unmapped LOINC
code, whether something here was wrong for you.

Issue templates for portal and harness reports are provided.

> ### One absolute rule
>
> **Contributions carry information about technology and providers. They never
> carry personal health information.**
>
> Contribute how a *system* behaves. Never anything about how a *person* is.
>
> No test results, findings, diagnoses, medications, appointment dates, chart
> screenshots, exported files, or log output that passed through anyone's record.
> Not yours and not anyone else's. This applies to pull requests, issues,
> comments, commit messages, example data, and test fixtures alike.
>
> A public repository is permanent, cached, and indexed. You cannot take it back.
>
> A useful contribution almost never needs a real example anyway. *"This portal
> returns a zip of C-CDA XML and the link expires in seven days"* is the whole
> contribution, and it says nothing about any patient.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

Not affiliated with any health system, portal vendor, or EHR company. Gives no
medical advice. If a situation looks urgent, contact your clinician or seek
urgent care.
