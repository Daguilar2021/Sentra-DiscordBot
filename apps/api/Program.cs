DotNetEnv.Env.Load("../../.env");
var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddOpenApi();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(
            "http://localhost:4200",
            "https://sentradev.vercel.app",
             )
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseCors();

app.MapPost("/api/auth/discord/callback", async (DiscordCallbackRequest request) =>
{
    if (string.IsNullOrWhiteSpace(request.Code))
        return Results.BadRequest(new { error = "Missing Discord code" });

    if (string.IsNullOrWhiteSpace(request.State))
        return Results.BadRequest(new { error = "Missing state/guild_id" });

    // Later: exchange code with Discord
    // Later: get Discord user
    // Later: save user to Supabase/Postgres

    return Results.Ok(new
    {
        message = "OAuth callback received",
        code = request.Code,
        state = request.State
    });
});

app.MapGet("/api/health", () => Results.Ok("Healthy"));

app.MapGet("/api/invite", (IConfiguration config) =>
{
    var clientId = config["CLIENT_ID"];
    var permissions = "8";

    var inviteUrl = $"https://discord.com/api/oauth2/authorize" +
                    $"?client_id={clientId}" +
                    $"&permissions={permissions}" +
                    $"&scope={Uri.EscapeDataString("bot applications.commands")}";

    return Results.Ok(new { url = inviteUrl });
});

app.Run();

public class DiscordCallbackRequest
{
    public string Code { get; set; } = "";
    public string State { get; set; } = "";
}