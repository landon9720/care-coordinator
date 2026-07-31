// Generate the site page content from the repository README.
//
// The README is the single source of truth. Contributors edit one file and the
// site follows, so the two can never drift. This script only transforms it for
// web display; it never rewrites the README itself.

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const README = resolve(here, '../../README.md');
const OUT = resolve(here, '../src/pages/_readme.md');
const BLOB = 'https://github.com/landon9720/care-coordinator/blob/main/';

let md = readFileSync(README, 'utf8');

// Content between these markers is repo-only and does not belong on the site,
// typically because it would be self-referential there (a link to the site
// itself) or is about working in the repository rather than about the project.
md = md.replace(/<!--\s*site:skip\s*-->[\s\S]*?<!--\s*\/site:skip\s*-->\n*/g, '');

// Drop the H1 — the page supplies its own header.
md = md.replace(/^#\s+.*\n+/, '');

// Repo-relative links would 404 on the site. Point them at GitHub instead.
// Leaves absolute URLs and in-page anchors alone.
md = md.replace(/\]\((?!https?:|#|mailto:)([^)]+)\)/g, (_m, path) => `](${BLOB}${path})`);

writeFileSync(OUT, md);

const words = md.split(/\s+/).filter(Boolean).length;
console.log(`sync-readme: ${words} words from README.md -> src/pages/_readme.md`);
