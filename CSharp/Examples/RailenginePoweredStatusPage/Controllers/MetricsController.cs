using Microsoft.AspNetCore.Mvc;
using Railengine;
using RailenginePoweredStatusPage.Models;
using RailenginePoweredStatusPage.Services;

namespace RailenginePoweredStatusPage.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MetricsController : ControllerBase
{
    private readonly RailengineClient railengineClient;
    private readonly Guid engineId;
    private readonly IEnumerable<IExternalMetricSource> externalSources;

    public MetricsController(RailengineClient railengineClient, IConfiguration configuration, IEnumerable<IExternalMetricSource> externalSources)
    {
        this.railengineClient = railengineClient;
        this.externalSources = externalSources;
        engineId = Guid.Parse(configuration["RailEngine:EngineId"]!);
    }

    [HttpGet]
    public async Task<ActionResult<List<MetricRecord>>> GetMetrics()
    {
        var page1 = await railengineClient.ListStorageDocuments<MetricRecord>(engineId, pageNumber: 1, pageSize: 100);
        var page2 = await railengineClient.ListStorageDocuments<MetricRecord>(engineId, pageNumber: 2, pageSize: 100);

        var railengineRecords = page1.Items.Concat(page2.Items)
            .Select(i => i.Document)
            .Where(r => r.Timestamp.HasValue && r.Value.HasValue)
            .OrderByDescending(r => r.Timestamp)
            .Take(144);

        var externalTasks = externalSources.Select(s => s.GetRecordsAsync());
        var externalRecords = (await Task.WhenAll(externalTasks)).SelectMany(r => r);

        return Ok(railengineRecords.Concat(externalRecords).ToList());
    }
}
