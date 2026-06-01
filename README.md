# Sentra-DiscordBot

Sentra is a Discord bot designed to improve organization and reduce friction between participants, mentors, and organizers at large-scale events such as hackathons.

## Overview

Sentra consists of four main components:

* Discord Bot (Python)
* Web Dashboard (Angular)
* Backend API (.NET)
* PostgreSQL Database

For local development, all services can be started using Docker Compose.

## Prerequisites

Before getting started, install:

* Docker Desktop (Windows/macOS) or Docker Engine (Linux)
* Git
* A Discord Developer Application for OAuth testing

## Clone the Repository

```bash
git clone <repository-url>
cd sentra
```

## Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

At a minimum, configure the following values:

```env
CLIENT_ID=your_discord_client_id
CLIENT_SECRET=your_discord_client_secret

POSTGRES_DB=sentra
POSTGRES_USER=sentra
POSTGRES_PASSWORD=sentra
```

> **Important:** Never commit your `.env` file. Use `.env.example` as the template and keep secrets such as `CLIENT_SECRET` private.

## Local Development

### Start Core Services

Build and start PostgreSQL, the API, and the Dashboard:

```bash
docker compose up -d --build
```

Open:

| Service    | URL                   |
| ---------- | --------------------- |
| Dashboard  | http://localhost:4200 |
| API        | http://localhost:5000 |
| PostgreSQL | localhost:5432        |

### Run the Discord Bot

The Discord Bot is configured as an optional Docker Compose profile.

To run it alongside the API, Dashboard, and PostgreSQL services:

```bash
docker compose --profile bot up -d --build
```

The bot profile expects valid Discord credentials in `.env`.

The first startup may take several minutes because moderation model dependencies are downloaded and cached. The Hugging Face cache is persisted in the `sentra-huggingface-cache` Docker volume.

### Useful Commands

View running services:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs --tail=120 api
```

View Dashboard logs:

```bash
docker compose logs --tail=120 dashboard
```

View Bot logs:

```bash
docker compose --profile bot logs --tail=120 bot
```

### Stop Services

Stop all running containers:

```bash
docker compose down
```

Stop all containers and remove database volumes:

```bash
docker compose down -v
```

### Rebuild Everything

If you encounter issues during development, rebuilding the environment often resolves them:

```bash
docker compose down -v
docker compose up --build
```

## Database Defaults

Docker Compose provides the following defaults if they are not overridden:

```env
POSTGRES_DB=sentra
POSTGRES_USER=sentra
POSTGRES_PASSWORD=sentra
POSTGRES_PORT=5432

API_PORT=5000
DASHBOARD_PORT=4200
```

Inside Docker containers, services communicate using Docker service names.

For example, the PostgreSQL hostname is:

```text
postgres
```

When running services directly on your host machine instead of Docker, continue using:

```text
localhost
```

> **Note:** The database initialization script only runs when the PostgreSQL volume is created for the first time. If you modify the schema and need a fresh local database, run:

```bash
docker compose down -v
docker compose up --build
```

## OAuth Development with Cloudflare Tunnel

Discord OAuth requires a publicly accessible HTTPS callback URL.

Because your local machine is not accessible from the internet, you must create a temporary Cloudflare Tunnel when testing authentication and verification workflows.

### Install Cloudflared

#### Windows

```bash
winget install Cloudflare.cloudflared
```

#### macOS

```bash
brew install cloudflare/cloudflare/cloudflared
```

#### Linux

Download and install the appropriate package from the Cloudflare releases page.

### Start a Tunnel

Expose the local API running on port 5000:

```bash
cloudflared tunnel --url http://localhost:5000
```

Cloudflare will generate a public URL similar to:

```text
https://example-name.trycloudflare.com
```

Keep the terminal window open while testing. Closing it will terminate the tunnel.

### Configure Discord OAuth

1. Open the Discord Developer Portal.
2. Select your application.
3. Navigate to **OAuth2 → Redirects**.
4. Add the callback URL:

```text
https://example-name.trycloudflare.com/api/auth/callback
```

5. Save your changes.

### Update Local Environment Variables

Update your `.env` file:

```env
API_URL=https://example-name.trycloudflare.com
```

Restart the API container:

```bash
docker compose restart api
```

You can now test Discord authentication locally using the Cloudflare Tunnel URL.

> **Important:** Because this is a temporary tunnel, the URL changes every time you restart `cloudflared`. Whenever a new tunnel URL is generated, update both your `.env` file and the Discord Developer Portal redirect URI.
