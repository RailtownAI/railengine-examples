using Railengine;
using RailenginePoweredStatusPage.Middleware;
using RailenginePoweredStatusPage.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddHttpClient();
builder.Services.AddSingleton<RailengineClient>(sp =>
{
    var config = sp.GetRequiredService<IConfiguration>();
    var httpClient = sp.GetRequiredService<IHttpClientFactory>().CreateClient();
    var pat = config["RailEngine:PAT"]!;
    return new RailengineClient(httpClient, pat);
});
builder.Services.AddSingleton<DailyInsight>();
builder.Services.AddHostedService<DailyInsightService>();

var app = builder.Build();

app.UseMiddleware<IPAllowlistMiddleware>();

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapControllers();

app.Run();
