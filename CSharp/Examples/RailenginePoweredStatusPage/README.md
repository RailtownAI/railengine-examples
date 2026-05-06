# Railengine Powered Status Page

A minimal ASP.NET Core web app that demonstrates using the [Railengine](https://railtown.ai) SDK to retrieve metrics and display them as live charts on a status page.

## What it does

The app exposes a `/api/metrics` endpoint that queries a Railengine engine for metric records, then serves a status page that renders the results as one Chart.js line chart per configured metric. Each card header shows the most recent value with its unit, rounded to 2 decimal places. The page fetches updated data every 5 minutes (configurable via `REFRESH_INTERVAL_MS` in `wwwroot/index.html`) and updates the charts in place — no full page reload.

## Expected metric shape

The engine is expected to return records in the following format:

```json
{ "metric": "engine-load", "timestamp": 1778023020646, "value": 64.2 }
{ "metric": "team-members", "timestamp": 1778023021948, "value": 1240 }
{ "metric": "logs", "timestamp": 1778023023341, "value": 0.133333 }
```

Each record has a `metric` name, a Unix millisecond `timestamp`, and a numeric `value`. Multiple records per metric are supported and will be plotted as a time series.

The C# `MetricRecord` model deserializes from camelCase JSON via `[JsonPropertyName]` attributes. If you copy the model into another project and use PascalCase JSON content, all values will silently deserialize to their type defaults (zeros, empty strings) — adjust the attributes (or your stored JSON) to match.

## Customizing metrics

To adapt the page for a different set of metrics, edit only the `METRICS` array near the top of the script in `wwwroot/index.html`:

```js
const METRICS = [
  { key: 'engine-load',  label: 'Railengine',    unit: 'bytes/min', color: '#6366f1' },
  { key: 'team-members', label: 'Users',         unit: 'users',     color: '#22d3ee', hideRepeats: true },
  { key: 'logs',         label: 'Conductr Logs', unit: 'logs/min',  color: '#34d399' },
];
```

Each entry:

- `key` — must match the `metric` field on records returned by `/api/metrics`
- `label` — shown as the card header
- `unit` — appended after the latest reading (e.g. `5.23 bytes/min`)
- `color` — the line and fill color (any CSS color)
- `hideRepeats` — optional, defaults to `false`. When `true`, point markers are suppressed for samples whose value matches the previous one — useful for metrics that report constantly when you only care about changes (e.g. user counts). The line itself stays continuous; only the dots are hidden.

Cards are generated from this list at page load, so adding, removing, renaming, or recoloring a metric is a one-line change. The page title and `<h1>` heading are still hardcoded in `wwwroot/index.html` if you want to rebrand those too.

## Configuration

### IP allowlist

Access to the site is restricted by IP address. Any request from an IP not on the allowlist receives a `403 Forbidden` response.

The allowed IPs are configured via the `AllowedIPs` array in `appsettings.json`:

```json
"AllowedIPs": [ "127.0.0.1", "::1" ]
```

The default permits localhost only. Add the IP addresses of any machines that should be able to view the status page.

## Getting started

1. Copy `appsettings.Development.sample.json` to `appsettings.Development.json`
2. Fill in your Railengine PAT and engine ID
3. Add any additional IP addresses to `AllowedIPs` as needed
4. Run the app:

```bash
dotnet run
```

The status page is served at `https://localhost:<port>/`.
