# Railengine samples that use the C# SDK

This folder contains C# / .NET examples that use the [Railengine](https://railengine.ai) SDK. The SDK is published on NuGet and works in any .NET 8+ application.

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download) or later
- A free [Railengine](https://railengine.ai) account

## Set up Railengine

1. Sign up for a free account at [Railengine](https://railengine.ai)
2. Create an Agent project
3. Create a new Engine with a schema that matches the data you want to store
4. From the engine settings, generate the credentials you need:
   - **PAT** — Personal Access Token, used for retrieval
   - **Engine Token** — used for ingestion
   - **Engine ID** — shown on the engine page

For a worked end-to-end setup with an example schema, see the [TypeScript Expense Tracker](../TypeScript/nextjs-expensify) — the engine setup flow is the same regardless of language.

## Install the NuGet packages

The Railengine C# SDK is split into separate packages so you can install only what you need:

- **[Railengine.Retrieval](https://www.nuget.org/packages/Railengine.Retrieval)** — query stored documents (list, get by ID, index search, vector search). Used by the status page example.
- **[Railengine.Ingestion](https://www.nuget.org/packages/Railengine.Ingestion)** — upsert and delete documents.

Install via the .NET CLI:

```bash
dotnet add package Railengine.Retrieval
dotnet add package Railengine.Ingestion
```

Or add a `<PackageReference>` to your `.csproj`:

```xml
<PackageReference Include="Railengine.Retrieval" Version="1.0.2" />
```

## Configure credentials

Examples in this folder read credentials from `appsettings.Development.json` (committed only as `.sample.json` for safety). A typical configuration block:

```json
"RailEngine": {
  "PAT": "[your-pat-token-here]",
  "EngineId": "[your-engine-id-here]"
}
```

Register `RailengineClient` as a singleton in `Program.cs`:

```csharp
using Railengine;

builder.Services.AddHttpClient();
builder.Services.AddSingleton<RailengineClient>(sp =>
{
    var config = sp.GetRequiredService<IConfiguration>();
    var httpClient = sp.GetRequiredService<IHttpClientFactory>().CreateClient();
    var pat = config["RailEngine:PAT"]!;
    return new RailengineClient(httpClient, pat);
});
```

Then inject `RailengineClient` into your controllers or services.

## Examples

- **[RailenginePoweredStatusPage](Examples/RailenginePoweredStatusPage)** — ASP.NET Core status page that pulls metric records from Railengine and renders them as live Chart.js line charts. Demonstrates `RailengineClient.ListStorageDocuments<T>`.

## Run an example

```bash
cd Examples/RailenginePoweredStatusPage
cp appsettings.Development.sample.json appsettings.Development.json
# edit appsettings.Development.json with your PAT and Engine ID
dotnet run
```
