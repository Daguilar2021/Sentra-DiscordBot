# ./Sentra-DiscordBot/Bot/Commands/mod_listener.py
# All listeners for the modConfiguration, handles mod functionality of reading text messages alongside timing out and deleting messages based on toxicity scores.

import time
import asyncio
import functools
from datetime import timedelta

import discord

from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import Infraction
from Bot.DB.settings_store import get_or_create_settings


def setup_mod_listener(bot: discord.ext.commands.Bot, engine):
    """
    Register the on_message moderation listener.
    `engine` is a ModerationEngine instance (already loaded at startup).
    """

    @bot.listen("on_message")
    async def on_message(message: discord.Message):
        # Skip bot messages and DMs
        if message.author.bot or not message.guild:
            return

        print(f"[DEBUG] Received message from {message.author.display_name}: '{message.content}'")

        # Skip empty messages (images-only, embeds, etc.)
        if not message.content or not message.content.strip():
            return

        # Check if guild has moderation enabled
        settings = get_or_create_settings(message.guild.id)
        if not settings.mod_channel_id:
            return

        threshold = settings.mod_toxicity_threshold or 0.7

        # Run the blocking model inference in a thread executor
        start_time = time.perf_counter()
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            functools.partial(engine.analyze, message.content),
        )
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000  # convert to milliseconds

        print(f"[DEBUG] Model returned toxicity score: {result['score']:.4f} (Threshold is {threshold})")

        if not result["toxic"] or result["score"] < threshold:
            return

        score = result["score"]
        keywords = result["keywords"]

        # --- Determine action based on score ---
        if score >= threshold + 0.25:
            action = "timeout"
        elif score >= threshold + 0.15:
            action = "delete"
        else:
            action = "warn"

        # --- Execute action ---
        try:
            if action in ("delete", "timeout"):
                await message.delete()

            if action == "timeout":
                try:
                    await message.author.timeout(
                        timedelta(minutes=5),
                        reason=f"Auto-mod: toxicity score {score}",
                    )
                except discord.Forbidden:
                    pass  # bot lacks permission to timeout this user

            if action == "warn":
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass

            # Send ephemeral-style warning to user via DM (ephemeral not possible on on_message)
            try:
                await message.author.send(
                    f"⚠️ Your message in **{message.guild.name}** was flagged by auto-moderation "
                    f"(score: {score:.2f}). Please keep the chat respectful."
                )
            except discord.Forbidden:
                pass  # DMs disabled

        except Exception as e:
            print(f"❌ Mod action failed: {e}")

        # --- Log infraction to DB ---
        try:
            db = get_session()
            infraction = Infraction(
                guild_id=message.guild.id,
                user_id=message.author.id,
                message_content=message.content[:2000],
                toxicity_score=score,
                keywords=keywords,
                action_taken=action,
                created_at=int(time.time()),
                reviewed=False,
            )
            db.add(infraction)
            db.commit()
            db.close()
        except Exception as e:
            print(f"❌ Failed to log infraction: {e}")

        # --- Post mod log embed ---
        try:
            mod_channel = message.guild.get_channel(settings.mod_channel_id)
            if not mod_channel:
                return

            # Score color coding
            if score >= 0.95:
                color = discord.Color.dark_red()
                severity = "🔴 Critical"
            elif score >= 0.85:
                color = discord.Color.red()
                severity = "🟠 High"
            elif score >= 0.7:
                color = discord.Color.orange()
                severity = "🟡 Moderate"
            else:
                color = discord.Color.yellow()
                severity = "⚪ Low"

            action_labels = {
                "warn": "⚠️ Message deleted + user warned",
                "delete": "🗑️ Message deleted + infraction logged",
                "timeout": "🔇 Message deleted + 5 min timeout",
            }

            embed = discord.Embed(
                title="🛡️ Auto-Moderation Alert",
                color=color,
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Offender", value=message.author.mention, inline=True)
            embed.add_field(name="Channel", value=f"<#{message.channel.id}>", inline=True)
            embed.add_field(
                name="Toxicity Score",
                value=f"**{score:.2f}** — {severity}\n*(Analyzed in {processing_time:.0f}ms)*",
                inline=True,
            )
            embed.add_field(
                name="Message",
                value=f"```{message.content[:500]}```",
                inline=False,
            )

            if keywords:
                embed.add_field(
                    name="Keywords",
                    value=", ".join(f'`{kw}`' for kw in keywords),
                    inline=False,
                )

            embed.add_field(name="Action", value=action_labels.get(action, action), inline=False)
            embed.set_footer(text=f"User ID: {message.author.id}")

            await mod_channel.send(embed=embed)

        except Exception as e:
            print(f"❌ Failed to post mod log: {e}")
