import discord
from discord import app_commands
from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import User, Team
from Bot.DB.settings_store import get_or_create_settings


# ── Helper: build the lobby embed for #find-teammates ──────────────────

def build_lobby_embed(team, members, max_size, guild):
    """Build the lobby card embed for a team."""
    count = len(members)
    status = "FULL 🔒" if count >= max_size else f"{count}/{max_size} Members"

    embed = discord.Embed(
        title=f"🎮 {team.name}",
        description=f"**[{status}]**",
        color=discord.Color.red() if count >= max_size else discord.Color.green()
    )

    creator = guild.get_member(team.creator_id)
    creator_name = creator.display_name if creator else "Unknown"
    embed.set_footer(text=f"Created by {creator_name}")

    member_lines = []
    for m in members:
        discord_member = guild.get_member(m.discord_id)
        name = discord_member.display_name if discord_member else f"User {m.discord_id}"
        rd = m.resume_data or {}
        skills = rd.get('skills', [])
        exp = rd.get('experience', '')
        skill_str = ", ".join(skills) if skills else "No skills set"
        line = f"• **{name}** — {skill_str}"
        if exp:
            line += f" ({exp})"
        member_lines.append(line)

    embed.add_field(
        name="Members",
        value="\n".join(member_lines) if member_lines else "No members yet",
        inline=False
    )
    return embed


# ── Persistent View: "Request to Join" button on lobby card ────────────

class RequestToJoinView(discord.ui.View):
    """Attached to the lobby card in #find-teammates. Persistent."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Request to Join",
        style=discord.ButtonStyle.primary,
        custom_id="team_request_join"
    )
    async def request_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            # Find the team by lobby message ID
            team = db.query(Team).filter(
                Team.lobby_message_id == interaction.message.id
            ).first()

            if not team:
                await interaction.followup.send("❌ This team no longer exists.", ephemeral=True)
                return

            # Check if team is full
            member_count = db.query(User).filter(User.team_id == team.id).count()
            settings = get_or_create_settings(interaction.guild.id)
            max_size = settings.max_team_size or 4

            if member_count >= max_size:
                await interaction.followup.send("❌ This team is currently full.", ephemeral=True)
                return

            # Check if user is verified and has resume
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user:
                await interaction.followup.send("❌ You are not registered. Use `/verify` first.", ephemeral=True)
                return
            if not user.is_verified:
                await interaction.followup.send("❌ You must be verified first.", ephemeral=True)
                return
            if not user.resume_data:
                await interaction.followup.send("❌ Please set up your resume first with `/resume edit`.", ephemeral=True)
                return
            if user.team_id and team.guild_id == interaction.guild.id:
                await interaction.followup.send("❌ You're already on a team. Leave your current team first with `/team leave`.", ephemeral=True)
                return

            # Send the join request to the team's private channel
            team_channel = interaction.guild.get_channel(team.textchanel_id)
            if not team_channel:
                await interaction.followup.send("❌ Team channel not found.", ephemeral=True)
                return

            # Build applicant resume embed
            rd = user.resume_data
            resume_embed = discord.Embed(
                title=f"📩 Join Request: {interaction.user.display_name}",
                color=discord.Color.yellow()
            )
            if interaction.user.avatar:
                resume_embed.set_thumbnail(url=interaction.user.avatar.url)
            resume_embed.add_field(name="About Me", value=rd.get('bio', 'Not set'), inline=False)
            gh = rd.get('github')
            if gh:
                resume_embed.add_field(name="Portfolio", value=gh, inline=False)
            resume_embed.add_field(name="Experience", value=rd.get('experience', 'Not set'), inline=True)
            skills = rd.get('skills', [])
            if skills:
                resume_embed.add_field(name="Skills", value=", ".join(skills), inline=True)

            # Send with approve/decline buttons
            view = ApproveJoinView(applicant_id=interaction.user.id)
            await team_channel.send(embed=resume_embed, view=view)

            await interaction.followup.send(
                f"✅ Request sent to **{team.name}**! The team leader will review your resume.",
                ephemeral=True
            )

        except Exception as e:
            print(f"❌ Request to join error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()


# ── Persistent View: Accept / Decline in team channel ──────────────────

class ApproveJoinView(discord.ui.View):
    """Attached to join requests inside the team channel. Persistent."""

    def __init__(self, applicant_id: int = 0):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(
        label="Accept ✅",
        style=discord.ButtonStyle.success,
        custom_id="team_accept_join"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            # Find the team via the channel
            team = db.query(Team).filter(
                Team.textchanel_id == interaction.channel.id
            ).first()

            if not team:
                await interaction.followup.send("❌ Team not found.", ephemeral=True)
                return

            # Only the creator can accept
            if interaction.user.id != team.creator_id:
                await interaction.followup.send("❌ Only the team leader can accept members.", ephemeral=True)
                return

            # Get the applicant ID from the embed
            embed = interaction.message.embeds[0] if interaction.message.embeds else None
            if not embed or not embed.title:
                await interaction.followup.send("❌ Could not find applicant info.", ephemeral=True)
                return

            # Extract applicant mention from embed title "📩 Join Request: DisplayName"
            # We need to find the user by searching the embed — use the thumbnail avatar
            # or better: search for unmatched users whose display name matches
            # Safer approach: store applicant_id in the custom_id or find from DB
            applicant_name = embed.title.replace("📩 Join Request: ", "")

            # Find the applicant — search guild members by display name
            applicant_member = discord.utils.find(
                lambda m: m.display_name == applicant_name,
                interaction.guild.members
            )
            if not applicant_member:
                await interaction.followup.send(f"❌ Could not find user **{applicant_name}** in this server.", ephemeral=True)
                return

            applicant = db.query(User).filter(User.discord_id == applicant_member.id, User.guild_id == interaction.guild.id).first()
            if not applicant:
                await interaction.followup.send("❌ Applicant is not registered.", ephemeral=True)
                return

            if applicant.team_id:
                await interaction.followup.send("❌ This user already joined another team.", ephemeral=True)
                # Disable buttons on this message
                await interaction.message.edit(view=None, content="~~Request~~ — User joined another team.")
                return

            # Check team is not full
            member_count = db.query(User).filter(User.team_id == team.id).count()
            settings = get_or_create_settings(interaction.guild.id)
            max_size = settings.max_team_size or 4

            if member_count >= max_size:
                await interaction.followup.send("❌ Team is already full. This request has expired.", ephemeral=True)
                await interaction.message.edit(view=None, content="~~Request~~ — Team is full.")
                return

            # Accept the user
            applicant.team_id = team.id
            db.commit()

            # Grant channel permissions
            text_ch = interaction.guild.get_channel(team.textchanel_id)
            voice_ch = interaction.guild.get_channel(team.voicechanel_id)
            if text_ch:
                await text_ch.set_permissions(applicant_member, read_messages=True, send_messages=True)
            if voice_ch:
                await voice_ch.set_permissions(applicant_member, connect=True, speak=True)

            # Update the request message
            await interaction.message.edit(
                view=None,
                content=f"✅ **{applicant_member.display_name}** has been accepted!"
            )

            # Send welcome in the team channel
            await interaction.channel.send(
                f"🎉 Welcome {applicant_member.mention} to **{team.name}**!"
            )

            # Update the lobby card
            new_count = member_count + 1
            is_full = new_count >= max_size
            if is_full:
                team.full_team = True
                db.commit()

            await _update_lobby_card(interaction.guild, team, db, max_size)

            await interaction.followup.send("✅ Member accepted!", ephemeral=True)

        except Exception as e:
            print(f"❌ Accept join error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()

    @discord.ui.button(
        label="Decline ❌",
        style=discord.ButtonStyle.danger,
        custom_id="team_decline_join"
    )
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            team = db.query(Team).filter(
                Team.textchanel_id == interaction.channel.id
            ).first()

            if not team:
                await interaction.followup.send("❌ Team not found.", ephemeral=True)
                return

            if interaction.user.id != team.creator_id:
                await interaction.followup.send("❌ Only the team leader can decline members.", ephemeral=True)
                return

            # Get applicant name from embed
            embed = interaction.message.embeds[0] if interaction.message.embeds else None
            if not embed or not embed.title:
                await interaction.followup.send("❌ Could not find applicant info.", ephemeral=True)
                return

            applicant_name = embed.title.replace("📩 Join Request: ", "")

            # Try to DM the applicant
            applicant_member = discord.utils.find(
                lambda m: m.display_name == applicant_name,
                interaction.guild.members
            )
            if applicant_member:
                try:
                    await applicant_member.send(
                        f"Your request to join **{team.name}** was declined."
                    )
                except discord.Forbidden:
                    pass  # Can't DM user, that's OK

            # Update the request message
            await interaction.message.edit(
                view=None,
                content=f"❌ **{applicant_name}**'s request was declined."
            )

            await interaction.followup.send("✅ Request declined.", ephemeral=True)

        except Exception as e:
            print(f"❌ Decline join error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()


# ── Helper: update the lobby card embed ────────────────────────────────

async def _update_lobby_card(guild, team, db, max_size):
    """Refresh the lobby card in #find-teammates with current members."""
    settings = get_or_create_settings(guild.id)
    find_ch = guild.get_channel(settings.find_teammates_channel_id)
    if not find_ch or not team.lobby_message_id:
        return

    members = db.query(User).filter(User.team_id == team.id).all()
    embed = build_lobby_embed(team, members, max_size, guild)

    try:
        msg = await find_ch.fetch_message(team.lobby_message_id)
        is_full = len(members) >= max_size

        if is_full:
            # Disable the join button
            view = RequestToJoinView()
            view.children[0].disabled = True
            view.children[0].label = "FULL 🔒"
            view.children[0].style = discord.ButtonStyle.secondary
            await msg.edit(embed=embed, view=view)
        else:
            await msg.edit(embed=embed, view=RequestToJoinView())
    except discord.NotFound:
        pass  # Message was deleted


# ── Team command group ─────────────────────────────────────────────────

TEAM_NAMES = [
    "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot",
    "Ghost", "Havoc", "Iron", "Jade", "Knight", "Luna",
    "Maverick", "Nova", "Omega", "Phoenix", "Quantum", "Raven",
    "Shadow", "Titan", "Ultra", "Viper", "Wraith", "Xenon",
    "Zenith"
]


class TeamCmds(app_commands.Group):
    def __init__(self):
        super().__init__(name="team", description="Team management commands")

    # ── /team create ───────────────────────────────────────────────────

    @app_commands.command(name="create", description="Create a new team and post a lobby card")
    async def create_team(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            # Validate user
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user:
                await interaction.followup.send("❌ You are not registered.", ephemeral=True)
                return
            if not user.is_verified:
                await interaction.followup.send("❌ You must be verified first.", ephemeral=True)
                return
            if not user.resume_data:
                await interaction.followup.send("❌ Please set up your resume first with `/resume edit`.", ephemeral=True)
                return
            if user.team_id:
                await interaction.followup.send("❌ You're already on a team. Leave first with `/team leave`.", ephemeral=True)
                return

            # Validate guild settings
            settings = get_or_create_settings(interaction.guild.id)
            if not settings.team_category_id:
                await interaction.followup.send("❌ No team category configured. Ask an admin to run `/sentra set_team_category`.", ephemeral=True)
                return
            if not settings.find_teammates_channel_id:
                await interaction.followup.send("❌ No find-teammates channel configured. Ask an admin to run `/sentra set_find_teammates_channel`.", ephemeral=True)
                return

            category = interaction.guild.get_channel(settings.team_category_id)
            if not category:
                await interaction.followup.send("❌ Team category channel not found.", ephemeral=True)
                return

            max_size = settings.max_team_size or 4
            safe_name = name[:50].strip()

            # Create the team row
            team = Team(
                name=safe_name,
                guild_id=interaction.guild.id,
                creator_id=interaction.user.id,
                full_team=False
            )
            db.add(team)
            db.commit()
            db.refresh(team)

            # Create private channels
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            voice_overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
                interaction.guild.me: discord.PermissionOverwrite(connect=True, speak=True),
                interaction.user: discord.PermissionOverwrite(connect=True, speak=True)
            }

            channel_name = f"team-{safe_name.lower().replace(' ', '-')}"
            text_ch = await interaction.guild.create_text_channel(
                channel_name, category=category, overwrites=overwrites,
                reason=f"Team created by {interaction.user}"
            )
            voice_ch = await interaction.guild.create_voice_channel(
                f"{channel_name}-vc", category=category, overwrites=voice_overwrites,
                reason=f"Team voice channel for {safe_name}"
            )

            team.textchanel_id = text_ch.id
            team.voicechanel_id = voice_ch.id

            # Assign creator to team
            user.team_id = team.id
            db.commit()

            # Post lobby card in #find-teammates
            find_ch = interaction.guild.get_channel(settings.find_teammates_channel_id)
            members = [user]
            embed = build_lobby_embed(team, members, max_size, interaction.guild)
            view = RequestToJoinView()
            lobby_msg = await find_ch.send(embed=embed, view=view)

            team.lobby_message_id = lobby_msg.id
            db.commit()

            # Welcome message in team channel
            await text_ch.send(
                f"🎮 Welcome to **{safe_name}**!\n\n"
                f"**Team Leader:** {interaction.user.mention}\n"
                f"**Max Size:** {max_size}\n\n"
                f"Join requests from other users will appear here. "
                f"Use **Accept ✅** or **Decline ❌** to manage your roster."
            )

            await interaction.followup.send(
                f"✅ Team **{safe_name}** created!\n"
                f"📝 Text channel: {text_ch.mention}\n"
                f"🔊 Voice channel: {voice_ch.mention}\n"
                f"📩 Lobby card posted in {find_ch.mention}",
                ephemeral=True
            )

        except Exception as e:
            print(f"❌ Team create error: {e}")
            await interaction.followup.send(f"❌ Error creating team: {str(e)}", ephemeral=True)
        finally:
            db.close()

    # ── /team leave ────────────────────────────────────────────────────

    @app_commands.command(name="leave", description="Leave your current team")
    async def leave_team(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user or not user.team_id:
                await interaction.followup.send("❌ You're not on a team.", ephemeral=True)
                return

            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                user.team_id = None
                db.commit()
                await interaction.followup.send("❌ Team not found. You've been unassigned.", ephemeral=True)
                return

            team_name = team.name
            settings = get_or_create_settings(interaction.guild.id)
            max_size = settings.max_team_size or 4

            # Remove user from team
            user.team_id = None
            db.commit()

            # Remove channel permissions
            text_ch = interaction.guild.get_channel(team.textchanel_id)
            voice_ch = interaction.guild.get_channel(team.voicechanel_id)
            if text_ch:
                await text_ch.set_permissions(interaction.user, overwrite=None)
            if voice_ch:
                await voice_ch.set_permissions(interaction.user, overwrite=None)

            # Check if creator left — transfer or disband
            if interaction.user.id == team.creator_id:
                remaining = db.query(User).filter(User.team_id == team.id).all()
                if remaining:
                    # Transfer to first remaining member
                    new_leader = remaining[0]
                    team.creator_id = new_leader.discord_id
                    db.commit()

                    new_leader_member = interaction.guild.get_member(new_leader.discord_id)
                    if text_ch and new_leader_member:
                        await text_ch.send(
                            f"👑 {interaction.user.mention} left. "
                            f"**{new_leader_member.display_name}** is now the team leader!"
                        )
                else:
                    # No one left — disband
                    await _disband_team(team, interaction.guild, db)
                    await interaction.followup.send(f"✅ You left **{team_name}**. The team was disbanded (no members remaining).", ephemeral=True)
                    return
            else:
                if text_ch:
                    await text_ch.send(f"📤 **{interaction.user.display_name}** has left the team.")

            # If team was full, re-open the lobby
            if team.full_team:
                team.full_team = False
                db.commit()

            await _update_lobby_card(interaction.guild, team, db, max_size)
            await interaction.followup.send(f"✅ You left **{team_name}**.", ephemeral=True)

        except Exception as e:
            print(f"❌ Team leave error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()

    # ── /team kick ─────────────────────────────────────────────────────

    @app_commands.command(name="kick", description="Kick a member from your team (leader only)")
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user or not user.team_id:
                await interaction.followup.send("❌ You're not on a team.", ephemeral=True)
                return

            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                await interaction.followup.send("❌ Team not found.", ephemeral=True)
                return

            if interaction.user.id != team.creator_id:
                await interaction.followup.send("❌ Only the team leader can kick members.", ephemeral=True)
                return

            if member.id == interaction.user.id:
                await interaction.followup.send("❌ You can't kick yourself. Use `/team leave` instead.", ephemeral=True)
                return

            target = db.query(User).filter(User.discord_id == member.id, User.guild_id == interaction.guild.id).first()
            if not target or target.team_id != team.id:
                await interaction.followup.send(f"❌ {member.display_name} is not on your team.", ephemeral=True)
                return

            # Remove from team
            target.team_id = None
            db.commit()

            # Remove channel permissions
            text_ch = interaction.guild.get_channel(team.textchanel_id)
            voice_ch = interaction.guild.get_channel(team.voicechanel_id)
            if text_ch:
                await text_ch.set_permissions(member, overwrite=None)
                await text_ch.send(f"🚫 **{member.display_name}** has been removed from the team.")
            if voice_ch:
                await voice_ch.set_permissions(member, overwrite=None)

            # Notify kicked user via DM
            try:
                await member.send(f"You have been removed from **{team.name}**.")
            except discord.Forbidden:
                pass

            # Re-open lobby if was full
            if team.full_team:
                team.full_team = False
                db.commit()

            settings = get_or_create_settings(interaction.guild.id)
            max_size = settings.max_team_size or 4
            await _update_lobby_card(interaction.guild, team, db, max_size)

            await interaction.followup.send(f"✅ Kicked **{member.display_name}** from the team.", ephemeral=True)

        except Exception as e:
            print(f"❌ Team kick error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()

    # ── /team info ─────────────────────────────────────────────────────

    @app_commands.command(name="info", description="View your current team's info")
    async def team_info(self, interaction: discord.Interaction):
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user or not user.team_id:
                await interaction.response.send_message("❌ You're not on a team.", ephemeral=True)
                return

            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                await interaction.response.send_message("❌ Team not found.", ephemeral=True)
                return

            settings = get_or_create_settings(interaction.guild.id)
            max_size = settings.max_team_size or 4
            members = db.query(User).filter(User.team_id == team.id).all()

            embed = discord.Embed(
                title=f"🎮 {team.name}",
                color=discord.Color.blue()
            )

            creator = interaction.guild.get_member(team.creator_id)
            embed.add_field(
                name="Team Leader",
                value=creator.mention if creator else "Unknown",
                inline=True
            )
            embed.add_field(name="Members", value=f"{len(members)}/{max_size}", inline=True)

            text_ch = interaction.guild.get_channel(team.textchanel_id)
            voice_ch = interaction.guild.get_channel(team.voicechanel_id)
            embed.add_field(
                name="Channels",
                value=f"💬 {text_ch.mention if text_ch else 'N/A'}\n🔊 {voice_ch.mention if voice_ch else 'N/A'}",
                inline=False
            )

            member_lines = []
            for m in members:
                dm = interaction.guild.get_member(m.discord_id)
                name = dm.display_name if dm else f"User {m.discord_id}"
                rd = m.resume_data or {}
                skills = rd.get('skills', [])
                skill_str = ", ".join(skills) if skills else "No skills"
                leader_tag = " 👑" if m.discord_id == team.creator_id else ""
                member_lines.append(f"• **{name}**{leader_tag} — {skill_str}")

            embed.add_field(
                name="Roster",
                value="\n".join(member_lines),
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"❌ Team info error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()

    # ── /team disband ──────────────────────────────────────────────────

    @app_commands.command(name="disband", description="Disband your team (leader only)")
    async def disband_team(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user or not user.team_id:
                await interaction.followup.send("❌ You're not on a team.", ephemeral=True)
                return

            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                await interaction.followup.send("❌ Team not found.", ephemeral=True)
                return

            if interaction.user.id != team.creator_id:
                await interaction.followup.send("❌ Only the team leader can disband the team.", ephemeral=True)
                return

            team_name = team.name
            await _disband_team(team, interaction.guild, db)

            await interaction.followup.send(f"✅ Team **{team_name}** has been disbanded.", ephemeral=True)

        except Exception as e:
            print(f"❌ Team disband error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()


# ── Helper: full disband logic ─────────────────────────────────────────

async def _disband_team(team, guild, db):
    """Delete team channels, remove all members, delete lobby card."""
    # Clear all member assignments
    members = db.query(User).filter(User.team_id == team.id).all()
    for m in members:
        m.team_id = None
    db.commit()

    # Delete channels
    text_ch = guild.get_channel(team.textchanel_id)
    voice_ch = guild.get_channel(team.voicechanel_id)
    if text_ch:
        await text_ch.delete(reason=f"Team {team.name} disbanded")
    if voice_ch:
        await voice_ch.delete(reason=f"Team {team.name} disbanded")

    # Delete lobby card
    settings = get_or_create_settings(guild.id)
    find_ch = guild.get_channel(settings.find_teammates_channel_id)
    if find_ch and team.lobby_message_id:
        try:
            msg = await find_ch.fetch_message(team.lobby_message_id)
            await msg.delete()
        except discord.NotFound:
            pass

    # Delete team row
    db.delete(team)
    db.commit()


team_cmds = TeamCmds()
