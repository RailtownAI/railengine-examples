using Microsoft.AspNetCore.Mvc;
using RailenginePoweredStatusPage.Services;

namespace RailenginePoweredStatusPage.Controllers;

[ApiController]
[Route("api/[controller]")]
public class InsightController : ControllerBase
{
    private readonly DailyInsight insight;

    public InsightController(DailyInsight insight)
    {
        this.insight = insight;
    }

    [HttpGet]
    public IActionResult Get() => Ok(new
    {
        text = insight.Text,
        generatedAt = insight.GeneratedAt,
        error = insight.Error,
    });
}
