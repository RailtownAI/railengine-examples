import { NextRequest, NextResponse } from "next/server";
import { RailEngine } from "@railtownai/railengine";

import {
  deserializeStorageBody,
  getStorageRowKeys,
  listAllStorageRows,
} from "@/lib/storage-list";

export async function DELETE(request: NextRequest) {
  try {
    const client = new RailEngine();
    const body = await request.json();
    const { id } = body;

    if (!id) {
      return NextResponse.json(
        { error: "Expense id (customer key) is required" },
        { status: 400 },
      );
    }

    const rawRows = await listAllStorageRows(client);
    const documents = rawRows.filter(
      (row): row is Record<string, unknown> =>
        row != null && typeof row === "object",
    );

    if (documents.length === 0) {
      return NextResponse.json(
        { error: "No storage documents returned for this engine" },
        { status: 404 },
      );
    }

    const documentToDelete = documents.find((doc) => {
      const { customerKey } = getStorageRowKeys(doc);
      if (customerKey === id) return true;
      const body = deserializeStorageBody(doc);
      if (body && typeof body === "object" && "id" in body) {
        return (body as { id: unknown }).id === id;
      }
      return false;
    });

    if (!documentToDelete) {
      return NextResponse.json(
        { error: "No storage row matched this expense id" },
        { status: 404 },
      );
    }

    const { eventId } = getStorageRowKeys(documentToDelete);
    if (!eventId) {
      return NextResponse.json(
        { error: "Storage row is missing EventId; cannot delete" },
        { status: 500 },
      );
    }

    await client.deleteEvent({ eventId });

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("Error in delete route:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
