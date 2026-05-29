# ./Sentra-DiscordBot/Bot/Commands/verify.py
# This script handles the verification system for the matchmaking system. It allows users to verify their email with Sentra.
import urllib.parse
import discord
from discord import app_commands

from config import Config

def register_verify_command(tree: app_commands.CommandTree):
    @tree.command(name="verify", description="Verify your email with Sentra")
    async def verify(interaction: discord.Interaction):
        redirect_uri = urllib.parse.quote(Config.API_URL + "/api/auth/callback", safe='')

        url = (
            f"https://discord.com/api/oauth2/authorize?client_id={Config.CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=identify%20email"
            f"&state={interaction.guild.id}"
        )

        embed = discord.Embed(
            title="Sentra Verification", 
            description="Click the button below to link your Discord account securely.",
            color=discord.Color.blue()
        )

        # Create a View with a URL Button
        view = discord.ui.View()
        button = discord.ui.Button(label="Verify Now", style=discord.ButtonStyle.link, url=url)
        view.add_item(button)

        try:
            await interaction.user.send(embed=embed, view=view)
            await interaction.response.send_message(
                "Check your DMs for a verification link!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I couldn’t DM you (your privacy settings block DMs). "
                "Please enable DMs for this server, then run `/verify` again.",
                ephemeral=True
            )
