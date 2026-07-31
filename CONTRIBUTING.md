# Contributing

Thanks for considering it. This project gets better mainly through people trying
it against institutions and tooling the maintainers have never touched.

## The one absolute rule

**Contributions carry information about technology and providers. They never
carry personal health information.**

Contribute how a *system* behaves. Never anything about how a *person* is.

That means none of the following, in pull requests, issues, comments, commit
messages, example data, or test fixtures:

- test results, values, or reference ranges from a real record
- findings, diagnoses, conditions, symptoms, or medications
- appointment dates, dates of service, or anything that pins to a person
- screenshots of a chart, portal, or message thread containing real content
- exported files, or log output produced by running these tools on real data
- names of patients, clinicians, or the specific people involved in your care

This applies to your own information as much as anyone else's. A public
repository is permanent, cached, and indexed by search engines. There is no
size of disclosure small enough to be fine, and you cannot take it back.

**If a contribution cannot be written without describing someone's health, it is
not a contribution this project wants.** Write the mechanism instead.

### What that looks like in practice

Useful, and carries nothing personal:

> Kaiser's portal exports a FHIR JSON bundle rather than C-CDA. The download is
> under Medical Records > Download, and the link expired for me after 72 hours.

> My clinic publishes a 5 business day response window for portal messages, and
> states that sending a second message on the same thread resets the queue
> position.

> `03_labs_csv.py` produced `LOINC:2965-2` unmapped. That code is Specific
> gravity. Patch attached.

Not acceptable, even though the intent is helpful:

> Here's my labs.csv so you can see the format.

> The script mislabeled my A1c from March, here's the row.

> Screenshot of my results page showing the bug.

If you need to show output, invent it. Made-up values demonstrate a format just
as well as real ones, and there is no version of "it's only one row" that is
safe.

### If an agent is drafting for you

If you are using an AI agent to prepare a contribution, the rule above is the
agent's to enforce as well as yours. It should read its draft back specifically
hunting for your identifying detail before anything is pushed, replace any real
example with an invented one, and tell you it did.

## What is most useful

1. **How to get a full export out of a specific portal.** The exact path through
   the interface, what format comes back, how long the link lasts, what it
   contains and what it leaves out. This is the highest-value contribution and it
   is different at every institution.
2. **Published response windows.** The number and the exact wording. Business
   days versus calendar days matters, and so does any stated policy about
   follow-up messages.
3. **Harness notes.** What worked or didn't with your particular AI tooling, and
   what a setup looks like when the agent has no filesystem access.
4. **Converter fixes.** Unmapped LOINC codes, sections that don't parse, formats
   that break the assumptions in `converters/`.
5. **Corrections to the doctrine.** If a threshold in `skill/SKILL.md` was wrong
   for you, say what it should have been. They are starting points, not
   measurements.

## Ground rules for the doctrine

`skill/SKILL.md` is instructions to an AI agent, so changes there carry weight.
Two standards apply:

- **Claims must be structural or cited, not anecdotal.** "Nobody chases the
  patient" is fine, because it is arguable from how the system is built. "Items
  like this take 400 days on average" is not, unless you can cite a source. A
  generalization from one person's experience is a design assumption, and should
  be written as one.
- **Never weaken the boundary or the escalation floor.** The skill coordinates
  logistics and does not give medical advice. It also must never treat "I don't
  interpret results" as a reason to stay quiet about a situation that looks
  unsafe. Those two sections work as a pair. Changes to either need a good
  argument.

## Practical

- Standard library Python only in `converters/`. No dependencies, no install
  step, no build. It should still run untouched in five years.
- Keep `skill/SKILL.md` short. Detail goes in `skill/reference/`.
- Small pull requests are easier to accept than large ones.
- Opening an issue first is welcome but not required.

## Reporting a privacy problem

If you find personal information that made it into this repository, do not open a
public issue. Contact the maintainer privately so it can be removed and the
history rewritten. Public disclosure of the leak makes the leak worse.
