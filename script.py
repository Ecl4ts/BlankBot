import discord, aiohttp, os
from discord.ext import commands
from dotenv import load_dotenv


intents = discord.Intents.all()

bot = commands.Bot(command_prefix='.', intents=intents)

load_dotenv()
booster_role = int(os.getenv('BOOSTER_ROLE'))
member_role  = int(os.getenv('MEMBER_ROLE'))

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    role = member.guild.get_role(member_role)
    await member.add_roles(role)

@bot.event
async def on_member_update(before, after):
    booster_role = after.guild.get_role(booster_role)
    
    if before.premium_since != after.premium_since:
        if after.premium_since:
            await after.add_roles(booster_role)
        else:
            await after.remove_roles(booster_role)

@bot.command()
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

bot.run(os.getenv('TOKEN'))
