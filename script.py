import discord
import aiohttp
import os
import asyncio

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()


def env_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in ("1", "true", "yes", "on")


booster_role = int(os.getenv("BOOSTER_ROLE", "0"))
member_role = int(os.getenv("MEMBER_ROLE", "0"))
honeypot_channel = int(os.getenv("HONEYPOT_CHANNEL", "0"))

bot_prefix = os.getenv("PREFIX", ".")

honeypot_enabled = env_bool("HONEYPOT_ENABLED")
booster_role_enabled = env_bool("BOOSTER_ROLE_ENABLED")
auto_role_enabled = env_bool("AUTO_ROLE_ENABLED")


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=bot_prefix,
    intents=intents
)


@bot.event
async def on_ready():
    print(f"[DEBUG] Bot set up successful | Bot: {bot.user}")
    print(f"[DEBUG] Bot ID: {bot.user.id}")
    print(f"[DEBUG] Guilds: {len(bot.guilds)}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if honeypot_enabled and message.channel.id == honeypot_channel:
        try:
            await message.delete()
        except discord.HTTPException:
            print(
                f"[DEBUG] Failed to delete message from "
                f"{message.author} in honeypot channel."
            )

        try:
            await message.author.send(
                f"You have triggered a honeypot in "
                f"{message.guild.name}. You have been banned from the server.\n"
                f"This ban expires in 24 hours. (1 day)"
            )
        except discord.HTTPException:
            print(
                f"[DEBUG] Failed to DM {message.author} "
                f"for triggering honeypot."
            )

        try:
            await message.author.ban(
                reason="Triggered honeypot",
                delete_message_seconds=86400
            )
        except discord.HTTPException:
            print(
                f"[DEBUG] Failed to ban {message.author} "
                f"for triggering honeypot."
            )

    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    if not auto_role_enabled:
        return

    role = member.guild.get_role(member_role)

    if role is None:
        print(
            f"[DEBUG] Could not find member role "
            f"{member_role} in {member.guild.name}."
        )
        return

    try:
        await member.add_roles(role)
    except discord.HTTPException as e:
        print(
            f"[DEBUG] Failed to add member role to "
            f"{member}: {e}"
        )


@bot.event
async def on_member_update(before, after):
    if not booster_role_enabled:
        return

    if before.premium_since == after.premium_since:
        return

    role = after.guild.get_role(booster_role)

    if role is None:
        return

    try:
        if after.premium_since:
            await after.add_roles(role)
        else:
            await after.remove_roles(role)
    except discord.HTTPException as e:
        print(
            f"[DEBUG] Failed to update booster role "
            f"for {after}: {e}"
        )


async def delete_webhook(webhook):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(webhook) as response:
                if response.status == 204:
                    return "Deleted"

                try:
                    data = await response.json()
                    return (
                        f"Could not delete.\n"
                        f"Message: {data.get('message', 'Unknown')}\n"
                        f"Code: {data.get('code', 'Unknown')}\n"
                        f"Status: {response.status}"
                    )
                except aiohttp.ContentTypeError:
                    return (
                        f"Could not delete.\n"
                        f"Status: {response.status}"
                    )

        except aiohttp.ClientError as e:
            return f"Could not delete.\nError: {e}"


@bot.command()
async def delete(ctx, webhook):
    message = await delete_webhook(webhook)
    await ctx.message.reply(message)


@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    try:
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False
        )
    except discord.Forbidden:
        await ctx.send(
            "I do not have permission to lock this channel.",
            delete_after=5
        )
        return

    await ctx.send("Channel locked.", delete_after=5)


@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    try:
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=True
        )
    except discord.Forbidden:
        await ctx.send(
            "I do not have permission to unlock this channel.",
            delete_after=5
        )
        return

    await ctx.send("Channel unlocked.", delete_after=5)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1:
        await ctx.send(
            "Amount must be greater than 0.",
            delete_after=5
        )
        return

    print(f"[DEBUG] Purging {amount} messages")

    try:
        await ctx.channel.purge(limit=amount + 1)
    except discord.Forbidden:
        await ctx.send(
            "I do not have permission to purge messages.",
            delete_after=5
        )
        return

    await ctx.send(
        f"Purged {amount} messages.",
        delete_after=5
    )


@bot.command()
@commands.has_permissions(manage_messages=True)
async def wipe(ctx):
    try:
        await ctx.channel.purge()
    except discord.Forbidden:
        await ctx.send(
            "I do not have permission to wipe this channel.",
            delete_after=5
        )
        return

    await ctx.send(
        "Wiped channel.",
        delete_after=5
    )


@bot.command()
async def member_count(ctx):
    await ctx.send(
        f"{ctx.guild.name} has {ctx.guild.member_count} members."
    )


@bot.command()
@commands.has_permissions(manage_roles=True)
async def role_all(ctx, role: discord.Role):
    members = ctx.guild.members
    total = len(members)

    success = 0
    failed = 0
    ratelimited = 0

    status_msg = await ctx.send(
        f"Role: {role.name}\n"
        f"Progress: 0/{total}\n"
        f"Success: 0\n"
        f"Failed: 0\n"
        f"Rate limited: 0"
    )

    for i, member in enumerate(members, start=1):
        try:
            await member.add_roles(role)
            success += 1

        except discord.HTTPException as e:
            if e.status == 429:
                ratelimited += 1
                retry_after = getattr(e, "retry_after", 1)
                await asyncio.sleep(retry_after)
            else:
                failed += 1

        except discord.Forbidden:
            failed += 1

        if i % 10 == 0 or i == total:
            try:
                await status_msg.edit(
                    content=(
                        f"Role: {role.name}\n"
                        f"Progress: {i}/{total}\n"
                        f"Success: {success}\n"
                        f"Failed: {failed}\n"
                        f"Rate limited: {ratelimited}"
                    )
                )
            except discord.HTTPException:
                pass

    await status_msg.edit(
        content=(
            f"Role: {role.name}\n"
            f"Done: {total}/{total}\n"
            f"Success: {success}\n"
            f"Failed: {failed}\n"
            f"Rate limited: {ratelimited}"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "You don't have permission to use that command.",
            delete_after=5
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"Missing argument: `{error.param.name}`",
            delete_after=5
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            "Invalid argument.",
            delete_after=5
        )
        return

    print(f"[DEBUG] Command error: {error}")


token = os.getenv("TOKEN")


configuration_error = (
    token is None
    or (
        booster_role == 0
        and booster_role_enabled
    )
    or (
        member_role == 0
        and auto_role_enabled
    )
    or (
        honeypot_channel == 0
        and honeypot_enabled
    )
)


if configuration_error:
    print("[ERROR] Environment variables were not set up correctly.")

    print(
        f"[DEBUG] Booster Role: {booster_role} | "
        f"Valid: {'Yes' if booster_role != 0 else 'No'}"
    )

    print(
        f"[DEBUG] Member Role: {member_role} | "
        f"Valid: {'Yes' if member_role != 0 else 'No'}"
    )

    print(
        f"[DEBUG] Honeypot Channel: {honeypot_channel} | "
        f"Valid: {'Yes' if honeypot_channel != 0 else 'No'}"
    )

    print(
        f"[DEBUG] Bot Token: "
        f"{token.split('.')[0] if token else 'None'} | "
        f"Valid: {'Yes' if token else 'No'}"
    )

    print(f"[DEBUG] Honeypot Enabled: {honeypot_enabled}")
    print(f"[DEBUG] Booster Role Enabled: {booster_role_enabled}")
    print(f"[DEBUG] Auto Role Enabled: {auto_role_enabled}")

else:
    print("[DEBUG] All checks passed. Running bot.")
    bot.run(token)
