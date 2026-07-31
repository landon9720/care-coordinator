#!/usr/bin/env python3
"""Flatten every numeric lab/vital result across all bundles into one CSV.

Run from the directory holding your extracted exports:
    python3 03_labs_csv.py

Writes readable/labs.csv. Values are verbatim from the source XML.
Extend M below to give names to any remaining raw LOINC codes — and please send
additions back upstream, the map is useful to everyone.

⚠️ Units and reference ranges drift across decades. Two results with the same
nominal unit are not necessarily comparable if their reference ranges differ, and
the same measurand can appear in units differing by orders of magnitude across a
long record. Normalize before comparing or charting.

Standard library only, deliberately. No install step, no dependencies.
"""
import xml.etree.ElementTree as ET, glob, csv, os

NS = {'h': 'urn:hl7-org:v3'}
LOINC = '2.16.840.1.113883.6.1'

# The patient-id directory inside IHE_XDM is assigned by the exporting system and
# differs for every person, so it must stay a wildcard.
PATTERN = "*-extracted/IHE_XDM/*/DOC*.XML"

M = {"29463-7":"Weight","8462-4":"BP diastolic","8480-6":"BP systolic","8302-2":"Height",
"8867-4":"Heart rate","9279-1":"Respiratory rate","8310-5":"Body temperature","39156-5":"BMI",
"2345-7":"Glucose","3094-0":"BUN","2160-0":"Creatinine","2951-2":"Sodium","2823-3":"Potassium",
"2075-0":"Chloride","2028-9":"CO2","17861-6":"Calcium","2885-2":"Total protein","1751-7":"Albumin",
"1920-8":"AST","1742-6":"ALT","6768-6":"Alk phos","1975-2":"Bilirubin total","718-7":"Hemoglobin",
"4544-3":"Hematocrit","6690-2":"WBC","789-8":"RBC","777-3":"Platelets","787-2":"MCV","785-6":"MCH",
"786-4":"MCHC","788-0":"RDW","4548-4":"Hemoglobin A1c","2093-3":"Cholesterol total","2085-9":"HDL",
"2089-1":"LDL","2571-8":"Triglycerides","3016-3":"TSH","2276-4":"Ferritin","1988-5":"CRP",
"30341-2":"ESR","2532-0":"LDH","33914-3":"eGFR","2498-4":"Iron","2500-7":"TIBC"}


def source_of(path):
    """Institution slug from the export directory: 'riverside-extracted/...' -> 'riverside'."""
    head = path.split(os.sep)[0]
    return head[:-len("-extracted")] if head.endswith("-extracted") else head


def label(code):
    n = code.get('displayName')
    if n:
        return n
    for tr in code.findall('h:translation', NS):
        if tr.get('displayName'):
            return tr.get('displayName')
    c = code.get('code') or '?'
    return M.get(c, 'LOINC:' + c)

rows = []
for f in sorted(glob.glob(PATTERN)):
    src = source_of(f).upper()
    try:
        root = ET.parse(f).getroot()
    except Exception:
        continue
    for obs in root.iter('{urn:hl7-org:v3}observation'):
        code, val = obs.find('h:code', NS), obs.find('h:value', NS)
        if code is None or val is None or code.get('codeSystem') != LOINC:
            continue
        v = val.get('value')
        if v is None:
            continue
        try:
            float(v)
        except Exception:
            continue
        name = label(code)
        if 'health-related event' in name.lower():   # social-history noise, same element shape
            continue
        t = obs.find('h:effectiveTime', NS)
        raw = t.get('value')[:8] if t is not None and t.get('value') else ''
        if len(raw) != 8:
            continue
        rr = obs.find('.//h:referenceRange//h:text', NS)
        ivl = obs.find('.//h:interpretationCode', NS)
        rows.append([f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}", src, name, v, val.get('unit') or '',
                     ' '.join(''.join(rr.itertext()).split()) if rr is not None else '',
                     ivl.get('code') if ivl is not None else ''])

seen, ded = set(), []
for r in sorted(rows, key=lambda r: (r[0], r[2])):
    k = (r[0], r[2], r[3])
    if k not in seen:
        seen.add(k); ded.append(r)

os.makedirs("readable", exist_ok=True)
with open("readable/labs.csv", "w", newline='') as fh:
    w = csv.writer(fh)
    w.writerow(["date", "source", "analyte", "value", "unit", "reference_range", "flag"])
    w.writerows(ded)

if not ded:
    print("labs.csv: no numeric LOINC-coded results found — check the export layout")
    raise SystemExit(0)

unnamed = {r[2] for r in ded if r[2].startswith("LOINC:")}
print(f"labs.csv: {len(ded)} rows, {len(set(r[2] for r in ded))} analytes, "
      f"{ded[0][0]}..{ded[-1][0]} ({len(rows)-len(ded)} duplicates removed)")
print(f"unnamed LOINC codes remaining: {len(unnamed)}")
