import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";

import { ExtractedExpenseSchema } from "@/lib/schema";
import { VISION_SYSTEM_PROMPT, VISION_USER_PROMPT } from "@/lib/vision-prompt";

export const runtime = "nodejs";
export const maxDuration = 60;

const ALLOWED_MIME = ["image/jpeg", "image/png", "image/webp", "image/gif"] as const;
type AllowedMime = (typeof ALLOWED_MIME)[number];

export async function POST(request: NextRequest) {
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      { error: "ANTHROPIC_API_KEY is not set" },
      { status: 500 },
    );
  }

  try {
    const body = await request.json();
    const imageBase64: unknown = body.imageBase64;
    const mimeType: unknown = body.mimeType;

    if (typeof imageBase64 !== "string" || typeof mimeType !== "string") {
      return NextResponse.json(
        { error: "imageBase64 (string) and mimeType (string) are required" },
        { status: 400 },
      );
    }
    if (!ALLOWED_MIME.includes(mimeType as AllowedMime)) {
      return NextResponse.json(
        { error: `Unsupported mime type: ${mimeType}` },
        { status: 400 },
      );
    }

    const anthropic = new Anthropic();
    const message = await anthropic.messages.create({
      model: "claude-opus-4-7",
      max_tokens: 1024,
      system: VISION_SYSTEM_PROMPT,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "image",
              source: {
                type: "base64",
                media_type: mimeType as AllowedMime,
                data: imageBase64,
              },
            },
            { type: "text", text: VISION_USER_PROMPT },
          ],
        },
      ],
    });

    const textBlock = message.content.find((b) => b.type === "text");
    if (!textBlock || textBlock.type !== "text") {
      return NextResponse.json(
        { error: "No text response from model" },
        { status: 502 },
      );
    }

    const raw = textBlock.text
      .trim()
      .replace(/^```(?:json)?\s*/i, "")
      .replace(/\s*```$/i, "");

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return NextResponse.json(
        { error: "Model returned invalid JSON" },
        { status: 502 },
      );
    }

    const result = ExtractedExpenseSchema.safeParse(parsed);
    if (!result.success) {
      console.error("[extract] schema validation failed", result.error.issues);
      return NextResponse.json(
        { error: "Extracted data failed schema validation" },
        { status: 422 },
      );
    }

    return NextResponse.json(result.data, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
