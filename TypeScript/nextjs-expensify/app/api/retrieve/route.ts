import { NextResponse } from "next/server";
import { RailEngine } from "@railtownai/railengine";

import { ExpenseSchema, type Expense } from "@/lib/schema";
import { listAllStorageRows, mapStorageRowsToSchema } from "@/lib/storage-list";

export async function GET() {
  try {
    const client = new RailEngine<Expense>({
      schema: ExpenseSchema,
    });
    const rows = await listAllStorageRows(client);
    const documents = mapStorageRowsToSchema<Expense>(rows, ExpenseSchema);

    return NextResponse.json(documents, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
