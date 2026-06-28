import discord, aiohttp, os
from discord.ext import commands
from dotenv import load_dotenv


intents = discord.Intents.all()

bot = commands.Bot(command_prefix='.', intents=intents)

load_dotenv()
booster_role = int(os.getenv('BOOSTER_ROLE', '0'))
member_role  = int(os.getenv('MEMBER_ROLE', '0'))

@bot.event
async def on_ready():
    print(f'[DEBUG] Bot set up successful   | Bot: {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    await member.add_roles(member_role)

@bot.event
async def on_member_update(before, after):

    if before.premium_since != after.premium_since:
        if after.premium_since:
            await after.add_roles(booster_role)
        else:
            await after.remove_roles(booster_role)


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

token = str(os.getenv('TOKEN', None))
if (token is None) or ((booster_role == 0) or (member_role == 0)):
    print("[ERROR] enviroment was not set up correctly.")
    print(f"[DEBUG] Booster Role: {booster_role}           |  Valid: {'Yes' if booster_role != 0 else 'No'}")
    print(f"[DEBUG] Member Role:  {member_role}            |  Valid: {'Yes' if booster_role != 0 else 'No'}")
    print(f"[DEBUG] Bot Token:    {token.split('.')[0]}    |  Valid: {'Yes' if booster_role != 0 else 'No'}")
else:
    print("[DEBUG] All checks passed. Running bot.")
    bot.run(token)
