using System.Text.Json.Serialization;

namespace RailenginePoweredStatusPage.Models;

public class MetricRecord
{
    [JsonPropertyName("metric")]
    public string Metric { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public long Timestamp { get; set; }

    [JsonPropertyName("value")]
    public double Value { get; set; }
}
