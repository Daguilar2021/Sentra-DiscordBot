import discord
from discord import app_commands
from Bot.DB.settings_store import get_or_create_settings, update_settings

def is_admin_or_owner(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.id == interaction.guild.owner_id:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    
    # Check for custom admin role
    s = get_or_create_settings(interaction.guild.id)
    if s.admin_role_id:
        role = interaction.guild.get_role(s.admin_role_id)
        if role in interaction.user.roles:
            return True
            
    return False

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

    embed = discord.Embed(title="Sentra Server Config", color=discord.Color.blurple())
    embed.add_field(name="Admin Role", value=fmt_role(s.admin_role_id), inline=False)
    embed.add_field(name="Mentor Role", value=fmt_role(s.mentor_role_id), inline=False)
    embed.add_field(name="Ticket Support Role", value=fmt_role(s.ticket_support_role_id), inline=False)
    embed.add_field(name="Ticket Category", value=f"<#{s.ticket_category_id}>" if s.ticket_category_id else "Not set", inline=False)
    embed.add_field(name="Staff Channel", value=fmt_channel(s.staff_channel_id), inline=False)
    embed.add_field(name="Find Teammates Channel", value=fmt_channel(s.find_teammates_channel_id), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@sentra.command(name="create_admin_role", description="Create a dedicated admin role for the server")
async def create_admin_role(interaction: discord.Interaction, name: str = "Sentra Admin"):
    # Only the server owner or an existing admin can run this
    if not is_admin_or_owner(interaction):
        await interaction.response.send_message("You don't have permission to create the admin role.", ephemeral=True)
        return

    s = get_or_create_settings(interaction.guild.id)
    if s.admin_role_id:
        existing_role = interaction.guild.get_role(s.admin_role_id)
        if existing_role:
            await interaction.response.send_message(f"An admin role already exists: {existing_role.mention}", ephemeral=True)
            return

    # Create the role
    try:
        new_role = await interaction.guild.create_role(
            name=name,
            color=discord.Color.red(),
            reason="Created by Sentra Bot for administration management"
        )
        update_settings(interaction.guild.id, admin_role_id=new_role.id)
        await interaction.response.send_message(f"✅ Created and configured admin role: {new_role.mention}. You can now add users to this role to grant them Sentra admin access.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to create roles (Missing 'Manage Roles').", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to create role: {str(e)}", ephemeral=True)

@sentra.command(name="set_mentor_role", description="Set the mentor role")
async def set_mentor_role(interaction: discord.Interaction, role: discord.Role):
    update_settings(interaction.guild.id, mentor_role_id=role.id)
    await interaction.response.send_message(f"✅ Mentor role set to {role.mention}", ephemeral=True)

@sentra.command(name="set_ticket_support_role", description="Set the role that handles tickets")
async def set_ticket_support_role(interaction: discord.Interaction, role: discord.Role):
    update_settings(interaction.guild.id, ticket_support_role_id=role.id)
    await interaction.response.send_message(f"✅ Ticket support role set to {role.mention}", ephemeral=True)

@sentra.command(name="set_find_teammates_channel", description="Set the channel used for find-teammates")
async def set_find_teammates_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    update_settings(interaction.guild.id, find_teammates_channel_id=channel.id)
    await interaction.response.send_message(f"✅ Find-teammates channel set to {channel.mention}", ephemeral=True)

@sentra.command(name="set_ticket_category", description="Set the category where new tickets will be created")
async def set_ticket_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    update_settings(interaction.guild.id, ticket_category_id=category.id)
    await interaction.response.send_message(f"✅ Ticket category set to **{category.name}**", ephemeral=True)

@sentra.command(name="set_staff_channel", description="Configure where ticket claim pings are sent")
async def set_staff_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    update_settings(interaction.guild.id, staff_channel_id=channel.id)
    await interaction.response.send_message(f"✅ Staff channel set to {channel.mention}", ephemeral=True)

@sentra.command(name="setup_tickets", description="Post the ticket creation panel in the current channel")
async def setup_tickets(interaction: discord.Interaction):
    s = get_or_create_settings(interaction.guild.id)
    if not s.ticket_category_id:
        await interaction.response.send_message("❌ Please set a ticket category first using `/sentra set_ticket_category`.", ephemeral=True)
        return

    from Bot.Commands.tickets import TicketPanel
    
    embed = discord.Embed(
        title="Sentra Support",
        description="Click the button below to open a private support ticket. Only the support team and administrators will have access to your ticket.",
        color=discord.Color.blue()
    )
    
    view = TicketPanel()
    await interaction.channel.send(embed=embed, view=view)
    
    update_settings(interaction.guild.id, ticket_panel_channel_id=interaction.channel.id)
    await interaction.response.send_message("✅ Ticket panel posted!", ephemeral=True)
