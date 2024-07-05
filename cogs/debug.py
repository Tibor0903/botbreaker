import discord, os, json
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


    #-#-#-// Server_Info //-#-#-# 

    @app_commands.command(description="Info about the server the bot's running on")
    async def server_info(self, intr :discord.Interaction):

        if str(os.getlogin()) == 'tibor0903':

            temperature = os.popen('vcgencmd measure_temp').read()
            temperature = temperature[temperature.index('=') + 1:-2]

            embed=discord.Embed(title="Server Info")
            embed.add_field(name="Host", value=os.getlogin(), inline=False)
            embed.add_field(name="Temperature", value=temperature, inline=False)

            await intr.response.send_message(embed=embed)
        else:

            await intr.response.send_message("Running on test server\n Data unavailable")


    #-#-#-#-#-#-// Temporary commands //-#-#-#-#-#-#-

    @app_commands.command(description='Deletes the "msg_id" column')
    async def delete_msg_ids(self, intr :discord.Interaction):

        c = await self.client.db.cursor()

        async with c:

            await c.execute("ALTER TABLE tasks DROP COLUMN msg_id;")
            await self.client.db.commit()

        await intr.response.send_message("Successfully dropped column msg_id")


    @app_commands.command()
    async def update_assigned_people(self, intr :discord.Interaction):

        c = await self.client.db.cursor()

        await c.execute("SELECT assigned_people, id FROM tasks;")

        rows = await c.fetchall()

        for row in rows:

            if row[0] is None: continue

            try:

                data = json.loads(row[0])
                data = data["user_ids"]

                data = str(data)[1:-1]                # Removes brackets
                data = str.join("", data.split(" "))  # Removes spaces

                await c.execute("UPDATE tasks SET assigned_people = ? WHERE id = ?;", [data, row[1]])

            except json.JSONDecodeError: 
                pass
        
        await c.execute("SELECT assigned_people, id FROM tasks;")
        rows = await c.fetchall()

        await c.execute("ALTER TABLE tasks DROP COLUMN assigned_people;")
        await c.execute("ALTER TABLE tasks ADD COLUMN assigned_people STRING;")

        for row in rows:

            await c.execute("UPDATE tasks SET assigned_people = ? WHERE id = ?", [row[0], row[1]])

        await self.client.db.commit()
        await c.close()
        await intr.response.send_message("Successfully updated assigned_people")


    @app_commands.command()
    async def update_steps(self, intr :discord.Interaction):

        c = await self.client.db.cursor()

        async with c:

            await c.execute("SELECT steps, id FROM tasks;")

            rows = await c.fetchall()

            for row in rows:

                if row[0] is None: continue

                try:

                    data = json.loads(row[0])
                    data = data["steps"]
                    data = json.dumps(data)

                    await c.execute("UPDATE tasks SET steps = ? WHERE id = ?;", [data, row[1]])
                
                except json.JSONDecodeError: continue

            await self.client.db.commit()

        await intr.response.send_message("Successfully updated steps to newer version")