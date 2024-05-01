import discord,time,json,os,random
from discord import app_commands

from dotenv import load_dotenv
from colorama import Style, Fore, Back
#from config import *


load_dotenv()

token = os.getenv("token")
debug_guild_id = os.getenv("debug_guild_id")


class ModifiedClient(discord.Client):
    def __init__(self, *, intents :discord.Intents) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        
        # This syncs commands with the debug guild on each run
        self.tree.copy_global_to(guild=debug_guild)
        await self.tree.sync(guild=debug_guild)


intents = discord.Intents.default()
#intents.members = True

client = ModifiedClient(intents = intents)
debug_guild = discord.Object(id = debug_guild_id)



#-#-// Gateway //-#-#

@client.event
async def on_ready():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+"ready"+Style.RESET_ALL)



#-#-// Slash Commands //-#-#

@client.tree.command()
async def embedtest(intr):

    embed=discord.Embed(title="Animators")
    embed.add_field(name="task 1", value="- step 1 (:white_check_mark:) \n- step 2", inline=False)

    await intr.response.send_message('', embed=embed)



#-#-// Bot Connection //-#-#

client.run(token)


# I'll use my own bot to test stuff
"""try:
    if os.getlogin() == 'pi':
        print('starting production')
        bot.run(productiontoken)

    else:
        print('starting testing')
        bot.run(testtoken)

except NameError:
    print(Fore.RED+'fatal: token variable not found'+Style.RESET_ALL)

except discord.errors.LoginFailure or discord.errors.HTTPException:
    print(Fore.RED+'fatal: invalid token'+Style.RESET_ALL)"""