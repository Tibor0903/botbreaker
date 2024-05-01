import discord,time,json,os,random
from discord.ext import commands

from colorama import Style, Fore, Back
from ignored_folder.config import *

i = discord.Intents.default()
i.members = True

bot = commands.Bot(intents = i)



#-#-// Gateway //-#-#

@bot.event
async def on_ready():

    await bot.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+"ready"+Style.RESET_ALL)



#-#-// Slash Commands //-#-#

@bot.slash_command(name='embedtest')
async def embedtest(intr):
    embed=discord.Embed(title="Animators")
    embed.add_field(name="task 1", value="- step 1 (:white_check_mark:) \n- step 2", inline=False)
    await intr.response.send_message('', embed=embed)



#-#-// Bot Connection //-#-#

try:
    if os.getlogin() == 'pi':
        print('starting production')
        bot.run(productiontoken)

    else:
        print('starting testing')
        bot.run(testtoken)

except NameError:
    print(Fore.RED+'fatal: token variable not found'+Style.RESET_ALL)

except discord.errors.LoginFailure or discord.errors.HTTPException:
    print(Fore.RED+'fatal: invalid token'+Style.RESET_ALL)