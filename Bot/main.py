import asyncio
import threading
import discord
from discord.ext import commands
from .config import Config
from .dbLink import init_db
from .oauth import app

# Bot Setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Run Web Server in Background
def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    print('✅ Database linked and Web Server active.')

@bot.command()
async def verify(ctx):
    # This URL triggers the Discord 'Authorize' screen
    url = (f"https://discord.com/api/oauth2/authorize?client_id={Config.CLIENT_ID}"
           f"&redirect_uri={Config.REDIRECT_URI}&response_type=code&scope=identify%20email")
    
    embed = discord.Embed(title="Sentra Verification", color=discord.Color.blue())
    embed.description = f"[Click here to verify your email]({url})"
    await ctx.author.send(embed=embed)
    await ctx.send("Check your DMs for a verification link!")

async def start_everything():
    Config.validate()
    init_db() # Ensure tables are ready
    
    # Start Flask
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Bot
    async with bot:
        await bot.start(Config.TOKEN)

if __name__ == "__main__":
    asyncio.run(start_everything())