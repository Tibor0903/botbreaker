import discord
from discord import app_commands
from discord.ext import commands


async def setup(client :commands.Bot):

    await client.add_cog(general(client))


class general(commands.Cog):

    def __init__(self, client) -> None:

        self.client = client


    #-#-#-// Commands //-#-#-#


    @app_commands.command(description="Sends a list of commands and their purposes")
    async def help(self, intr :discord.Interaction):

        embed = discord.Embed(color=discord.colour.parse_hex_number("#2B2D31"), 
                              title="List of Commands")
        
        icon_url = ("https://cdn.discordapp.com/attachments/1234791407265251402/1236177556630142996/6d66b23b5f142921.jpg?"
                    "ex=66370f90&is=6635be10&hm=6f1163150dd284b768e4da7caba14450d6265c8d298bbc47d91beb8afba70c95&")

        embed.set_author(name="/help", icon_url=icon_url)

        with open("cogs/general_help.txt") as f:

            lines = f.readlines()
            current_field_name = ""
            current_field_value = ""

            for line in lines:

                if line.startswith("-//"):

                    line = line[3:]

                    embed.add_field(name=line, value=current_field_value)
                    current_field_value = ""
                else:

                    current_field_value += line


        await intr.response.send_message(embed=embed)