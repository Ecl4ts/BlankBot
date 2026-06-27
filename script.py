import discord, aiohttp, os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='.', intents=intents)

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
    role = member.guild.get_role(1520444030855676004)
    

@bot.command()
async def check_booster(ctx, member: discord.Member):
    role = member.guild.get_role(1520440841179631716)
    if member.premium_since:
        await ctx.send(f"{member} is boosting!")
        await member.add_roles(role)
    else:
        await ctx.send(f"{member} is not boosting")
        await member.remove_roles(role)

async def delete_webhook(webhook):
    async with aiohttp.ClientSession() as session:
        async with session.delete(webhook) as response:
            if response.status == 204:
                print("done")
                return "Deleted"
            else:
                data = await response.json()
                return f"Could not delete. \nMessage: {data['message']}\nCode: {data['code']}\nStatus: {response.status}"

@bot.command()
async def delete(ctx, webhook):
    message = await delete_webhook(webhook)
    await ctx.message.reply(message)

@bot.command()
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=(amount + 1))
    await ctx.send(f"Purged {amount} messages", delete_after=5)

@bot.command()
async def wipe(ctx):
    await ctx.channel.purge()
    await ctx.send(f"Wiped channel", delete_after=5)

bot.run(os.getenv('TOKEN'))