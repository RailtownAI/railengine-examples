using System.Text.Json.Serialization;

namespace RailenginePoweredStatusPage.Models;

public class PyPiOverallResponse
{
    [JsonPropertyName("data")]
    public List<PyPiOverallEntry> Data { get; set; } = [];
}

public class PyPiOverallEntry
{
    [JsonPropertyName("category")]
    public string Category { get; set; } = string.Empty;

    [JsonPropertyName("date")]
    public string Date { get; set; } = string.Empty;

    [JsonPropertyName("downloads")]
    public double Downloads { get; set; }
}
