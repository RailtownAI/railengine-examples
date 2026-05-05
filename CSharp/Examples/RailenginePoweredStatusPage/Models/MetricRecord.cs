namespace RailenginePoweredStatusPage.Models;

public class MetricRecord
{
    public string Metric { get; set; } = string.Empty;
    public long Timestamp { get; set; }
    public double Value { get; set; }
}
