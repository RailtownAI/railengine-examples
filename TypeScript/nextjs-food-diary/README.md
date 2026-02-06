# Food Diary powered by Railengine

## Setup

1. Sign up for a free account at [Railengine](https://railengine.ai)
2. Create a new Engine with the schema in `engine-schema.json`
3. Install dependencies:

   ```bash
   npm install
   ```

4. Copy `.env.example` to `.env` and fill in your Railengine credentials from your engine dashboard:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your:
   - `ENGINE_TOKEN` - Your Engine Token for ingestion
   - `ENGINE_PAT` - Your Engine PAT for retrieval
   - `ENGINE_ID` - Your Engine ID

5. Run the development server:

   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000) in your browser.
