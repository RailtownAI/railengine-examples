using System.Net.Http.Json;
using RailenginePoweredStatusPage.Models;

namespace RailenginePoweredStatusPage.Services;

public class PyPiDownloadsSource : IExternalMetricSource
{
    private readonly IHttpClientFactory httpClientFactory;
    private readonly string package;

    public PyPiDownloadsSource(IHttpClientFactory httpClientFactory, IConfiguration configuration)
    {
        this.httpClientFactory = httpClientFactory;
        package = configuration["PyPi:Package"] ?? "railtracks";
    }

    public async Task<IEnumerable<MetricRecord>> GetRecordsAsync()
    {
        var client = httpClientFactory.CreateClient();
        var httpResponse = await client.GetAsync(
            $"https://pypistats.org/api/packages/{package}/overall");

        if (!httpResponse.IsSuccessStatusCode) return [];

        var response = await httpResponse.Content.ReadFromJsonAsync<PyPiOverallResponse>();

        if (response?.Data == null) return [];

        return response.Data
            .Where(e => e.Category == "without_mirrors")
            .OrderByDescending(e => e.Date)
            .Take(30)
            .Select(e => new MetricRecord
            {
                Metric = "pypi-downloads",
                Timestamp = DateTimeOffset.Parse(e.Date).ToUnixTimeMilliseconds(),
                Value = e.Downloads,
            });
    }
}
