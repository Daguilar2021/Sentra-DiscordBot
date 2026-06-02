using System.Net.Http.Headers;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using Npgsql;

DotNetEnv.Env.Load("../../.env");

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHttpClient();

frontendUrl = builder.Configuration["FRONTEND_URL"] 
?? throw new InvalidOperationException("FRONTEND_URL is not configured");

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(frontendUrl)
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

var app = builder.Build();

app.UseCors();

app.MapGet("/api/auth/callback", async (
    string? code,
    string? state,
    IHttpClientFactory httpClientFactory,
    IConfiguration config) =>
{
    if (string.IsNullOrWhiteSpace(code))
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=missing_code");

    if (string.IsNullOrWhiteSpace(state))
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=missing_state");

    if (!ulong.TryParse(state, out var guildId))
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=invalid_state");

    var clientId = config["CLIENT_ID"];
    var clientSecret = config["CLIENT_SECRET"];
    var redirectUri = config["API_URL"] + "/api/auth/callback";

    var http = httpClientFactory.CreateClient();
    
    var tokenResponse = await http.PostAsync
    (
        "https://discord.com/api/oauth2/token",
        new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["client_id"] = clientId!,
            ["client_secret"] = clientSecret!,
            ["grant_type"] = "authorization_code",
            ["code"] = code,
            ["redirect_uri"] = redirectUri!
        })
    );

    if (!tokenResponse.IsSuccessStatusCode)
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=token_exchange_failed");

    var token = await tokenResponse.Content.ReadFromJsonAsync<DiscordTokenResponse>();

    if (string.IsNullOrWhiteSpace(token?.AccessToken))
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=no_access_token");

    var userRequest = new HttpRequestMessage(HttpMethod.Get, "https://discord.com/api/users/@me");
    userRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token.AccessToken);

    var userResponse = await http.SendAsync(userRequest);

    if (!userResponse.IsSuccessStatusCode)
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=user_fetch_failed");

    var discordUser = await userResponse.Content.ReadFromJsonAsync<DiscordUserResponse>();

    if (discordUser == null || string.IsNullOrWhiteSpace(discordUser.Id))
        return Results.Redirect($"{config["FRONTEND_URL"]}?error=invalid_user");

    var discordId = ulong.Parse(discordUser.Id);

    // Save or update user in Supabase
    try
    {
        var databaseString = config["CONNECTION_STRINGS"];
        using var connection = new NpgsqlConnection(databaseString);
        await connection.OpenAsync();

        // Upsert user (insert if new, update if exists)
        var cmd = connection.CreateCommand();
        cmd.CommandText = @"
            INSERT INTO users (discord_id, guild_id, email, is_verified, role)
            VALUES (@discord_id, @guild_id, @email, TRUE, 'hacker')
            ON CONFLICT (discord_id, guild_id) DO UPDATE SET
                email = EXCLUDED.email,
                is_verified = TRUE
            RETURNING id;
        ";

        cmd.Parameters.AddWithValue("@discord_id", (long)discordId);
        cmd.Parameters.AddWithValue("@guild_id", (long)guildId);
        cmd.Parameters.AddWithValue("@email", discordUser.Email ?? (object)DBNull.Value);

        var userId = await cmd.ExecuteScalarAsync();
    }
    catch (Exception ex)
    {
        // Log the error but don't fail the auth flow
        Console.Error.WriteLine($"Database error: {ex.Message}");
    }

    // Redirect to frontend success page with auth data
    var successUrl = $"{config["FRONTEND_URL"]}/auth/success?discordId={discordId}&guildId={state}&email={Uri.EscapeDataString(discordUser.Email ?? "")}";
    return Results.Redirect(successUrl);
});

//health check endpoint
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

public class DiscordTokenResponse
{
    [JsonPropertyName("access_token")]
    public string? AccessToken { get; set; }
}

public class DiscordUserResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("email")]
    public string? Email { get; set; }
}