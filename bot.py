from utils.functions import *

import discord, aiosqlite as asql
from discord.ext import commands

from colorama import Style, Fore


sys_message_divider = "---------------"


class Bot(commands.Bot):

    def __init__(self, command_prefix :str, intents :discord.Intents, debug_guild_id :str) -> None:

        super().__init__(command_prefix, intents=intents)
        self.debug_guild = discord.Object(debug_guild_id)


    async def setup_hook(self) -> None:

        # Database loader

        self.db = await asql.connect("main.db")
        cursor = await self.db.cursor()

        async with cursor as c:
            await c.execute(("CREATE TABLE IF NOT EXISTS tasks ("
                        "id INTEGER PRIMARY KEY, "
                        "msg_id INTEGER, "
                        "department_name STRING, "
                        "task_name STRING, "
                        "status BOOLEAN, "
                        "assigned_people JSON, "
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