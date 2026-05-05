using Railengine;
using RailenginePoweredStatusPage.Middleware;

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

var app = builder.Build();

app.UseMiddleware<IPAllowlistMiddleware>();

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapControllers();

app.Run();
