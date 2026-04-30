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

  const data: unknown = await res.json().catch(() => null);
  const hits = storageDocumentsFromListResponse(data);
  const pairs: Array<{ expense: Expense; rawScore: number | null }> = [];
  for (const hit of hits) {
    const exp = expenseFromSearchHit(hit);
    if (!exp) continue;
    pairs.push({ expense: exp, rawScore: rawSearchScoreFromHit(hit) });
    if (pairs.length >= limit) break;
  }

  const finiteScores = pairs
    .map((p) => p.rawScore)
    .filter((x): x is number => x != null);
  const maxScore =
    finiteScores.length > 0 ? Math.max(...finiteScores, 1e-9) : 0;

  return pairs.map(({ expense, rawScore }) => {
    if (rawScore == null || maxScore <= 0) {
      return { ...expense };
    }
    const relevancePercent = Math.min(
      100,
      Math.max(0, Math.round((rawScore / maxScore) * 100)),
    );
    return { ...expense, relevancePercent };
  });
}

export async function searchVectorExpenses(
  client: RailEngine,
  engineId: string,
  vectorStore: string,
  searchText: string,
  limit: number,
): Promise<Expense[]> {
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

  const data: unknown = await res.json().catch(() => null);
  const hits = storageDocumentsFromListResponse(data);
  const out: Expense[] = [];
  for (const hit of hits) {
    const exp = expenseFromSearchHit(hit);
    if (exp) {
      out.push(exp);
      if (out.length >= limit) break;
    }
  }

  return out;
}
