import discord, os
from discord import app_commands
from discord.ext import commands

from dotenv import load_dotenv
load_dotenv()


debug_guild_id = os.getenv("debug_guild_id")
debug_guild = discord.Object(debug_guild_id)


async def setup(client :commands.Bot):

    await client.add_cog(debug_commands(client))


class debug_commands(commands.Cog):

    def __init__(self, client) -> None:
        
        self.client = client


    #-#-#-// Get_Database //-#-#-#

    @app_commands.command(description='Sends the database file')
    @app_commands.guilds(debug_guild)
    async def get_db(self, intr :discord.Interaction):

        await intr.response.send_message(file=discord.File('main.db'))

    @app_commands.command(description="Info about the server the bot's running on")
    async def server_info(self, intr :discord.Interaction):
        if os.getlogin() == 'tibor0903' or 'pi': # server
            temperature = os.popen('vcgencmd measure_temp').read()
            temperature = temperature[temperature.index('=') + 1:-2]
            embed=discord.Embed(title="Server Info")
            embed.add_field(name="Host", value=os.getlogin(), inline=False)
            embed.add_field(name="Temperature", value=temperature, inline=False)
            await intr.response.send_message(embed=embed)
        else:
            await intr.response.send_message('running on test server, unavaliable')