import type { RailEngine } from "@railtownai/railengine";

import { ExpenseSchema, type Expense, type ExpenseSearchResult } from "@/lib/schema";
import {
  deserializeStorageBody,
  storageDocumentsFromListResponse,
} from "@/lib/storage-list";

type RailEngineWithRequest = RailEngine & {
  _makeRequest(
    method: string,
    path: string,
    options?: { body?: unknown; queryParams?: Record<string, string> },
  ): Promise<Response>;
};

async function readJsonResponseOrThrow(
  res: Response,
  context: string,
): Promise<unknown> {
  const text = await res.text().catch(() => "");
  if (!res.ok) {
    const snippet = text.length > 800 ? `${text.slice(0, 800)}…` : text;
    throw new Error(
      `${context} (${res.status}): ${snippet || res.statusText || "unknown"}`,
    );
  }
  if (!text.trim()) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new Error(`${context}: invalid JSON response`);
  }
}

/** Try Body wrapper first, then a hit that is already a flat expense object. */
function expenseFromSearchHit(hit: unknown): Expense | null {
  if (hit == null || typeof hit !== "object") return null;
  const fromBody = deserializeStorageBody(hit);
  const candidates = [fromBody, hit];
  for (const c of candidates) {
    if (c != null && typeof c === "object") {
      const parsed = ExpenseSchema.safeParse(c);
      if (parsed.success) return parsed.data;
    }
  }
  return null;
}

/** Known keys for Azure AI Search / Railtown / OData rank fields. */
const SCORE_KEYS = [
  "@search.score",
  "@search.reranker_score",
  "score",
  "Score",
  "searchScore",
  "SearchScore",
  "documentScore",
  "DocumentScore",
  "rankingScore",
  "RankingScore",
  "relevanceScore",
  "RelevanceScore",
  "similarityScore",
  "SimilarityScore",
] as const;

const NESTED_SCORE_WRAPPERS = [
  "document",
  "Document",
  "item",
  "Item",
  "hit",
  "Hit",
  "result",
  "Result",
  "value",
] as const;

function coerceFiniteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value.trim());
    if (Number.isFinite(n)) {
      return n;
    }
  }
  return null;
}

function scoreFromPlainObject(obj: Record<string, unknown>): number | null {
  for (const key of SCORE_KEYS) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const n = coerceFiniteNumber(obj[key]);
      if (n != null) {
        return n;
      }
    }
  }
  for (const key of Object.keys(obj)) {
    const k = key.toLowerCase();
    if (
      k.includes("lineitem") ||
      (!k.endsWith("score") && k !== "score" && !key.includes("@search.score"))
    ) {
      continue;
    }
    const n = coerceFiniteNumber(obj[key]);
    if (n != null) {
      return n;
    }
  }
  return null;
}

/**
 * Best-effort rank from API hit: wrapper row, nested document, or JSON Body payload.
 */
function rawSearchScoreFromHit(hit: unknown): number | null {
  if (!hit || typeof hit !== "object") {
    return null;
  }
  const r = hit as Record<string, unknown>;

  let s = scoreFromPlainObject(r);
  if (s != null) {
    return s;
  }

  for (const wrap of NESTED_SCORE_WRAPPERS) {
    const inner = r[wrap];
    if (inner && typeof inner === "object") {
      s = scoreFromPlainObject(inner as Record<string, unknown>);
      if (s != null) {
        return s;
      }
    }
  }

  const bodyObj = deserializeStorageBody(hit);
  if (bodyObj && typeof bodyObj === "object") {
    s = scoreFromPlainObject(bodyObj as Record<string, unknown>);
    if (s != null) {
      return s;
    }
  }

  return null;
}

/** Vector / embedding APIs often expose distance (lower = closer) instead of score. */
const DISTANCE_KEYS = [
  "@search.vectorDistance",
  "vectorDistance",
  "VectorDistance",
  "distance",
  "Distance",
  "cosineDistance",
  "CosineDistance",
  "l2Distance",
  "L2Distance",
  "euclideanDistance",
  "EuclideanDistance",
] as const;

function distanceFromPlainObject(obj: Record<string, unknown>): number | null {
  for (const key of DISTANCE_KEYS) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const n = coerceFiniteNumber(obj[key]);
      if (n != null) return n;
    }
  }
  for (const key of Object.keys(obj)) {
    const k = key.toLowerCase();
    if (k.includes("lineitem")) continue;
    if (!k.includes("distance")) continue;
    const n = coerceFiniteNumber(obj[key]);
    if (n != null) return n;
  }
  return null;
}

function rawVectorDistanceFromHit(hit: unknown): number | null {
  if (!hit || typeof hit !== "object") return null;
  const r = hit as Record<string, unknown>;

  let d = distanceFromPlainObject(r);
  if (d != null) return d;

  for (const wrap of NESTED_SCORE_WRAPPERS) {
    const inner = r[wrap];
    if (inner && typeof inner === "object") {
      d = distanceFromPlainObject(inner as Record<string, unknown>);
      if (d != null) return d;
    }
  }

  const bodyObj = deserializeStorageBody(hit);
  if (bodyObj && typeof bodyObj === "object") {
    d = distanceFromPlainObject(bodyObj as Record<string, unknown>);
    if (d != null) return d;
  }

  return null;
}

/**
 * Similarity-style score (higher better), else distance (lower better).
 */
function vectorRankSignalFromHit(
  hit: unknown,
): { value: number; higherIsBetter: boolean } | null {
  const score = rawSearchScoreFromHit(hit);
  if (score != null) return { value: score, higherIsBetter: true };
  const dist = rawVectorDistanceFromHit(hit);
  if (dist != null) return { value: dist, higherIsBetter: false };
  return null;
}

type ScoredExpensePair = {
  expense: Expense;
  raw: number | null;
  higherIsBetter: boolean;
};

/**
 * Map raw scores to 0–100 within this result set (best hit → 100%).
 * Supports higher-is-better (e.g. similarity) and lower-is-better (e.g. distance).
 */
function addRelevancePercent(pairs: ScoredExpensePair[]): ExpenseSearchResult[] {
  const scored = pairs.filter((p): p is ScoredExpensePair & { raw: number } => p.raw != null);
  if (scored.length === 0) {
    return pairs.map(({ expense }) => ({ ...expense }));
  }

  const lowerIsBetter = scored.every((p) => p.higherIsBetter === false);

  if (!lowerIsBetter) {
    const max = Math.max(...scored.map((p) => p.raw), 1e-9);
    return pairs.map(({ expense, raw }) => {
      if (raw == null || max <= 0) return { ...expense };
      const relevancePercent = Math.min(
        100,
        Math.max(0, Math.round((raw / max) * 100)),
      );
      return { ...expense, relevancePercent };
    });
  }

  const values = scored.map((p) => p.raw);
  const min = Math.min(...values);
  const max = Math.max(...values);
  return pairs.map(({ expense, raw }) => {
    if (raw == null) return { ...expense };
    if (max - min < 1e-12) {
      return { ...expense, relevancePercent: 100 };
    }
    const relevancePercent = Math.min(
      100,
      Math.max(0, Math.round(((max - raw) / (max - min)) * 100)),
    );
    return { ...expense, relevancePercent };
  });
}

export async function searchIndexExpenses(
  client: RailEngine,
  engineId: string,
  searchText: string,
  limit: number,
): Promise<ExpenseSearchResult[]> {
  const api = client as RailEngineWithRequest;
  const res = await api._makeRequest("POST", `/api/Engine/Indexing/Search`, {
    body: {
      EngineId: engineId,
      Query: { search: searchText },
    },
  });

  const data: unknown = await readJsonResponseOrThrow(
    res,
    "Index search failed",
  );
  const hits = storageDocumentsFromListResponse(data);
  const pairs: ScoredExpensePair[] = [];
  for (const hit of hits) {
    const exp = expenseFromSearchHit(hit);
    if (!exp) continue;
    pairs.push({
      expense: exp,
      raw: rawSearchScoreFromHit(hit),
      higherIsBetter: true,
    });
    if (pairs.length >= limit) break;
  }

  return addRelevancePercent(pairs);
}

export async function searchVectorExpenses(
  client: RailEngine,
  engineId: string,
  vectorStore: string,
  searchText: string,
  limit: number,
): Promise<ExpenseSearchResult[]> {
  const api = client as RailEngineWithRequest;
  const res = await api._makeRequest(
    "POST",
    `/api/Engine/${engineId}/Embeddings/Search`,
    {
      body: {
        VectorStore: vectorStore,
        Query: searchText,
      },
    },
  );

  const data: unknown = await readJsonResponseOrThrow(
    res,
    "Vector search failed",
  );
  const hits = storageDocumentsFromListResponse(data);
  const pairs: ScoredExpensePair[] = [];
  for (const hit of hits) {
    const exp = expenseFromSearchHit(hit);
    if (!exp) continue;
    const sig = vectorRankSignalFromHit(hit);
    pairs.push({
      expense: exp,
      raw: sig?.value ?? null,
      higherIsBetter: sig?.higherIsBetter ?? true,
    });
    if (pairs.length >= limit) break;
  }

  return addRelevancePercent(pairs);
}
