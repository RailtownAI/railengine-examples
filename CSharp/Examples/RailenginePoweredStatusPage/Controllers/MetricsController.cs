using Microsoft.AspNetCore.Mvc;
using Railengine;
using RailenginePoweredStatusPage.Models;

namespace RailenginePoweredStatusPage.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MetricsController : ControllerBase
{
    private readonly RailengineClient railengineClient;
    private readonly Guid engineId;

    public MetricsController(RailengineClient railengineClient, IConfiguration configuration)
    {
        this.railengineClient = railengineClient;
        engineId = Guid.Parse(configuration["RailEngine:EngineId"]!);
    }

    [HttpGet]
    public async Task<ActionResult<List<MetricRecord>>> GetMetrics()
    {
        var results = await railengineClient.ListStorageDocuments<MetricRecord>(
            engineId,
            pageNumber: 1,
            pageSize: 100
        );

        return Ok(results.Items.Select(i => i.Document).ToList());
    }
}
