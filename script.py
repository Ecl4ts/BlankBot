import discord, aiohttp, os
from discord.ext import commands
from dotenv import load_dotenv


intents = discord.Intents.all()

bot = commands.Bot(command_prefix='.', intents=intents)

load_dotenv()
booster_role = int(os.getenv('BOOSTER_ROLE', '0'))
member_role  = int(os.getenv('MEMBER_ROLE', '0'))
honeypot_channel = int(os.getenv('HONEYPOT_CHANNEL', '0'))

@bot.event
async def on_ready():
    print(f'[DEBUG] Bot set up successful   | Bot: {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == honeypot_channel:
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        for channel in message.guild.text_channels:
            try:
                await channel.purge(limit=100, check=lambda m: m.author.id == message.author.id)
            except discord.HTTPException:
                pass

        try:
            await message.author.kick(reason="Triggered honeypot")
        except discord.Forbidden:
            pass

    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    await member.add_roles(member.guild.get_role(member_role))

@bot.event
async def on_member_update(before, after):
    if before.premium_since != after.premium_since:
        role = after.guild.get_role(booster_role)
        if not role:
            return
        if after.premium_since:
            await after.add_roles(role)
        else:
            await after.remove_roles(role)


async def delete_webhook(webhook):
    async with aiohttp.ClientSession() as session:
        async with session.delete(webhook) as response:
            if response.status == 204:
                return "Deleted"
            else:
                data = await response.json()
                return f"Could not delete. \nMessage: {data['message']}\nCode: {data['code']}\nStatus: {response.status}"

@bot.command()
async def delete(ctx, webhook):
    message = await delete_webhook(webhook)
    await ctx.message.reply(message)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=(amount + 1))
    await ctx.send(f"Purged {amount} messages", delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def wipe(ctx):
    await ctx.channel.purge()
    await ctx.send(f"Wiped channel", delete_after=5)

@bot.command()
async def member_count(ctx):
    member_count = ctx.guild.member_count
    await ctx.send(f"{ctx.guild.name} has {member_count} members.")


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
            else:
                failed += 1

        if i % 10 == 0 or i == total:
            await status_msg.edit(content=(
                f"Role: {role.name}\n"
                f"Progress: {i}/{total}\n"
                f"Success: {success}\n"
                f"Failed: {failed}\n"
                f"Rate limited: {ratelimited}"
            ))

    await status_msg.edit(content=(
        f"Role: {role.name}\n"
        f"Done: {total}/{total}\n"
        f"Success: {success}\n"
        f"Failed: {failed}\n"
        f"Rate limited: {ratelimited}"
    ))

token = os.getenv('TOKEN')
if (token is None) or ((booster_role == 0) or (member_role == 0)) or (honeypot_channel == 0):
    print("[ERROR] environment variables were not set up correctly.")
    print(f"[DEBUG] Booster Role: {booster_role}           |  Valid: {'Yes' if booster_role != 0 else 'No'}")
    print(f"[DEBUG] Member Role:  {member_role}            |  Valid: {'Yes' if member_role != 0 else 'No'}")
    print(f"[DEBUG] Honeypot Channel: {honeypot_channel} |  Valid: {'Yes' if honeypot_channel != 0 else 'No'}")
    print(f"[DEBUG] Bot Token:    {(token.split('.')[0]) if token else "None"}    |  Valid: {'Yes' if token else 'No'}")
else:
    print("[DEBUG] All checks passed. Running bot.")
    bot.run(token)
