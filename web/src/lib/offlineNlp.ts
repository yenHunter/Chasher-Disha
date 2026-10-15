/**
 * lib/offlineNlp.ts
 * M7: OFFLINE-1 — Local intent lookup from bundled JSON.
 *
 * Uses cosine similarity on simple character-level bigram bags.
 * Accurate enough for the 30 common farming queries; BanglaBERT is
 * used when online.
 *
 * Sentinels (__SENTINEL__, __ASK_WEATHER__, etc.) are returned as-is
 * so the UI can route them correctly offline too.
 */

type IntentEntry = {
  intent:    string;
  examples:  string[];
  responses: string[];
};

let _intents: IntentEntry[] | null = null;

async function loadIntents(): Promise<IntentEntry[]> {
  if (_intents) return _intents;
  // Dynamic import — bundled into the JS chunk by Vite
  const mod = (await import('@/assets/offline_intents.json')) as {
    default: IntentEntry[];
  };
  _intents = mod.default;
  return _intents;
}

/** Character bigrams of a string — fast, language-agnostic. */
function bigrams(s: string): Map<string, number> {
  const map = new Map<string, number>();
  const t   = s.trim().toLowerCase();
  for (let i = 0; i < t.length - 1; i++) {
    const bg = t.slice(i, i + 2);
    map.set(bg, (map.get(bg) ?? 0) + 1);
  }
  return map;
}

function cosineSim(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0, normA = 0, normB = 0;
  a.forEach((va, k) => { dot += va * (b.get(k) ?? 0); normA += va * va; });
  b.forEach((vb) => { normB += vb * vb; });
  return normA === 0 || normB === 0 ? 0 : dot / Math.sqrt(normA * normB);
}

function randomItem<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

const FALLBACK_BN = 'দুঃখিত, এই মুহূর্তে ইন্টারনেট সংযোগ নেই। সংযুক্ত হলে আরও ভালো উত্তর দিতে পারব।';
const THRESHOLD   = 0.12;   // lower than server-side 0.60 — bigrams are sparser

/**
 * Look up the best matching intent locally.
 * Returns the response string (or sentinel string).
 */
export async function offlineLookup(query: string): Promise<string> {
  const intents = await loadIntents();
  const qBg     = bigrams(query);
  let   best    = 0;
  let   bestEntry: IntentEntry | null = null;

  for (const entry of intents) {
    for (const example of entry.examples) {
      const score = cosineSim(qBg, bigrams(example));
      if (score > best) { best = score; bestEntry = entry; }
    }
  }

  if (!bestEntry || best < THRESHOLD) return FALLBACK_BN;

  const response = randomItem(bestEntry.responses);

  // Return sentinels as-is so routing works offline
  if (response.startsWith('__')) return response;

  // Replace template tokens (date / time)
  const now  = new Date();
  const date = now.toLocaleDateString('bn-BD', { year: 'numeric', month: 'long', day: 'numeric' });
  const time = now.toLocaleTimeString('bn-BD', { hour: '2-digit', minute: '2-digit' });
  return response.replace('{current_date}', date).replace('{current_time}', time);
}
