import discord
from discord import app_commands
from Bot.DB.settings_store import get_or_create_settings, update_settings
from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import Infraction

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

async def sync_staff_permissions(guild: discord.Guild, s):
    """Helper to sync permissions for the staff channel and category."""
    admin_role = guild.get_role(s.admin_role_id) if s.admin_role_id else None
    support_role = guild.get_role(s.ticket_support_role_id) if s.ticket_support_role_id else None
    
    # 1. Update Staff Channel
    if s.staff_channel_id:
        channel = guild.get_channel(s.staff_channel_id)
        if channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True)
            }
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(view_channel=True)
            
            try:
                await channel.edit(overwrites=overwrites)
            except discord.Forbidden:
                pass

    # 2. Update Staff Category (if the channel is in one)
    if s.staff_channel_id:
        channel = guild.get_channel(s.staff_channel_id)
        if channel and channel.category:
            cat = channel.category
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True)
            }
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(view_channel=True)
            
            try:
                await cat.edit(overwrites=overwrites)
            except discord.Forbidden:
                pass

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
    embed.add_field(name="Team Category", value=f"**{interaction.guild.get_channel(s.team_category_id).name}**" if s.team_category_id and interaction.guild.get_channel(s.team_category_id) else "Not set", inline=False)
    embed.add_field(name="Max Team Size", value=str(s.max_team_size or 4), inline=False)

    # Moderation settings
    embed.add_field(name="──── Moderation ────", value="\u200b", inline=False)
    embed.add_field(name="Mod Channel", value=fmt_channel(s.mod_channel_id), inline=False)
    
    threshold_val = s.mod_toxicity_threshold if s.mod_toxicity_threshold is not None else 0.7
    embed.add_field(name="Toxicity Threshold", value=str(threshold_val), inline=False)

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

@sentra.command(name="set_ticket_support_role", description="Set the role that handles tickets (automatically grants access to staff channel)")
async def set_ticket_support_role(interaction: discord.Interaction, role: discord.Role):
    update_settings(interaction.guild.id, ticket_support_role_id=role.id)
    s = get_or_create_settings(interaction.guild.id)
    await sync_staff_permissions(interaction.guild, s)
    await interaction.response.send_message(f"✅ Ticket support role set to {role.mention} and permissions synced.", ephemeral=True)

@sentra.command(name="set_find_teammates_channel", description="Set the channel used for find-teammates")
async def set_find_teammates_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    update_settings(interaction.guild.id, find_teammates_channel_id=channel.id)
    await interaction.response.send_message(f"✅ Find-teammates channel set to {channel.mention}", ephemeral=True)

@sentra.command(name="set_team_category", description="Set the category where team channels are created")
async def set_team_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    update_settings(interaction.guild.id, team_category_id=category.id)
    await interaction.response.send_message(f"✅ Team category set to **{category.name}**", ephemeral=True)

@sentra.command(name="set_max_team_size", description="Set the max number of members per team")
async def set_max_team_size(interaction: discord.Interaction, size: int):
    if size < 2 or size > 10:
        await interaction.response.send_message("❌ Team size must be between 2 and 10.", ephemeral=True)
        return
    update_settings(interaction.guild.id, max_team_size=size)
    await interaction.response.send_message(f"✅ Max team size set to **{size}**", ephemeral=True)

@sentra.command(name="set_ticket_category", description="Set the category where new tickets will be created")
async def set_ticket_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    update_settings(interaction.guild.id, ticket_category_id=category.id)
    await interaction.response.send_message(f"✅ Ticket category set to **{category.name}**", ephemeral=True)

@sentra.command(name="set_staff_channel", description="Configure where ticket claim pings are sent")
async def set_staff_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    update_settings(interaction.guild.id, staff_channel_id=channel.id)
    s = get_or_create_settings(interaction.guild.id)
    await sync_staff_permissions(interaction.guild, s)
    await interaction.response.send_message(f"✅ Staff channel set to {channel.mention} and permissions synced.", ephemeral=True)

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

@sentra.command(name="quick_setup", description="Auto-create all essential roles, categories, and channels for Sentra")
async def quick_setup(interaction: discord.Interaction):
    # Only the server owner or an existing admin can run this
    if not is_admin_or_owner(interaction):
        await interaction.response.send_message("You don't have permission to run quick setup.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    try:
        # --- Roles ---
        admin_role = await guild.create_role(name="Sentra Admin", color=discord.Color.red(), reason="Sentra Quick Setup")
        mentor_role = await guild.create_role(name="Mentor", color=discord.Color.gold(), reason="Sentra Quick Setup")
        support_role = await guild.create_role(name="Support Team", color=discord.Color.blue(), reason="Sentra Quick Setup")
        
        # --- Categories ---
        # Admin-only overwrites
        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            admin_role: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        
        # Staff (Admin + Support)
        staff_cat_overwrites = admin_overwrites.copy()
        staff_cat_overwrites[support_role] = discord.PermissionOverwrite(view_channel=True)

        ticket_cat = await guild.create_category(name="🎫 Support Tickets", overwrites=admin_overwrites, reason="Sentra Quick Setup")
        team_cat = await guild.create_category(name="🚀 Hackathon Teams", reason="Sentra Quick Setup")
        staff_cat = await guild.create_category(name="🛡️ Sentra Staff", overwrites=staff_cat_overwrites, reason="Sentra Quick Setup")
        
        # --- Channels ---
        find_teammates = await guild.create_text_channel(name="find-teammates", reason="Sentra Quick Setup")
        
        # Support channel for the panel
        support_channel = await guild.create_text_channel(name="support", reason="Sentra Quick Setup")
        
        # Automatically post the panel
        from Bot.Commands.tickets import TicketPanel
        panel_embed = discord.Embed(
            title="Sentra Support",
            description="Click the button below to open a private support ticket. Only the support team and administrators will have access to your ticket.",
            color=discord.Color.blue()
        )
        await support_channel.send(embed=panel_embed, view=TicketPanel())
        
        # Staff alerts inherits from staff_cat
        staff_channel = await guild.create_text_channel(name="staff-alerts", category=staff_cat, reason="Sentra Quick Setup")
        
        # Mod logs overrides staff_cat to hide it from Support role
        mod_overwrites = admin_overwrites.copy()
        mod_overwrites[support_role] = discord.PermissionOverwrite(view_channel=False)
        mod_channel = await guild.create_text_channel(name="mod-logs", category=staff_cat, overwrites=mod_overwrites, reason="Sentra Quick Setup")
        
        # --- Save to DB ---
        update_settings(
            guild.id,
            admin_role_id=admin_role.id,
            mentor_role_id=mentor_role.id,
            ticket_support_role_id=support_role.id,
            ticket_category_id=ticket_cat.id,
            team_category_id=team_cat.id,
            staff_channel_id=staff_channel.id,
            find_teammates_channel_id=find_teammates.id,
            ticket_panel_channel_id=support_channel.id,
            mod_channel_id=mod_channel.id
        )
        
        await interaction.followup.send("✅ **Quick Setup Complete!** All essential roles, categories, and channels have been created. The ticket panel has been posted in " + support_channel.mention + "!")
        
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have the required permissions (`Manage Channels` & `Manage Roles`) to run quick setup.")
    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred during setup: {str(e)}")

# ─── Moderation Commands ─────────────────────────────────────────────────────

@sentra.command(name="set_mod_channel", description="Set the channel where moderation logs are posted (enables auto-mod)")
async def set_mod_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    update_settings(interaction.guild.id, mod_channel_id=channel.id)
    await interaction.response.send_message(
        f"✅ Mod log channel set to {channel.mention}. Auto-moderation is now **enabled**.",
        ephemeral=True,
    )

@sentra.command(name="set_toxicity_threshold", description="Set the toxicity sensitivity (0.0-1.0, lower = stricter)")
async def set_toxicity_threshold(interaction: discord.Interaction, value: float):
    if value < 0.0 or value > 1.0:
        await interaction.response.send_message(
            "❌ Threshold must be between 0.0 and 1.0.", ephemeral=True
        )
        return
    update_settings(interaction.guild.id, mod_toxicity_threshold=value)
    await interaction.response.send_message(
        f"✅ Toxicity threshold set to **{value}**.", ephemeral=True
    )

@sentra.command(name="view_infractions", description="View infraction history for a user")
async def view_infractions(interaction: discord.Interaction, user: discord.User):
    db = get_session()
    try:
        infractions = (
            db.query(Infraction)
            .filter(
                Infraction.guild_id == interaction.guild.id,
                Infraction.user_id == user.id,
            )
            .order_by(Infraction.created_at.desc())
            .limit(10)
            .all()
        )
    finally:
        db.close()

    if not infractions:
        await interaction.response.send_message(
            f"✅ No infractions found for {user.mention}.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"Infractions for {user.display_name}",
        color=discord.Color.orange(),
    )

    for inf in infractions:
        timestamp = f"<t:{inf.created_at}:R>" if inf.created_at else "Unknown"
        keywords_str = ", ".join(inf.keywords) if inf.keywords else "None"
        embed.add_field(
            name=f"{inf.action_taken.upper()} — Score: {inf.toxicity_score:.2f} — {timestamp}",
            value=f"```{inf.message_content[:100]}```Keywords: {keywords_str}",
            inline=False,
        )

    embed.set_footer(text=f"Showing last {len(infractions)} infractions")
    await interaction.response.send_message(embed=embed, ephemeral=True)
