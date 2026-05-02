import discord
from discord import app_commands
from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import User
from sqlalchemy.orm.attributes import flag_modified

VALID_SKILLS = [
    "Frontend", "Backend", "Fullstack", "UI/UX Design",
    "Machine Learning / AI", "Data Science", "Mobile Dev",
    "Game Dev", "Cloud / DevOps", "Hardware / IoT"
]

class ResumeModal(discord.ui.Modal, title='Edit Your Resume'):
    bio = discord.ui.TextInput(
        label='About Me',
        style=discord.TextStyle.paragraph,
        placeholder='A short bio about yourself and your goals...',
        required=True,
        max_length=500
    )
    github = discord.ui.TextInput(
        label='GitHub / Portfolio Link',
        style=discord.TextStyle.short,
        placeholder='https://github.com/yourusername',
        required=False,
        max_length=150
    )
    experience = discord.ui.TextInput(
        label='Experience Level',
        style=discord.TextStyle.short,
        placeholder='Beginner, Intermediate, or Advanced',
        required=True,
        max_length=50
    )
    skills = discord.ui.TextInput(
        label='Skills (comma-separated, up to 5)',
        style=discord.TextStyle.paragraph,
        placeholder='e.g. Frontend, Backend, UI/UX Design, ML/AI, Mobile Dev',
        required=True,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user:
                await interaction.followup.send("❌ You are not registered.", ephemeral=True)
                return

            # Parse and validate skills
            raw_skills = [s.strip() for s in self.skills.value.split(",") if s.strip()]
            if len(raw_skills) > 5:
                await interaction.followup.send("❌ Please select a maximum of 5 skills.", ephemeral=True)
                return

            resume_data = user.resume_data or {}
            resume_data['bio'] = self.bio.value
            resume_data['github'] = self.github.value
            resume_data['experience'] = self.experience.value
            resume_data['skills'] = raw_skills

            # Force SQLAlchemy to detect the JSONB mutation
            user.resume_data = resume_data
            flag_modified(user, 'resume_data')
            db.commit()

            skills_str = ", ".join(raw_skills)
            await interaction.followup.send(
                f"✅ Resume updated!\n**Bio:** {self.bio.value[:80]}...\n**Experience:** {self.experience.value}\n**Skills:** {skills_str}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Error saving resume: {str(e)}", ephemeral=True)
        finally:
            db.close()


class ResumeCmds(app_commands.Group):
    def __init__(self):
        super().__init__(name="resume", description="Manage your matchmaking resume")

    @app_commands.command(name="edit", description="Edit your matchmaking resume details")
    async def edit_resume(self, interaction: discord.Interaction):
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id, User.guild_id == interaction.guild.id).first()
            if not user:
                await interaction.response.send_message("❌ You are not registered in the database.", ephemeral=True)
                return
            if not user.is_verified:
                await interaction.response.send_message("❌ You must be verified first before setting up a resume.", ephemeral=True)
                return

            # Pre-fill the modal with existing data
            resume_data = user.resume_data or {}
            modal = ResumeModal()
            modal.bio.default = resume_data.get('bio', '')
            modal.github.default = resume_data.get('github', '')
            modal.experience.default = resume_data.get('experience', '')
            existing_skills = resume_data.get('skills', [])
            modal.skills.default = ", ".join(existing_skills)

            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"❌ /resume edit error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()

    @app_commands.command(name="view", description="View a user's resume")
    async def view_resume(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        db = get_session()
        try:
            user = db.query(User).filter(User.discord_id == target.id, User.guild_id == interaction.guild.id).first()
            if not user or not user.resume_data:
                await interaction.response.send_message(f"❌ {target.mention} hasn't set up their resume yet.", ephemeral=True)
                return

            rd = user.resume_data
            embed = discord.Embed(title=f"{target.display_name}'s Resume", color=discord.Color.brand_green())
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)

            embed.add_field(name="About Me", value=rd.get('bio', 'Not set'), inline=False)

            gh = rd.get('github')
            if gh:
                embed.add_field(name="Portfolio", value=gh, inline=False)

            embed.add_field(name="Experience Level", value=rd.get('experience', 'Not set'), inline=True)

            skills = rd.get('skills', [])
            if skills:
                embed.add_field(name="Top Skills", value=", ".join(skills), inline=True)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"❌ /resume view error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            db.close()

resume_cmds = ResumeCmds()
