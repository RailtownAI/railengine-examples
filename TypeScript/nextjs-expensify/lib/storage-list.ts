import type { RailEngine } from "@railtownai/railengine";
import type { z } from "zod";

/**
 * Rail Engine storage list JSON may use OData-style `value`, or `results` / `items`.
 * @railtownai/railengine listStorageDocuments currently misses `value`, yielding empty lists.
 */
export function storageDocumentsFromListResponse(data: unknown): unknown[] {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  if (typeof data !== "object") return [];
  const r = data as Record<string, unknown>;
  for (const key of ["value", "results", "items"] as const) {
    const v = r[key];
    if (Array.isArray(v)) return v;
  }
  return [];
}

/** Event / customer identifiers on a storage list row (API may use PascalCase). */
export function getStorageRowKeys(doc: Record<string, unknown>): {
  customerKey: string | undefined;
  eventId: string | undefined;
} {
  const ck = doc.CustomerKey ?? doc.customerKey;
  const eid = doc.EventId ?? doc.eventId;
  return {
    customerKey: typeof ck === "string" ? ck : undefined,
    eventId: typeof eid === "string" ? eid : undefined,
  };
}

/** Deserialize storage row Body (JSON string or already-parsed object). */
export function deserializeStorageBody(item: unknown): unknown {
  if (!item || typeof item !== "object") return null;
  const r = item as Record<string, unknown>;
  const raw = r.Body ?? r.body ?? r.content ?? r.Content;
  if (raw == null) return null;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw) as unknown;
    } catch {
      return null;
    }
  }
  if (typeof raw === "object") return raw;
  return null;
}

export function totalPagesFromStorageResponse(data: unknown): number {
  if (data == null || typeof data !== "object" || Array.isArray(data)) return 1;
  const r = data as Record<string, unknown>;
  const tp = r.totalPages;
  const pc = r.pageCount;
  if (typeof tp === "number" && tp >= 1) return tp;
  if (typeof pc === "number" && pc >= 1) return pc;
  return 1;
}

type RailEngineWithRequest = RailEngine & {
  _makeRequest(
    method: string,
    path: string,
    options?: { queryParams?: Record<string, string> },
  ): Promise<Response>;
};

/** Paginated storage list using the same transport as RailEngine (PAT, base URL, engine id). */
export async function listAllStorageRows(
  client: RailEngine,
  pageSize = 100,
): Promise<unknown[]> {
  const api = client as RailEngineWithRequest;
  const engineId = client.engineId;
  const out: unknown[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const res = await api._makeRequest(
      "GET",
      `/api/Engine/${engineId}/Storage`,
      {
        queryParams: {
          PageNumber: String(page),
          PageSize: String(Math.min(pageSize, 100)),
        },
      },
    );

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`Storage list failed (${res.status}): ${text}`);
    }

    const data: unknown = await res.json().catch(() => null);
    const batch = storageDocumentsFromListResponse(data);
    out.push(...batch);

    const totalPages = totalPagesFromStorageResponse(data);
    hasMore = page < totalPages && batch.length === Math.min(pageSize, 100);
    page += 1;
  }

  return out;
}

/** Parse storage rows into T using Zod; skips invalid rows (same tolerance as SDK). */
export function mapStorageRowsToSchema<T>(
  rows: unknown[],
  schema: z.ZodSchema<T>,
): T[] {
  const result: T[] = [];
  for (const row of rows) {
    const body = deserializeStorageBody(row);
    if (body == null || typeof body !== "object") continue;
    const parsed = schema.safeParse(body);
    if (parsed.success) result.push(parsed.data);
  }
  return result;
}
