import { NextResponse } from "next/server";
import { RailEngine } from "@railtownai/railengine";
import { FoodDiaryItemSchema, type FoodDiaryItem } from "@/lib/schema";

export async function GET() {
  try {
    const client = new RailEngine<FoodDiaryItem>({
      schema: FoodDiaryItemSchema,
    });
    const documents = await client.listStorageDocuments({
      pageSize: 100,
    });

    return NextResponse.json(documents, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
