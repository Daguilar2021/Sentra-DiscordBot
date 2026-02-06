import discord
from discord import app_commands
from Bot.DB.settings_store import get_or_create_settings, update_settings

def is_admin_or_owner(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.id == interaction.guild.owner_id:
        return True
    return interaction.user.guild_permissions.administrator

class SentraAdmin(app_commands.Group):
    def __init__(self):
        super().__init__(name="sentra", description="Sentra admin configuration commands")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_admin_or_owner(interaction):
            await interaction.response.send_message(
                "Only server admins/owner can use Sentra setup commands.",
                ephemeral=True
            )
            return False
        return True

sentra = SentraAdmin()

@sentra.command(name="view_config", description="View this server’s Sentra configuration")
async def view_config(interaction: discord.Interaction):
    s = get_or_create_settings(interaction.guild.id)

    def fmt_role(role_id):
        return f"<@&{role_id}>" if role_id else "Not set"

    def fmt_channel(channel_id):
        return f"<#{channel_id}>" if channel_id else "Not set"

    team_channels = s.team_chat_channel_ids or []
    team_channels_str = ", ".join(f"<#{cid}>" for cid in team_channels) if team_channels else "None"

    embed = discord.Embed(title="Sentra Server Config", color=discord.Color.blurple())
    embed.add_field(name="Mentor Role", value=fmt_role(s.mentor_role_id), inline=False)
    embed.add_field(name="Ticket Support Role", value=fmt_role(s.ticket_support_role_id), inline=False)
    embed.add_field(name="Team Chat Channels", value=team_channels_str, inline=False)
    embed.add_field(name="Find Teammates Channel", value=fmt_channel(s.find_teammates_channel_id), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@sentra.command(name="set_mentor_role", description="Set the mentor role")
async def set_mentor_role(interaction: discord.Interaction, role: discord.Role):
    update_settings(interaction.guild.id, mentor_role_id=role.id)
    await interaction.response.send_message(f"✅ Mentor role set to {role.mention}", ephemeral=True)

@sentra.command(name="set_ticket_support_role", description="Set the role that handles tickets")
async def set_ticket_support_role(interaction: discord.Interaction, role: discord.Role):
    update_settings(interaction.guild.id, ticket_support_role_id=role.id)
    await interaction.response.send_message(f"✅ Ticket support role set to {role.mention}", ephemeral=True)

@sentra.command(name="add_team_chat_channel", description="Add a channel as an official team chat")
async def add_team_chat_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    s = get_or_create_settings(interaction.guild.id)
    channels = s.team_chat_channel_ids or []
    if channel.id not in channels:
        channels.append(channel.id)
    update_settings(interaction.guild.id, team_chat_channel_ids=channels)
    await interaction.response.send_message(f"✅ Added team chat channel: {channel.mention}", ephemeral=True)

@sentra.command(name="set_find_teammates_channel", description="Set the channel used for find-teammates")
async def set_find_teammates_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    update_settings(interaction.guild.id, find_teammates_channel_id=channel.id)
    await interaction.response.send_message(f"✅ Find-teammates channel set to {channel.mention}", ephemeral=True)
