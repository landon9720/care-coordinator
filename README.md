# care-coordinator

Tools and doctrine for using an AI agent to get your medical records out of a
patient portal, make them readable, keep track of what is actually open, and
coordinate your own care.

<!-- site:skip -->
**[care-coordinator-nine.vercel.app](https://care-coordinator-nine.vercel.app)** — the same
content as this README, as a web page.
<!-- /site:skip -->


This is not a medical app and it gives no medical advice. It handles logistics:
what was started, whose move it is, and what has been sitting untouched.

## The problem it exists for

A clinician orders something. Completing it requires you to call and book it, or
to follow up, or to send something in. You don't. Nobody notices.

That failure is structural rather than anyone's fault. Items like that usually
have no deadline attached, so nothing in any system is watching them. There is no
alert to miss because no alert was ever configured. Clinics have machinery that
chases their own queues, at least sometimes: recall lists, schedulers, reminder
calls. Nobody chases the patient.

That is a description of fee-for-service outpatient care, which is where this was
built. Integrated and single-payer systems with organized recall do chase patients
for some overdue items, so the asymmetry is weaker there. Reports from those
systems are welcome.

So the working assumption behind everything here is that silence should worry you
*more* when the ball is in your court, not less. An order that requires you to
phone and book something is the highest-risk item on the board precisely because
it has the least structure around it.

## What's in here

**`skill/`** is a [Claude Skill](https://docs.claude.com/en/docs/claude-code/skills).
It is doctrine rather than machinery: it tells an agent what to track, what to
watch for, when to speak up, and where the boundaries are. It does not require
your files to be in any particular format or place. Install it and your agent
works with whatever you already have.

**`converters/`** turns raw portal exports into text you and your agent can
actually read. Three Python scripts, standard library only, no install step.

**`examples/`** holds a reference implementation of a dormancy tracker, for
anyone who wants that shape. It is one way to do it, not the way.

## Getting your records out

You are legally entitled to them. Two things worth knowing:

- **HIPAA right of access** gives you your records within 30 days. This is a
  statutory deadline, not a courtesy.
- **The 21st Century Cures Act** information blocking rule is why patient API
  access exists at all, and why "we don't do that" is usually not a valid answer.

Most portals offer a bulk export somewhere in a records or document section. What
comes back is typically a zip of C-CDA XML, sometimes a FHIR JSON bundle. Download
links often expire in about a week, so keep the zip. It is your source of truth.

One thing to internalize early: **an export is a dated snapshot, and absence from
it is not evidence of absence.** Exports carry explicit incompleteness notices.
If something isn't there, that means unknown, not no.

## Make it readable

Raw C-CDA and FHIR are machine interchange formats. They are dense with
namespaces, template identifiers, escaping, and boilerplate repeated on every
entry. Converting that to plain text is not a preprocessing chore, it is one of
the main things this system does for you.

For a human it is the difference between an unreadable file and your own medical
history. For a language model the gain is bigger and less obvious: raw XML burns
enormous context on identifiers that carry no meaning, and that noise measurably
degrades reasoning about the parts that do. The reduction is roughly an order of
magnitude in both cases.

```
python3 converters/01_ccda_to_markdown.py   # one markdown file per encounter
python3 converters/02_extract_tables.py     # timeline + diagnoses/meds/immunizations/procedures
python3 converters/03_labs_csv.py           # every numeric result as one time series
```

Run them from the directory holding your extracted exports. Two rules make this
safe to redo: the original export is the source of truth, and everything derived
is disposable. Regenerate derived files rather than editing them, or you create a
second source of truth that will quietly diverge.

Anything you wrote yourself is a *source*, not a derivative. Keep it outside the
tree that gets regenerated so a refresh cannot destroy it.

## Telling your agent things

A large part of what makes a local aggregate worth having is that you can just
talk to it. Symptoms between visits, what was actually said in the room, what you
tried and whether it helped, something that happened before the electronic record
existed. Much of that exists nowhere else, because the chart only holds what
somebody typed during an appointment.

Two things about self-report that are worth knowing up front:

- **Qualitative self-report is reliable and valuable.** What something feels like,
  what makes it worse, what order things happened in.
- **Quantitative self-report should be treated as an estimate.** Durations, dates,
  counts, severities. Remembered intervals tend to run long. Anchor them to a
  dated document where one exists.

Nothing you tell your agent changes your chart. If something in the record is
wrong, fixing it is a formal amendment request to the provider, and it needs to be
tracked like any other open item. Acknowledgement is not completion, so check a
later export to confirm the change actually landed.

## Which parts of this work for you

What is possible depends on two things: your AI tooling, and your provider's
portal. Those vary a lot, and this project is honest about only having verified a
corner of the space.

**Verified:** Epic / MyChart bulk export, converted and coordinated with Claude
Code (filesystem access, scripts, persistent local state).

**Unverified but expected to work:** the doctrine in `skill/` assumes nothing
about storage or tooling, so it should apply to any agent with any layout. The
converters need C-CDA XML, so they should work with any portal that exports it.

**Not yet covered:** Oracle Health, athenahealth, eClinicalWorks, Kaiser,
VA / Blue Button, and FHIR JSON bundles generally. Also every harness that isn't
Claude Code: web chat, Claude Desktop with MCP, mobile, API.

If you get this working somewhere not listed, that's the most useful thing you
could send back.

## Contributing

Pull requests welcome. What helps most is knowledge that only shows up when
somebody actually tries this against a real institution: how to get an export out
of a specific portal, what format it returns, what a clinic's published response
window is, whether something here was wrong for you.

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
> A useful contribution almost never needs a real example anyway. "This portal
> returns a zip of C-CDA XML and the link expires in seven days" is the whole
> contribution, and it says nothing about any patient.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT. See [LICENSE](LICENSE).

This project is not affiliated with any health system, portal vendor, or
electronic health record company. It gives no medical advice. If a situation
looks urgent, contact your clinician or seek urgent care.
