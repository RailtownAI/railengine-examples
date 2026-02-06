import { NextRequest, NextResponse } from "next/server";
import { RailEngineIngest } from "@railtownai/railengine-ingest";
import { z } from "zod";
import { v4 as uuidv4 } from "uuid";
import { FoodDiaryItemSchema, type FoodDiaryItem } from "@/lib/schema";

export async function POST(request: NextRequest) {
  try {
    const client = new RailEngineIngest<FoodDiaryItem>({
      schema: FoodDiaryItemSchema,
    });
    const body = await request.json();
    // Auto-generate UUID for id field
    const dataWithId = {
      ...body,
      id: uuidv4(),
    };
    const validatedData = FoodDiaryItemSchema.parse(dataWithId);

    const response = await client.upsert(validatedData);

    await new Promise((resolve) => setTimeout(resolve, 2000));

    return NextResponse.json({ success: true, status: response.status }, { status: 200 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Validation error", details: error.issues },
        { status: 400 },
      );
    }

    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
