import asyncio
import threading
import discord
from discord.ext import commands

from Bot.config import Config
from Bot.DB.dbLink import init_db
from Bot.oauth import app
from Bot.Commands.admin import sentra
from Bot.Commands.verify import register_verify_command
from Bot.Commands.tickets import TicketPanel, TicketActions

def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

intents = discord.Intents.none()
intents.guilds = True

bot = commands.Bot(command_prefix=None, intents=intents)

# Register commands once, at import time
bot.tree.add_command(sentra)
register_verify_command(bot.tree)

has_started = False

@bot.event
async def on_ready():
    global has_started
    if has_started:
        return
    has_started = True

    print(f"✅ Logged in as {bot.user}")

    init_db()
    threading.Thread(target=run_flask, daemon=True).start()

    # Register persistent views
    bot.add_view(TicketPanel())
    bot.add_view(TicketActions())

    await bot.tree.sync()
    print("✅ Slash commands synced.")
    print("✅ Database linked and Web Server active.")

async def start_everything():
    Config.validate()
    await bot.start(Config.TOKEN)

if __name__ == "__main__":
    asyncio.run(start_everything())

