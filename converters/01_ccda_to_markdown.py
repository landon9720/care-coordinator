#!/usr/bin/env python3
"""Convert C-CDA XML documents into readable markdown, one file per encounter.

Run from the directory holding your extracted exports:
    python3 01_ccda_to_markdown.py

Expects extracted bundles laid out as  <institution>-extracted/IHE_XDM/<id>/DOC*.XML
which is what an IHE_XDM zip from a patient portal unpacks to. The institution
slug is taken from the directory name, so any number of sources work.

Writes into readable/<institution>/ as summary/ and encounters/<year>/.
Narrative text comes through verbatim. Nothing is inferred or rewritten.

Standard library only, deliberately. No install step, no dependencies.
"""
import xml.etree.ElementTree as ET, glob, re, os, collections

NS = {'h': 'urn:hl7-org:v3'}
ROOT = "readable"

# The patient-id directory inside IHE_XDM is assigned by the exporting system and
# differs for every person, so it must stay a wildcard.
PATTERN = "*-extracted/IHE_XDM/*/DOC*.XML"

FOOTER = """
## Also generated here

- **`timeline.md`** — every encounter chronologically with facility, provider and
  verbatim diagnosis text. Start here.
- **`labs.csv`** — all numeric results as a flat time series:
  `date, source, analyte, value, unit, reference_range, flag`.
- **`diagnoses.csv` / `medications.csv` / `immunizations.csv` / `procedures.csv`** —
  per-encounter lists, deduplicated across systems.

## What is and isn't here

Narrative text only, verbatim from the C-CDA source — nothing rewritten or inferred.
Clinical notes, pathology reports and radiology impressions come through as prose.
Tables render as pipe-separated lines; readable, not pretty.

**Commonly not obtainable through a patient portal:**

- **Radiology images (DICOM).** Reports usually come through; the images generally
  do not. Imaging is typically released separately by the radiology department on
  request.
- **Anything outside the shared record.** Portal exports routinely carry a notice
  that they may not contain the entire record. Absence from an export is not
  evidence that something does not exist — a HIPAA right-of-access request is the
  route to the rest.

Regenerate everything by re-running the three scripts in order.
"""


def source_of(path):
    """Institution slug from the export directory: 'riverside-extracted/...' -> 'riverside'."""
    head = path.split(os.sep)[0]
    return head[:-len("-extracted")] if head.endswith("-extracted") else head


def flat(e):
    parts=[]
    for node in e.iter():
        tag=node.tag.split('}')[-1]
        if node.text and node.text.strip(): parts.append(node.text.strip())
        if tag in ('tr','paragraph','br','item'): parts.append('\n')
        elif tag in ('td','th'): parts.append(' | ')
        if node.tail and node.tail.strip(): parts.append(node.tail.strip())
    s=' '.join(parts)
    s=re.sub(r' *\n *','\n',s); s=re.sub(r'\n{3,}','\n\n',s)
    s=re.sub(r'(\| *){2,}','| ',s); s=re.sub(r'[ \t]{2,}',' ',s)
    return s.strip()

index=collections.defaultdict(list)
for f in sorted(glob.glob(PATTERN)):
    src=source_of(f)
    try: root=ET.parse(f).getroot()
    except Exception: continue
    ti=root.find('h:title',NS)
    title=''.join(ti.itertext()).strip() if ti is not None else 'Document'
    enc=root.find('.//h:encompassingEncounter',NS)
    date=None; fac=''; prov=''
    if enc is not None:
        t=enc.find('h:effectiveTime',NS)
        v=None
        if t is not None:
            v=t.get('value') or (t.find('h:low',NS).get('value') if t.find('h:low',NS) is not None else None)
        if v: date=f"{v[:4]}-{v[4:6]}-{v[6:8]}"
        nm=enc.find('.//h:healthCareFacility//h:name',NS)
        if nm is not None: fac=' '.join(''.join(nm.itertext()).split())
        pn=enc.find('.//h:encounterParticipant//h:assignedPerson//h:name',NS)
        if pn is not None: prov=' '.join(''.join(pn.itertext()).split())
    body=[]
    for sec in root.iter('{urn:hl7-org:v3}section'):
        st=sec.find('h:title',NS); tx=sec.find('h:text',NS)
        if st is None or tx is None: continue
        t2=flat(tx)
        if t2: body.append(f"## {''.join(st.itertext()).strip()}\n\n{t2}\n")
    if date:
        d=os.path.join(ROOT,src,"encounters",date[:4]); slug=re.sub(r'[^A-Za-z0-9]+','-',fac)[:44].strip('-')
        fn=f"{date}_{slug or 'encounter'}.md"
    else:
        d=os.path.join(ROOT,src,"summary"); fn=re.sub(r'[^A-Za-z0-9]+','-',title)[:50].strip('-')+".md"
    os.makedirs(d,exist_ok=True)
    hdr=[f"# {title}",""]
    hdr.append(f"**Source:** {src.upper()}")
    if date: hdr.append(f"**Date:** {date}")
    if fac: hdr.append(f"**Facility:** {fac}")
    if prov: hdr.append(f"**Provider:** {prov}")
    hdr.append(f"**Origin:** `{f}`"); hdr.append("")
    open(os.path.join(d,fn),'w').write('\n'.join(hdr)+'\n'+'\n'.join(body))
    index[src].append((date or "—", fac or title, os.path.join(d,fn).replace(ROOT+"/","")))

lines=["# Medical records — readable index","",
       "Markdown conversions of the C-CDA bundles in `../*-extracted/`.",
       "One file per encounter, grouped by source and year. Narrative text only — no data was altered.","",
       "```","readable/"]
for src in sorted(index):
    lines.append(f"├── {src}/     summary/ + encounters/<year>/")
lines += ["```",""]
for src in sorted(index):
    rows=sorted(index[src], key=lambda r:r[0])
    lines.append(f"## {src.upper()} — {len(rows)} documents\n")
    lines.append("| Date | Facility | File |"); lines.append("|---|---|---|")
    for d,fa,p in rows: lines.append(f"| {d} | {fa[:52]} | [`{os.path.basename(p)}`]({p}) |")
    lines.append("")
lines.append(FOOTER)
os.makedirs(ROOT,exist_ok=True)
open(os.path.join(ROOT,"README.md"),'w').write('\n'.join(lines))
print("docs:", sum(len(v) for v in index.values()))
