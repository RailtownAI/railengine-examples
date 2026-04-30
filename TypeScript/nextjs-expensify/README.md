# Expensify-style Expense Tracker powered by Railengine

A Next.js example app that ingests receipts into Railengine. Drop a receipt
image onto the page and Claude vision extracts the structured fields (vendor,
amount, currency, date, category, line items, tax, tip), which you confirm and
save into Railengine.

Built with Next.js 16 (app router), React 19, TypeScript, Tailwind CSS, and
shadcn/ui. Includes a light/dark theme toggle and a mobile-responsive layout.

## Setup

1. Sign up for a free account at [Railengine](https://railengine.ai)
2. Create an Agent project
3. Create a new Engine with the schema in `engine-schema.json`
4. Install dependencies:

   ```bash
   npm install
   ```

5. Copy `.env.example` to `.env` and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your:
   - `ENGINE_TOKEN` — Engine Token for ingestion
   - `ENGINE_PAT` — Engine PAT for retrieval
   - `ENGINE_ID` — Engine ID
   - `ANTHROPIC_API_KEY` — Anthropic API key (only needed for receipt OCR;
     manual entry and delete work without it)

6. Run the development server:

   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000) in your browser.

## How it works

```
image dropped
    → FileReader → base64
    → POST /api/extract
    → Claude vision (claude-opus-4-7)
    → JSON validated against ExtractedExpenseSchema
    → user reviews/edits in confirmation dialog
    → POST /api/ingest
    → RailEngineIngest.upsert(expense)
    → list refetches via /api/retrieve
```

The receipt image is **never stored in Railengine** — only the structured
fields end up in the document store. To change the model used for OCR, edit
the `model` string in
[`app/api/extract/route.ts`](app/api/extract/route.ts).

## Schema

The expense schema is defined in [`lib/schema.ts`](lib/schema.ts) and the
sample document at [`engine-schema.json`](engine-schema.json) matches it
exactly — paste it into your Railengine engine when creating the schema.
