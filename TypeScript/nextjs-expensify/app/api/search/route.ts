import { NextRequest, NextResponse } from "next/server";
import { RailEngine } from "@railtownai/railengine";
import { z } from "zod";

import {
  searchIndexExpenses,
  searchVectorExpenses,
} from "@/lib/engine-search";
import { ExpenseSchema, type Expense, type ExpenseSearchResult } from "@/lib/schema";

/** Cap results to bound latency / cost from search APIs. */
const MAX_RESULTS = 40;

const SearchBodySchema = z.object({
  q: z
    .string()
    .max(2000)
    .transform((s) => s.trim())
    .pipe(z.string().min(1, "Query required")),
  mode: z.enum(["index", "vector"]),
});

/**
 * Index/vector search uses a raw request + Body deserialization compatible with
 * object or string payloads. The stock SDK iterators skip non-string bodies and
 * often yield zero rows for real API responses.
 */

export async function POST(request: NextRequest) {
  try {
    const json: unknown = await request.json().catch(() => null);
    const parsedBody = SearchBodySchema.safeParse(json);
    if (!parsedBody.success) {
      return NextResponse.json(
        { error: "Invalid body", details: parsedBody.error.issues },
        { status: 400 },
      );
    }

    const q = parsedBody.data.q;
    const client = new RailEngine<Expense>({
      schema: ExpenseSchema,
    });
    const engineId = client.engineId;

    let results: ExpenseSearchResult[];

    if (parsedBody.data.mode === "index") {
      results = await searchIndexExpenses(client, engineId, q, MAX_RESULTS);
    } else {
      results = await searchVectorExpenses(
        client,
        engineId,
        "VectorStore1",
        q,
        MAX_RESULTS,
      );
    }

    return NextResponse.json({ results }, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Search failed" },
      { status: 500 },
    );
  }
}
