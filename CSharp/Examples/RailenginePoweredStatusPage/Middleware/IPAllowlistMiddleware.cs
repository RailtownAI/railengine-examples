using System.Net;

namespace RailenginePoweredStatusPage.Middleware;

public class IPAllowlistMiddleware
{
    private readonly RequestDelegate next;
    private readonly HashSet<IPAddress> allowedIPs;

    public IPAllowlistMiddleware(RequestDelegate next, IConfiguration configuration)
    {
        this.next = next;
        var entries = configuration.GetSection("AllowedIPs").Get<string[]>() ?? [];
        allowedIPs = entries.Select(IPAddress.Parse).ToHashSet();
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var remoteIP = context.Connection.RemoteIpAddress;

        if (remoteIP is null || !allowedIPs.Contains(remoteIP.MapToIPv4()) && !allowedIPs.Contains(remoteIP.MapToIPv6()))
        {
            context.Response.StatusCode = StatusCodes.Status403Forbidden;
            return;
        }

        await next(context);
    }
}
