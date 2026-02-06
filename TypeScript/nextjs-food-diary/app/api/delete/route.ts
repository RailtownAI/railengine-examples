import { NextRequest, NextResponse } from "next/server";
import { RailEngine } from "@railtownai/railengine";

export async function DELETE(request: NextRequest) {
  try {
    const client = new RailEngine();
    const body = await request.json();
    const { id } = body;

    if (!id) {
      return NextResponse.json(
        { error: "Food item id (customer key) is required" },
        { status: 400 },
      );
    }

    const documents = (await client.listStorageDocuments({
      pageSize: 100,
      raw: true,
    })) as Array<Record<string, unknown>>;

    if (documents.length === 0) {
      return NextResponse.json(
        { error: "No documents found for this customer key" },
        { status: 404 },
      );
    }

    const documentToDelete = documents.find((doc) => doc.customerKey === id);
    if (!documentToDelete) {
      return NextResponse.json(
        { error: "Document not found for this customer key" },
        { status: 404 },
      );
    }

    await client.deleteEvent({ eventId: documentToDelete.eventId as string });

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("Error in delete route:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
