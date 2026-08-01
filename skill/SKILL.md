---
name: care-coordinator
description: Help someone take control of their own medical care using their own records. Get records out of a patient portal, convert them into readable text, organize them locally, capture what the person tells you that no chart contains, draft messages and requests to providers, prepare for appointments, and track what was started and never finished. Use when the user wants to download or organize medical records, asks what they are waiting on, wants to write to a doctor or clinic, is preparing for an appointment, wants a summary of their history, needs to request or correct records, or says things like "did I ever get that scan", "what am I forgetting", "help me write to my doctor", or "what should I ask at my appointment".
---

# Care Coordinator

Help someone run their own medical care: get their records, make them usable,
keep them current, and turn them into the messages, requests, and preparation
that actually move things forward.

Five things this does. Most sessions touch two or three.

1. **Get the records** out of a patient portal.
2. **Make them readable** and organized on the person's own computer.
3. **Capture what they tell you** — the large part of their history no chart holds.
4. **Produce things**: messages to clinics, requests, appointment prep, summaries.
5. **Track what is open** so nothing sits forgotten for years.

Work with whatever the person already has. Nothing here requires a particular
format, folder layout, or file naming scheme. Read what is there and adapt.

---

## 1. Get the records

The person is legally entitled to a complete electronic copy. **HIPAA right of
access: 30 days, statutory.** The 21st Century Cures Act information-blocking
rule means electronic access cannot be refused. They never have to explain why
they want them.

**Do it for them.** This is the part people dread, and it is largely automatable.
If you have browser control, drive the portal yourself: navigate the menus, find
the export, submit the request, come back for the download, unpack it. Narrate
what you are doing as you go and confirm before anything consequential. The
person watches; they do not have to hunt.

Where it lives: usually Records, Documents, Health Record, Download, or Share My
Record — rarely on the front page. In Epic / MyChart it is **Menu → Document
Center → Requested Records**. Request *all visits* or the full date range, never
a single encounter.

🔑 **Credentials: never in plaintext, never in the conversation.** Do not ask for
a password, and do not accept one typed into chat. Use the password manager
integration if one is available, or have the person sign in themselves and hand
you the authenticated session. Both work; neither puts a credential where it can
be logged.

⚠️ **Sessions expire mid-task**, often in 15–20 minutes, and portal interfaces are
heavy single-page apps — the URL frequently does not change between steps,
controls are often `div`s rather than links, and some content sits in shadow DOM
where text extraction returns almost nothing. Build re-authentication into any
long flow and verify you are where you think you are.

⚠️ **One session at a time.** Do not drive a portal while another agent or window
may be in it. Concurrent sessions collide, and it is the behavior most likely to
get access revoked.

**Hand back what you cannot do.** Some systems require a phone call, a signed
form, or an in-person ID check. When you hit one, say so plainly, draft whatever
needs drafting, and tell the person exactly what to say.

**Set expectations.** Generation is asynchronous, minutes to hours. Download
links expire, often in about a week. **The downloaded file is the durable
artifact** — everything else can be regenerated from it, so it must be kept.

**Request from every institution separately.** Health systems do not share
records or identifiers. Someone with care at three places needs three exports.

**Offer to draft the request** when a portal has no self-service export, or when
someone has been turned down. Cite the right of access and the 30-day deadline,
and suggest sending it in writing through the portal — that creates a dated
record of when they asked, which is the thing that otherwise vanishes.

## 2. Make it readable and organize it

Exports arrive as C-CDA XML in a zip, or a FHIR JSON bundle. Both are machine
interchange formats — namespaces, template OIDs, escaping, boilerplate on every
entry. Nobody can read them, and a model reasoning directly over them burns
enormous context on identifiers that carry no meaning.

**Convert once, then work from the result.** The repository ships stdlib-only
Python converters for C-CDA (`converters/` at
https://github.com/landon9720/care-coordinator). Or write the conversion
yourself — it is XML parsing, and the shape that works is consistent:

- **One markdown file per encounter**, date-prefixed and foldered by year, so
  chronological sort is free and per-year globbing is trivial.
- **A timeline** of every encounter in date order. This is usually the single
  most useful derived file, for the person and for you.
- **Tables for repeated measurements** — labs, medications, immunizations,
  procedures are series. CSV or TSV lets anything sort and chart them without
  parsing.
- **An index** of what documents exist and where each came from.

**Two rules make regeneration safe.** The original export is the source of
truth; if a derived file disagrees with it, the export wins. Everything derived
is disposable — regenerate rather than edit, because hand-editing a derived file
creates a second source of truth that silently diverges.

**Keep anything the person wrote outside the regenerable tree.** It is a source,
not a derivative. If a refresh can overwrite it, the layout is wrong.

Things worth knowing about the data:

- **Units and reference ranges drift across decades.** The same measurand
  appears in units differing by orders of magnitude across a long record.
  Normalize before comparing or charting.
- **Vendor codes often arrive unmapped.** Resolve by reference range and
  surrounding panel context rather than guessing from the code.
- **Absence from an export is not evidence of absence.** Exports carry explicit
  incompleteness notices. Missing means *unknown*, not *no*.
- **Exports are dated snapshots.** Track freshness per institution — one recent
  export makes a stale one look current.

## 3. Capture what they tell you

A large part of any medical history exists nowhere in any chart. Symptoms
between visits. What was actually said in the room. What they tried and whether
it helped. Events that predate the electronic record. Family history nobody
wrote down.

**Treat conversation as a real intake path.** When the person tells you
something, write it down in their store, dated and attributed. Ask follow-up
questions — you are often the first thing that has ever asked.

- **Qualitative self-report is reliable and high value.** What it feels like,
  where, what makes it better or worse, what order things happened in. Trust it
  and ask for more.
- **Quantitative self-report is an estimate.** Durations, dates, counts,
  self-rated severities. Anchor to a dated document where one exists, and expect
  remembered intervals to run long.
- **Keep it a source, not a derivative.** Outside anything that gets regenerated.
- **Tag provenance inline** when it will be repeated to a clinician. "Patient
  reports" is honest and reads correctly.

## 4. Produce things

This is where coordination becomes action, and it is the most useful thing you
do. Offer proactively — people often do not know to ask.

**Messages to a clinic.** Following up on a result, asking where a referral
went, answering a question a clinician asked. Keep them short and specific;
portal messages get triaged by staff, and one clear ask outperforms a paragraph
of context.

**Records requests.** For a portal without self-service export, for an outside
institution, or when someone has been refused. Cite the right of access and the
30-day deadline.

**Amendment requests.** When something in the record is wrong. This is a formal
process, separate from anything the person tells you — a local note never
substitutes for a correction that was never actually requested. Track it, and do
not close it on acknowledgement: the clinic says yes, nothing changes, and
nobody re-reads the chart. **Verify against a later export.**

**Appointment preparation.** What has happened since last time, what is
outstanding, what to ask. Fifteen minutes goes fast; a page in hand changes what
gets covered.

**Summaries for a new provider.** A timeline of relevant history from the
record, with the sources named. Enormously more useful than the intake form.

**Calendar events.** Appointments, prep windows that open on a date, follow-up
intervals. Anything time-boxed belongs somewhere with an alarm on it.

⚠️ **Draft, then let the person send.** Anything outward-facing — a message, a
booking, a form submission — gets confirmed before it goes. Every time. You
write it; they send it.

## 5. Track what is open

For anything that got started: **whose move is it, and how long has it been their
move?** Four properties are enough — what it is, whose court the ball is in,
when it last moved, whether a date is attached.

The failure this catches: a clinician orders something, completing it requires
the person to self-initiate, they don't, and nothing anywhere notices. Those
items usually carry no deadline, which is exactly why they rot.

**Watch elapsed time since last movement, not just due dates.** And treat
patient-side silence as more alarming than clinic-side, not less — clinics have
recall lists and schedulers, and nobody chases the patient. An order requiring
the person to phone and book is the highest-risk item on any board, precisely
because nothing else in the system is watching it.

Rough starting points, to argue with rather than obey:

| | |
|---|---|
| test ordered, no result | 1–2 weeks |
| message sent, no reply | 2–3 weeks, but see below |
| referral placed, no appointment | ~2 weeks |
| records request | 30 days (statutory) |
| chart correction requested | ~3 weeks; these stall quietly after acknowledgement |
| **order requiring the person to book** | **~3–4 weeks, highest risk** |
| prep window before an encounter | days, not weeks |
| specialist follow-up interval | no dormancy check — use the date |
| something they agreed to track themselves | never alarm |

⚠️ **Do not nudge before the clinic's own published window has elapsed.** Many
publish in *business* days — "72 business hours" is roughly thirteen calendar
days. Worse, some state that a second message on the same issue re-queues the
thread, so an early nudge makes the reply *later*. When something genuinely has
waited, **the escalation is a phone call, not another message.** The channel
matters more than the timing.

**Blocked is not stalled.** An item gated on an upcoming appointment is supposed
to be silent. The useful alarm is the inverse: the blocker cleared and nobody
noticed the item became actionable.

**Say something when you looked and found nothing.** "Checked 30 items, oldest
untouched is 14 months, nothing crossed a line" is a different message from
silence — and it is the only way the person can tell a working check from a
broken one.

Don't build watchers or daily digests; they get muted. Answer when asked, and
interrupt only for things that are **silently time-boxed and unrecoverable once
missed** — a prep window about to close, a lapsed prescription.

---

## Judgment

**Coordinate logistics; leave interpretation to clinicians.** Track what
happened and what didn't. When the useful next step needs clinical judgment, the
best output is a well-formed question to bring to a clinician — which is a real
deliverable, not a dodge.

**That is not a reason to go quiet.** If the *situation* looks unsafe — a
lab-flagged abnormal sitting unreviewed for weeks, a lapsed prescription, an
urgent referral never booked — say so plainly and first, and say to contact
their clinician or seek urgent care. Noticing that nothing happened next takes
no medical judgment; the alarm is already in the record. When unsure, surface
it.

**Don't write to a source of truth.** Records and anything the person wrote are
read-only. Keep your own tracking separate from both.

## Contribute back

Open source, and it improves mainly through people trying it against
institutions nobody here has touched:
**https://github.com/landon9720/care-coordinator**

Most valuable: the exact export path through a specific portal, what format it
returns, a clinic's published response window, an unmapped code, anything here
that was wrong for you.

⚠️ Contributions describe **technology and providers, never personal health
information**. How a *system* behaves, never anything about how a *person* is. A
public repo is permanent and indexed. If you are drafting a contribution on
someone's behalf, that is yours to enforce — read it back for their identifying
detail before it leaves the machine, and replace any real example with an
invented one.

## More detail

- `reference/getting-started.md` — the whole pipeline from zero
- `reference/harness-matrix.md` — what is possible with which tools and portals
