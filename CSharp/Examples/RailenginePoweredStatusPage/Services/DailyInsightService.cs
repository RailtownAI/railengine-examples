using System.Net.Http.Json;
using System.Text;
using System.Text.Json;

namespace RailenginePoweredStatusPage.Services;

public class DailyInsightService : BackgroundService
{
    private readonly IHttpClientFactory httpClientFactory;
    private readonly DailyInsight state;
    private readonly ILogger<DailyInsightService> logger;
    private readonly string apiKey;
    private readonly string apiVersion;
    private readonly string beta;
    private readonly string model;
    private readonly Guid engineId;
    private readonly string pat;
    private readonly string mcpServerBaseUrl;
    private readonly string mcpServerName;

    private static readonly TimeSpan Interval = TimeSpan.FromHours(24);
    private static readonly TimeSpan RequestTimeout = TimeSpan.FromMinutes(10);

    private const string Prompt =
        "You are an automated reviewer for a status page dashboard.\n\n" +
        "Use AT MOST 2 Railengine tool calls. Call `getEngineStorageDocuments` to fetch the 50 most recent metric records in a single call, then summarize. Do not use the vector or embedding search tools — this engine has no vectors. Do not make additional exploratory calls.\n\n" +
        "Output format (strict):\n" +
        "- One single line per metric, nothing else.\n" +
        "- Format: \"{Metric name}: {one-sentence insight including the latest value and any notable trend}\"\n" +
        "- Plain text only. No markdown, no headers, no bullets, no emoji, no bold.\n" +
        "- No preamble, no commentary about your process, no closing remarks.\n" +
        "- If a metric is flat, say so concisely.";

    public DailyInsightService(
        IHttpClientFactory httpClientFactory,
        DailyInsight state,
        IConfiguration configuration,
        ILogger<DailyInsightService> logger)
    {
        this.httpClientFactory = httpClientFactory;
        this.state = state;
        this.logger = logger;
        apiKey = configuration["Anthropic:ApiKey"] ?? "";
        apiVersion = configuration["Anthropic:ApiVersion"]!;
        beta = configuration["Anthropic:Beta"]!;
        model = configuration["Anthropic:Model"]!;
        engineId = Guid.Parse(configuration["RailEngine:EngineId"]!);
        pat = configuration["RailEngine:PAT"]!;
        mcpServerBaseUrl = configuration["RailEngine:McpServerBaseUrl"]!.TrimEnd('/');
        mcpServerName = configuration["RailEngine:McpServerName"]!;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (string.IsNullOrEmpty(apiKey))
        {
            logger.LogInformation("Anthropic:ApiKey not configured; daily insight disabled.");
            return;
        }

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await GenerateAsync(stoppingToken);
                state.Error = null;
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Daily insight generation failed");
                state.Error = ex.Message;
            }

            try { await Task.Delay(Interval, stoppingToken); }
            catch (TaskCanceledException) { return; }
        }
    }

    private async Task GenerateAsync(CancellationToken ct)
    {
        logger.LogInformation("Starting daily insight generation…");

        // Bound the entire streamed call by RequestTimeout via a linked CTS,
        // and disable HttpClient.Timeout so it doesn't cancel the stream mid-read.
        using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        cts.CancelAfter(RequestTimeout);

        using var client = httpClientFactory.CreateClient();
        client.Timeout = Timeout.InfiniteTimeSpan;
        using var request = new HttpRequestMessage(HttpMethod.Post, "https://api.anthropic.com/v1/messages");
        request.Headers.Add("x-api-key", apiKey);
        request.Headers.Add("anthropic-version", apiVersion);
        request.Headers.Add("anthropic-beta", beta);

        var body = new
        {
            model,
            max_tokens = 256,
            stream = true,
            mcp_servers = new[]
            {
                new
                {
                    type = "url",
                    url = $"{mcpServerBaseUrl}/{engineId}",
                    name = mcpServerName,
                    authorization_token = pat,
                },
            },
            messages = new[]
            {
                new { role = "user", content = Prompt },
            },
        };

        request.Content = JsonContent.Create(body);

        // ResponseHeadersRead returns as soon as headers arrive; stream is read below.
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cts.Token);

        if (!response.IsSuccessStatusCode)
        {
            var errBody = await response.Content.ReadAsStringAsync(cts.Token);
            throw new InvalidOperationException($"Claude API returned {(int)response.StatusCode}: {errBody}");
        }

        var text = await ReadTextFromStreamAsync(response, cts.Token);

        state.Text = text;
        state.GeneratedAt = DateTimeOffset.UtcNow;
        logger.LogInformation("Daily insight generated ({Length} chars)", text.Length);
    }

    // Parse Anthropic's SSE stream and accumulate text per content-block index.
    // We only care about blocks of type "text"; mcp_tool_use and mcp_tool_result
    // blocks are tracked but their content ignored. The final assistant answer
    // is the highest-indexed text block.
    private static async Task<string> ReadTextFromStreamAsync(HttpResponseMessage response, CancellationToken ct)
    {
        var blocks = new Dictionary<int, (string Type, StringBuilder Text)>();

        using var stream = await response.Content.ReadAsStreamAsync(ct);
        using var reader = new StreamReader(stream);

        string? eventType = null;
        string? line;
        while ((line = await reader.ReadLineAsync(ct)) != null)
        {
            if (line.StartsWith("event:"))
            {
                eventType = line["event:".Length..].Trim();
                continue;
            }
            if (!line.StartsWith("data:")) continue;

            var data = line["data:".Length..].Trim();
            if (string.IsNullOrEmpty(data)) continue;

            using var doc = JsonDocument.Parse(data);
            var root = doc.RootElement;

            switch (eventType)
            {
                case "content_block_start":
                {
                    var index = root.GetProperty("index").GetInt32();
                    var block = root.GetProperty("content_block");
                    var blockType = block.GetProperty("type").GetString() ?? "";
                    var sb = new StringBuilder();
                    if (blockType == "text" && block.TryGetProperty("text", out var initialText))
                    {
                        sb.Append(initialText.GetString());
                    }
                    blocks[index] = (blockType, sb);
                    break;
                }
                case "content_block_delta":
                {
                    var index = root.GetProperty("index").GetInt32();
                    var delta = root.GetProperty("delta");
                    if (delta.GetProperty("type").GetString() == "text_delta"
                        && blocks.TryGetValue(index, out var entry))
                    {
                        entry.Text.Append(delta.GetProperty("text").GetString());
                    }
                    break;
                }
                case "error":
                {
                    var msg = root.TryGetProperty("error", out var err) && err.TryGetProperty("message", out var m)
                        ? m.GetString()
                        : data;
                    throw new InvalidOperationException($"Claude API stream error: {msg}");
                }
            }
        }

        return blocks
            .OrderBy(kvp => kvp.Key)
            .Where(kvp => kvp.Value.Type == "text")
            .Select(kvp => kvp.Value.Text.ToString())
            .Where(s => !string.IsNullOrWhiteSpace(s))
            .LastOrDefault() ?? "";
    }
}
