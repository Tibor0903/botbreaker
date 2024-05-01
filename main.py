import discord,time,json,os,random
from discord import app_commands

from dotenv import load_dotenv
from colorama import Style, Fore, Back
from colorama import just_fix_windows_console as fix_win_console
#from config import *


fix_win_console()
load_dotenv()

production_token = 0
test_token = os.getenv("token")
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


#-#-// Functions //-#-#

def getCurrentTime() -> str:

    # 01/01/1970 00:00:00 UTC
    return time.strftime("%d/%m/%Y %H:%M:%S UTC", time.gmtime())



#-#-// Gateway //-#-#

@client.event
async def on_ready():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+"-----------\n")
    print(f"The bot has started session at {getCurrentTime()}!")
    print("\n-----------"+Style.RESET_ALL)


@client.event
async def on_resumed():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+"-----------\n")
    print(f"The bot has resumed session at {getCurrentTime()}!")
    print("\n-----------"+Style.RESET_ALL)


@client.event
async def on_disconnect():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.RED+"-----------\n")
    print(f"The bot has disconnected at {getCurrentTime()}!")
    print("\n-----------"+Style.RESET_ALL)



#-#-// Slash Commands //-#-#

@client.tree.command()
async def embedtest(intr):

    embed=discord.Embed(title="Animators")
    embed.add_field(name="task 1", value="- step 1 (:white_check_mark:) \n- step 2", inline=False)

    await intr.response.send_message('', embed=embed)



#-#-// Bot Connection //-#-#

try:

    token = 0

    if os.getlogin() == 'pi':

        print(Fore.BLUE+'The bot is using the production token!')
        token = production_token

    else:
        print(Fore.BLUE+'The bot is using the test token!')
        token = test_token

    print(f'Start time: {getCurrentTime()}\n')
    print('---------------'+Style.RESET_ALL)
    client.run(token)

except NameError:
    print(Fore.RED+ '\nFatal: Token variable not found' +Style.RESET_ALL)

except discord.errors.LoginFailure or discord.errors.HTTPException:
    print(Fore.RED+ '\nFatal: Invalid token' +Style.RESET_ALL)