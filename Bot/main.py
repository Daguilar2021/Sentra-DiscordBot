# ./Sentra-DiscordBot/Bot/main.py
# This is the main entry point for the Sentra Discord bot. It handles the initialization of the bot and the registration of commands.

import asyncio
import discord
from discord.ext import commands
from config import Config
from DB.dbLink import init_db
from Commands.admin import sentra
from Commands.verify import register_verify_command
from Commands.tickets import TicketPanel, TicketActions, StaffClaimView
from Commands.resume import resume_cmds
from Commands.team import team_cmds, RequestToJoinView, ApproveJoinView
from Commands.mod_listener import setup_mod_listener

intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=None, intents=intents)

# Register commands once, at import time
bot.tree.add_command(sentra)
bot.tree.add_command(resume_cmds)
bot.tree.add_command(team_cmds)
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

    # Load moderation engine (heavy model load — do once at startup)
    print("⏳ Loading moderation engine...")
    from Bot.Moderation.engine import ModerationEngine
    mod_engine = ModerationEngine()
    setup_mod_listener(bot, mod_engine)

    # Register persistent views
    bot.add_view(TicketPanel())
    bot.add_view(TicketActions())
    bot.add_view(StaffClaimView())
    bot.add_view(RequestToJoinView())
    bot.add_view(ApproveJoinView())

    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands synced: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print("✅ Database linked and Web Server active.")

async def start_everything():
    Config.validate()
    await bot.start(Config.TOKEN)

if __name__ == "__main__":
    asyncio.run(start_everything())

