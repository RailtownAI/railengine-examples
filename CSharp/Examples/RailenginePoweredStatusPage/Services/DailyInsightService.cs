using System.Net.Http.Json;
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

    private const string Prompt =
        "You are an automated reviewer for a status page dashboard. " +
        "Use the available Railengine tools to fetch the most recent metric records stored in this engine, then summarize what you find.\n\n" +
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
        using var client = httpClientFactory.CreateClient();
        using var request = new HttpRequestMessage(HttpMethod.Post, "https://api.anthropic.com/v1/messages");
        request.Headers.Add("x-api-key", apiKey);
        request.Headers.Add("anthropic-version", apiVersion);
        request.Headers.Add("anthropic-beta", beta);

        var body = new
        {
            model,
            max_tokens = 1024,
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

        using var response = await client.SendAsync(request, ct);
        var responseBody = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException($"Claude API returned {(int)response.StatusCode}: {responseBody}");
        }

        using var doc = JsonDocument.Parse(responseBody);
        var content = doc.RootElement.GetProperty("content");

        // Take the final text block. Earlier text blocks are narration emitted
        // between MCP tool calls ("I'll start by exploring…") which we don't want.
        var text = content.EnumerateArray()
            .Where(b => b.GetProperty("type").GetString() == "text")
            .Select(b => b.GetProperty("text").GetString())
            .Where(s => !string.IsNullOrWhiteSpace(s))
            .LastOrDefault() ?? "";

        state.Text = text;
        state.GeneratedAt = DateTimeOffset.UtcNow;
        logger.LogInformation("Daily insight generated ({Length} chars)", text.Length);
    }
}
