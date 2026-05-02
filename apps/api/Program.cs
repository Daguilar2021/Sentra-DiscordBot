DotNetEnv.Env.Load("../../.env");
var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddOpenApi();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("http://localhost:4200")
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

record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
{
    public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
}
