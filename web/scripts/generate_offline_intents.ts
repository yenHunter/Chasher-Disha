/**
 * scripts/generate_offline_intents.ts
 * M7: OFFLINE-1
 *
 * Reads ../../intents.csv and emits src/assets/offline_intents.json.
 * Run before each build: `npx tsx scripts/generate_offline_intents.ts`
 * Or add to package.json prebuild: "prebuild": "npx tsx scripts/generate_offline_intents.ts"
 *
 * Output schema:
 * [{ "intent": string, "examples": string[], "responses": string[] }, ...]
 */

import fs   from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

const CSV_PATH  = path.resolve(__dirname, '../../intents.csv');
const OUT_DIR   = path.resolve(__dirname, '../src/assets');
const OUT_PATH  = path.join(OUT_DIR, 'offline_intents.json');

interface IntentEntry {
  intent:    string;
  examples:  string[];
  responses: string[];
}

function splitSemicolon(s: string): string[] {
  return s.split(';').map((x) => x.trim()).filter(Boolean);
}

// Minimal CSV parser: handles the semicolon-delimited multi-value fields
// wrapped in double-quotes as produced by intents.csv.
function parseCsv(raw: string): IntentEntry[] {
  const lines  = raw.replace(/\r\n/g, '\n').split('\n');
  const result: IntentEntry[] = [];

  for (let i = 1; i < lines.length; i++) {   // skip header
    const line = lines[i].trim();
    if (!line) continue;

    // Split on commas that are NOT inside double-quoted fields
    const fields: string[] = [];
    let inQuote = false;
    let current = '';
    for (const ch of line) {
      if (ch === '"') { inQuote = !inQuote; continue; }
      if (ch === ',' && !inQuote) { fields.push(current); current = ''; }
      else current += ch;
    }
    fields.push(current);

    if (fields.length < 3) continue;
    result.push({
      intent:    fields[0].trim(),
      examples:  splitSemicolon(fields[1]),
      responses: splitSemicolon(fields[2]),
    });
  }
  return result;
}

// Read, parse, write
const raw     = fs.readFileSync(CSV_PATH, 'utf-8');
const intents = parseCsv(raw);
fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(OUT_PATH, JSON.stringify(intents, null, 2), 'utf-8');
console.log(`✓ offline_intents.json — ${intents.length} intents → ${OUT_PATH}`);
