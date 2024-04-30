import discord,time,json,os,random
from discord import SlashCommandGroup, Intents
from discord.ui import Button, View
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands import command, cooldown, is_owner, guild_only

from colorama import Style, Fore, Back

testtoken='MTIyODAzOTYyNTMyNzc3NTc2Ng.GEtNDL.jI_P3H5dyd8IMY59pYbKq1qPvgXBqddL2Ngx-Y'

i = discord.Intents.default()
i.members = True

bot = commands.Bot(intents = i)

@bot.event
async def on_ready():
    await bot.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+"ready"+Style.RESET_ALL)

@bot.slash_command(name='embedtest')
async def embedtest(intr):
    embed=discord.Embed(title="Animators")
    embed.add_field(name="task 1", value="- step 1 (:white_check_mark:) \n- step 2", inline=False)
    await intr.response.send_message('', embed=embed)

try:
    if os.getlogin() == 'pi':
        print('starting production')
        bot.run(testtoken)
    else:
        print('starting testing')
        bot.run(testtoken)
except NameError:
    print(Fore.RED+'fatal: token variable not found'+Style.RESET_ALL)
except discord.errors.LoginFailure or discord.errors.HTTPException:
    print(Fore.RED+'fatal: invalid token'+Style.RESET_ALL)