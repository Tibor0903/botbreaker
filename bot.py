from utils.functions import *

import discord, os, aiosqlite as asql
from discord.ext import commands

from colorama import Style, Fore


sys_message_divider = "---------------"


def deleteFilesInFolder(folder_path :str):

    for obj in os.listdir(folder_path):

        obj = f"{folder_path}/{obj}"

        if os.path.isfile(obj):

            os.remove(obj)
        else:

            deleteFilesInFolder(obj)
            os.rmdir(obj)


class Bot(commands.Bot):

    def __init__(self, command_prefix :str, intents :discord.Intents, debug_guild_id :str) -> None:

        super().__init__(command_prefix, intents=intents)
        self.debug_guild = discord.Object(debug_guild_id)


    async def setup_hook(self) -> None:

        try:
            deleteFilesInFolder("app_cache")
        except FileNotFoundError:
            os.mkdir('app_cache')
        except:
            print(Style.RESET_ALL+Fore.YELLOW+'Could not delete app_cache!'+Style.RESET_ALL)
        # Database loader

        self.db = await asql.connect("main.db")
        cursor = await self.db.cursor()

        async with cursor as c:
            await c.execute(("CREATE TABLE IF NOT EXISTS tasks ("
                        "id INTEGER PRIMARY KEY, "
                        "department_name STRING, "
                        "task_name STRING, "
                        "status BOOLEAN, "
                        "assigned_people STRING, "
                        "steps JSON);"
                        ))
            
        await self.db.commit()

        # Slash Commands        
        await self.load_extension("cogs.tasks")
        await self.load_extension("cogs.debug")

        # This syncs commands with the debug guild on each run
        self.tree.copy_global_to(guild = self.debug_guild)
        await self.tree.sync(guild = self.debug_guild)


    #-#-#-#-#-#-#-// Gateway //-#-#-#-#-#-#-#

    async def on_ready(self):

        await self.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))

        print(Fore.GREEN+f"{sys_message_divider}\n")
        print(f"The bot has started session at {getCurrentTime()}!")
        print(f"\n{sys_message_divider}"+Style.RESET_ALL)


    async def on_resumed(self):

        await self.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
        
        print(Fore.GREEN+f"{sys_message_divider}\n")
        print(f"The bot has resumed session at {getCurrentTime()}!")
        print(f"\n{sys_message_divider}"+Style.RESET_ALL)


    async def on_disconnect(self):

        print(Fore.RED+f"{sys_message_divider}\n")
        print(f"The bot has disconnected at {getCurrentTime()}!")
        print(f"\n{sys_message_divider}"+Style.RESET_ALL)


if __name__ == "__main__":

    from os import getenv
    from dotenv import load_dotenv

    load_dotenv()
    test_token     = getenv("test_token")
    debug_guild_id = getenv("debug_guild_id")

    intents = discord.Intents().default()
    intents.members = True
    intents.message_content = True

    bot = Bot("/", intents, debug_guild_id)
    bot.run(test_token)