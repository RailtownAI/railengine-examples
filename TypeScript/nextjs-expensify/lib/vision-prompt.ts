import { CATEGORIES } from "@/lib/schema";

export const VISION_SYSTEM_PROMPT =
  "You are a receipt OCR engine. You read images of receipts and return structured JSON. You never include prose, explanations, markdown, or code fences. You output exactly one JSON object and nothing else.";

export const VISION_USER_PROMPT = `Extract the following fields from this receipt image and return ONLY a JSON object with this exact shape:

{
  "vendor": string,             // merchant/business name as printed
  "amount": number,             // grand total paid, in major currency units (e.g. 18.45)
  "currency": string,           // ISO 4217 code, uppercase, e.g. "USD". Infer from symbol/locale; default "USD" if ambiguous.
  "date": string,               // ISO 8601 datetime (e.g. "2026-04-28T14:32:00-07:00"). If only a date is visible, use T00:00:00Z.
  "category": string,           // one of: ${CATEGORIES.join(", ")}. Pick the best fit; use "other" only as last resort.
  "lineItems": [                // every individually-priced item on the receipt
    { "description": string, "price": number }
  ],
  "tax": number,                // total tax. Use 0 if not present.
  "tip": number                 // tip / gratuity. Use 0 if not present.
}

Rules:
- Output a single valid JSON object. No markdown, no commentary, no trailing text.
- Use 0 (not null) for missing numeric fields (tax, tip, line item prices).
- If vendor is unreadable, use "Unknown".
- If date is unreadable, use today's date in UTC.
- Numbers must be JSON numbers, not strings. Do not include currency symbols inside numbers.
- "amount" is the final grand total, including tax and tip.`;
