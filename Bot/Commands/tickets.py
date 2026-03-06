import discord
import time
import asyncio
from discord import app_commands
from Bot.DB.settings_store import get_or_create_settings, update_settings
from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import Ticket

class TicketActions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.secondary, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if the channel is a ticket
        db = get_session()
        try:
            ticket = db.query(Ticket).filter(Ticket.channel_id == interaction.channel.id).first()
            if not ticket:
                await interaction.followup.send("This doesn't seem to be a managed ticket channel.", ephemeral=True)
                return

            if ticket.status == 'closed':
                await interaction.followup.send("This ticket is already closed.", ephemeral=True)
                return

            ticket.status = 'closed'
            db.commit()

            await interaction.channel.send("🔒 **Ticket closed.** This channel will be deleted in 10 seconds.")
            
            # Wait and delete
            await asyncio.sleep(10)
            
        finally:
            db.close()
            try:
                await interaction.channel.delete(reason="Ticket closed")
            except:
                pass

class StaffClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim 🚩", style=discord.ButtonStyle.success, custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        db = get_session()
        try:
            ticket = db.query(Ticket).filter(Ticket.staff_message_id == interaction.message.id).first()
            if not ticket:
                await interaction.followup.send("Ticket not found in DB.", ephemeral=True)
                return
                
            if ticket.claimed_by:
                await interaction.followup.send("This ticket is already claimed.", ephemeral=True)
                return

            ticket.claimed_by = interaction.user.id
            db.commit()

            ticket_channel = interaction.guild.get_channel(ticket.channel_id)
            if ticket_channel:
                await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_message_history=True)
                await ticket_channel.send(f"🚩 {interaction.user.mention} has claimed this ticket and will be assisting you shortly.")
                
                # Update initial message in the ticket channel
                async for msg in ticket_channel.history(limit=5, oldest_first=True):
                    if msg.author == interaction.guild.me and msg.embeds and msg.components:
                        embed = msg.embeds[0]
                        embed.color = discord.Color.orange()
                        
                        found = False
                        for i, field in enumerate(embed.fields):
                            if field.name == "Claimed By":
                                embed.set_field_at(i, name="Claimed By", value=interaction.user.mention, inline=False)
                                found = True
                                break
                        if not found:
                            embed.add_field(name="Claimed By", value=interaction.user.mention, inline=False)
                        
                        await msg.edit(embed=embed)
                        break

            # Update the original staff message
            button.label = f"Claimed by {interaction.user.display_name}"
            button.style = discord.ButtonStyle.secondary
            button.disabled = True
            
            embed_staff = interaction.message.embeds[0]
            embed_staff.color = discord.Color.orange()
            
            # Prepend claimed user to description
            if "**Claimed by:**" not in embed_staff.description:
                embed_staff.description = f"**Claimed by:** {interaction.user.mention}\n\n{embed_staff.description}"
            
            await interaction.message.edit(embed=embed_staff, view=self)

        except Exception as e:
            await interaction.followup.send(f"Error claiming ticket: {str(e)}", ephemeral=True)
        finally:
            db.close()

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        
        s = get_or_create_settings(guild_id)
        if not s.ticket_category_id:
            await interaction.followup.send("❌ The ticketing system is not configured yet (Category missing).", ephemeral=True)
            return

        # 1. Rate Limiting: Check if user already has an open ticket
        db = get_session()
        try:
            existing_ticket = db.query(Ticket).filter(
                Ticket.guild_id == guild_id,
                Ticket.user_id == user_id,
                Ticket.status == 'open'
            ).first()

            if existing_ticket:
                await interaction.followup.send("❌ You already have an open ticket!", ephemeral=True)
                return

            # 2. Create private channel
            category = interaction.guild.get_channel(s.ticket_category_id)
            if not category:
                await interaction.followup.send("❌ Ticket category not found. Please contact an admin.", ephemeral=True)
                return

            # Permissions
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            }
            
            # We no longer add the support role automatically to ensure claiming is required.

            ticket_channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket opened by {interaction.user}"
            )

            # Send notification to staff channel
            staff_message_id = None
            if s.staff_channel_id:
                staff_channel = interaction.guild.get_channel(s.staff_channel_id)
                if staff_channel:
                    embed_staff = discord.Embed(
                        title="New Ticket 🚩",
                        description=f"Ticket opened by {interaction.user.mention}\nChannel: {ticket_channel.mention}",
                        color=discord.Color.red()
                    )
                    
                    # Ping the support role if configured (optional but helpful)
                    content = ""
                    if s.ticket_support_role_id:
                        content = f"<@&{s.ticket_support_role_id}>"
                        
                    staff_msg = await staff_channel.send(content=content, embed=embed_staff, view=StaffClaimView())
                    staff_message_id = staff_msg.id

            # 3. Save to database
            new_ticket = Ticket(
                guild_id=guild_id,
                user_id=user_id,
                channel_id=ticket_channel.id,
                status='open',
                created_at=int(time.time()),
                staff_message_id=staff_message_id
            )
            db.add(new_ticket)
            db.commit()

            # 4. Success message in ticket channel
            embed = discord.Embed(
                title="Ticket Created",
                description=f"Welcome {interaction.user.mention}! Please describe your issue and wait for the support team.",
                color=discord.Color.green()
            )
            await ticket_channel.send(content=f"{interaction.user.mention} Support team will be with you shortly.", embed=embed, view=TicketActions())
            
            await interaction.followup.send(f"✅ Ticket created! Head over to {ticket_channel.mention}", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to create ticket: {str(e)}", ephemeral=True)
        finally:
            db.close()
