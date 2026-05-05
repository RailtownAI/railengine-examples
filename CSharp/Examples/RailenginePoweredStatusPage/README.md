# Railengine Powered Status Page

A minimal ASP.NET Core web app that demonstrates using the [Railengine](https://railtown.ai) SDK to retrieve metrics and display them as live charts on a status page.

## What it does

The app exposes a `/api/metrics` endpoint that queries a Railengine engine for metric records, then serves a status page that renders the results as three Chart.js line charts — one per metric. The page auto-refreshes every 5 minutes.

## Expected metric shape

The engine is expected to return records in the following format:

```json
{ "metric": "engine-load", "timestamp": 1778023020646, "value": 64.2 }
{ "metric": "team-members", "timestamp": 1778023021948, "value": 1240 }
{ "metric": "logs", "timestamp": 1778023023341, "value": 0.133333 }
```

Each record has a `metric` name, a Unix millisecond `timestamp`, and a numeric `value`. Multiple records per metric are supported and will be plotted as a time series.

## Getting started

1. Copy `appsettings.Development.sample.json` to `appsettings.Development.json`
2. Fill in your Railengine PAT and engine ID
3. Run the app:

```bash
dotnet run
```

The status page is served at `https://localhost:<port>/`.
