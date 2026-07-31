#!/usr/bin/env python3
"""Extract structured facts from the C-CDA bundles into flat text artifacts.

Run from the directory holding your extracted exports:
    python3 02_extract_tables.py

Writes into readable/: timeline.md, diagnoses.csv, medications.csv,
immunizations.csv, procedures.csv
Nothing is inferred or rewritten — values come verbatim from the source XML.

Standard library only, deliberately. No install step, no dependencies.
"""
import xml.etree.ElementTree as ET, glob, csv, re, os, collections

NS = {'h': 'urn:hl7-org:v3'}
OUT = "readable"

# The patient-id directory inside IHE_XDM is assigned by the exporting system and
# differs for every person, so it must stay a wildcard.
PATTERN = "*-extracted/IHE_XDM/*/DOC*.XML"


def source_of(path):
    """Institution slug from the export directory: 'riverside-extracted/...' -> 'riverside'."""
    head = path.split(os.sep)[0]
    return head[:-len("-extracted")] if head.endswith("-extracted") else head


def clean(x):
    """Flatten an element to text, keeping cell/row boundaries visible."""
    if x is None:
        return ''
    parts = []
    for node in x.iter():
        tag = node.tag.split('}')[-1]
        if node.text and node.text.strip():
            parts.append(node.text.strip())
        if tag in ('td', 'th'):
            parts.append('|')
        elif tag in ('tr', 'paragraph', 'item', 'br'):
            parts.append(' // ')
        if node.tail and node.tail.strip():
            parts.append(node.tail.strip())
    s = ' '.join(parts)
    s = re.sub(r'\s*\|\s*', ' | ', s)
    s = re.sub(r'(\s*//\s*)+', ' // ', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip(' |/')

def docs():
    for f in sorted(glob.glob(PATTERN)):
        src = source_of(f).upper()
        try:
            root = ET.parse(f).getroot()
        except Exception:
            continue
        enc = root.find('.//h:encompassingEncounter', NS)
        date, fac, prov, etype = '', '', '', ''
        if enc is not None:
            t = enc.find('h:effectiveTime', NS)
            v = None
            if t is not None:
                v = t.get('value')
                if not v and t.find('h:low', NS) is not None:
                    v = t.find('h:low', NS).get('value')
            if v and len(v) >= 8:
                date = f"{v[:4]}-{v[4:6]}-{v[6:8]}"
            fac = clean(enc.find('.//h:healthCareFacility//h:name', NS))
            prov = clean(enc.find('.//h:encounterParticipant//h:assignedPerson//h:name', NS))
            c = enc.find('h:code', NS)
            etype = (c.get('displayName') or '') if c is not None else ''
        yield f, src, root, date, fac, prov, etype

def section(root, pattern):
    """Return the narrative text of the first section whose title matches."""
    for sec in root.iter('{urn:hl7-org:v3}section'):
        ti = sec.find('h:title', NS)
        if ti is not None and re.search(pattern, clean(ti), re.I):
            return clean(sec.find('h:text', NS))
    return ''

rows_dx, rows_med, rows_imm, rows_proc, timeline = [], [], [], [], []
sources = set()

for f, src, root, date, fac, prov, etype in docs():
    sources.add(src)
    dx = section(root, r'visit diagnos|active problem')
    if date:
        timeline.append((date, src, etype or '—', fac or '—', prov or '—', dx[:300]))
    for sec_pat, bucket in ((r'^\s*Medications', rows_med),
                            (r'Immunization', rows_imm),
                            (r'^\s*Procedures', rows_proc),
                            (r'visit diagnos|active problem', rows_dx)):
        txt = section(root, sec_pat)
        if txt:
            bucket.append([date, src, fac, txt])

os.makedirs(OUT, exist_ok=True)
for name, rows in (("diagnoses.csv", rows_dx), ("medications.csv", rows_med),
                   ("immunizations.csv", rows_imm), ("procedures.csv", rows_proc)):
    seen, ded = set(), []
    for r in rows:
        k = (r[0], r[3])
        if k in seen:
            continue
        seen.add(k)
        ded.append(r)
    with open(os.path.join(OUT, name), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(["date", "source", "facility", "text"])
        w.writerows(sorted(ded, key=lambda r: r[0]))
    print(f"{name}: {len(ded)} rows")

timeline.sort()
if not timeline:
    print("timeline.md: no dated encounters found — check the export layout")
    raise SystemExit(0)
with open(os.path.join(OUT, "timeline.md"), 'w') as fh:
    fh.write("# Encounter timeline\n\n")
    fh.write(f"{len(timeline)} encounters, {timeline[0][0]} to {timeline[-1][0]}, "
             f"across {', '.join(sorted(sources))}. Generated from the C-CDA bundles; "
             "diagnosis text is verbatim.\n\n")
    year = None
    for d, src, et, fa, pr, dx in timeline:
        if d[:4] != year:
            year = d[:4]
            fh.write(f"\n## {year}\n\n")
        fh.write(f"**{d}** · {src} · {et}  \n{fa}")
        if pr and pr != '—':
            fh.write(f" · {pr}")
        fh.write("  \n")
        if dx:
            fh.write(f"<sub>{dx}</sub>  \n")
        fh.write("\n")
print(f"timeline.md: {len(timeline)} encounters")
