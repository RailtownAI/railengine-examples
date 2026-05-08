using RailenginePoweredStatusPage.Models;

namespace RailenginePoweredStatusPage.Services;

public interface IExternalMetricSource
{
    Task<IEnumerable<MetricRecord>> GetRecordsAsync();
}
