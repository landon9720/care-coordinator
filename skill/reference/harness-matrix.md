# What's possible from where you are

Two things determine what you can actually do: **your AI tooling**, and **your
provider's portal**. Both vary a lot.

This file is deliberately honest about coverage. Most of the grid is unverified,
and unverified cells say so rather than being filled in from guesswork. If you
work in one of them, that report is the most useful thing you could contribute.

## The legal floor, which applies everywhere

Identical regardless of tooling or institution, and worth knowing before you ask
for anything:

| | |
|---|---|
| **HIPAA right of access** | Your records, within **30 days**. Statutory, not a courtesy. |
| **21st Century Cures Act** | Information blocking rule. Why patient API access exists, and why refusal is usually not valid. |
| **USCDI** | The standardized data set providers must be able to give you. |
| **SMART on FHIR** | The standard letting you authorize an app against your record. |

Any dormancy threshold anchored on the 30-day number is standing on law rather
than opinion. Most other thresholds are judgment.

## Harness axis

What your AI can actually touch, roughly in descending capability:

| harness | filesystem | persistent state | can run scripts |
|---|---|---|---|
| **Claude Code** | full | yes, local files | yes |
| **Claude Desktop + MCP** | via connectors | depends on setup | via MCP servers |
| **API + your own code** | whatever you build | whatever you build | yes |
| **Web chat (uploads)** | uploads only | project files at best | no |
| **Mobile only** | no | no | no |

The doctrine in `SKILL.md` assumes **none** of this. It is about what to watch
for, and it applies with a paper notebook. Capability changes how much can be
automated, not whether the approach works.

## Provider axis

What comes out of the portal, and how.

| portal / EHR | status |
|---|---|
| **Epic / MyChart** | ✅ **Verified.** Bulk export produces an IHE_XDM zip of C-CDA XML. Links expire in about a week. `converters/` was written against real exports from two separate Epic instances. |
| Oracle Health (Cerner) | ❓ Unverified |
| athenahealth | ❓ Unverified |
| eClinicalWorks / healow | ❓ Unverified |
| NextGen, Meditech, Veradigm | ❓ Unverified |
| Kaiser Permanente | ❓ Unverified |
| VA / My HealtheVet | ❓ Unverified. Blue Button is the likely path. |

❓ means nobody has reported back, not that it doesn't work.

## Verified cell

**Epic + Claude Code.** The full path works end to end: browser-assisted bulk
export, conversion to markdown and CSV with the scripts in `converters/`, local
state for tracking what's open, and coordination on top. This is the only
combination anyone has confirmed.

## Everything else, honestly

**Likely to work with little friction:** any portal exporting C-CDA XML, since the
converters key on the format rather than the institution. Any harness with
filesystem access, since nothing depends on Claude Code specifically.

**Likely to need work:** FHIR JSON bundles. No converter here handles them yet.
The output shape would be the same; the parsing is different. This is probably
the highest-value missing piece.

**Works but differently:** a harness with no filesystem. You lose automated
conversion and persistent state, and the pattern becomes: convert elsewhere or
request readable formats, upload what matters, keep the open-items list as a
document you maintain by hand and paste back in. Less convenient, and the
coordination discipline is unchanged. **The dormancy problem is not a tooling
problem.** A list on paper, checked monthly, catches the thing that has been
sitting for a year.

## Filling in a cell

If you get this working somewhere not listed, open an issue using the portal or
harness template. Describe **what the system did**, never anything about anyone's
health. See `CONTRIBUTING.md`.
