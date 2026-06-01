# Sentra-DiscordBot

Sentra is a Discord Bot tailored towards improving organization and minimizing friction between participants and organizers in large events like Hackathons

## Docker Local Development

This repo includes a Docker Compose setup for local development. It follows the same root-level Compose pattern used by the Odysseus project: Compose is the main local entry point, and each app service has a focused Dockerfile.

Start the database, .NET API, and Angular dashboard:

```powershell
docker compose up -d --build
```

Open:

- Dashboard: `http://localhost:4200`
- API health check: `http://localhost:5000/api/health`
- Postgres: `localhost:5432`

Start the Discord bot too:

```powershell
docker compose --profile bot up -d --build
```

The bot profile expects real Discord credentials in `.env`. The first bot startup can take a while because the moderation model dependencies are large and the Hugging Face model cache is persisted in the `sentra-huggingface-cache` Docker volume.

Useful checks:

```powershell
docker compose ps
docker compose logs --tail=120 api
docker compose logs --tail=120 dashboard
docker compose --profile bot logs --tail=120 bot
```

Compose provides local database defaults if you do not override them:

```env
POSTGRES_DB=sentra
POSTGRES_USER=sentra
POSTGRES_PASSWORD=sentra
POSTGRES_PORT=5432
API_PORT=5000
DASHBOARD_PORT=4200
```

Inside containers, the database URL is overridden to use the Compose service name `postgres`. Keep using localhost values when you run pieces directly on your host machine.

## 🛠️ Local Development Setup

Because Sentra uses a Web Dashboard that requires users to log in via Discord (OAuth2), Discord needs a secure, public `https://` URL to send users back to after they authenticate. 

When developing locally, your `localhost` is not accessible to the internet. To fix this, you must set up a **Cloudflare Tunnel** to securely expose your local backend.

### Setting Up a Temporary Cloudflare Tunnel (Quick Start)

Follow these steps to generate a temporary, public URL for your local environment:

1. **Install Cloudflared CLI**
   * **Windows:** Download and install via [Winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/): `winget install Cloudflare.cloudflared` (or download the `.exe` from [Cloudflare's GitHub](https://github.com/cloudflare/cloudflared/releases)).
   * **macOS:** Install via Homebrew: `brew install cloudflare/cloudflare/cloudflared`
   * **Linux:** Download the `.deb` or `.rpm` package from the [Cloudflare releases page](https://github.com/cloudflare/cloudflared/releases).

2. **Start the Tunnel**
   Run the following command in your terminal to route traffic from a public URL to your local backend (assuming the OAuth callbacks are handled on port 5000):
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```

3. **Get Your Public URL**
   In the terminal output, look for a line that says something like: 
   `https://<random-words>.trycloudflare.com`. Copy this URL. Keep the terminal open, as closing it will kill the tunnel.

4. **Update Your Discord Developer App**
   * Go to the [Discord Developer Portal](https://discord.com/developers/applications) and select your application.
   * Navigate to the **OAuth2** tab.
   * Under **Redirects**, add your new URL appended with `/callback`. 
   * *Example:* `https://<random-words>.trycloudflare.com/callback`
   * Save your changes.

5. **Update Your `.env` File**
   * Open the `.env` file in the root of the project.
   * Find the `REDIRECT_URI` variable.
   * Paste the exact same URL you added to Discord:
     ```env
     REDIRECT_URI=https://<random-words>.trycloudflare.com/callback
     ```

> **Important:** Because this is a *temporary* tunnel, the URL will change every time you restart the `cloudflared` command. You will need to update both your `.env` file and the Discord Developer Portal with the new URL whenever you start a new session.
