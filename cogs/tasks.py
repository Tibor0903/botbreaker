import aiosqlite as asql

from utils.functions import *
from utils.task_embed import TaskEmbed

import discord
from discord import app_commands
from discord.ext import commands


async def setup(client :commands.Bot):

    await client.add_cog( tasks(client) )


class tasks(commands.Cog):

    def __init__(self, client) -> None:

        self.client = client

    
    #-#-#-#-#-#-#-#-// Commands //-#-#-#-#-#-#-#-#

    @app_commands.command(description="Creates a task")
    @app_commands.rename(dpt="department_name", name="task_name")
    @app_commands.describe(dpt="the department's name", name="task's name (animate something, code something, etc.)",
                        hide_reply="hides a reply to the command (also doesn't show who ran the command)")
    async def create_task(self, intr :discord.Interaction, dpt :str, name :str, hide_reply :bool = False):

        client = self.client

        c: asql.Cursor = await client.db.cursor()
        response_msg = "```yaml\n Created a task!```"

        await c.execute("SELECT id FROM tasks WHERE department_name = ? AND task_name = ?;", [dpt, name])

        similar_task = await c.fetchone()
        if not (similar_task is None) and len(similar_task): # If the task doesn't exist, the len is 0 (False)

            response_msg = f"```prolog\n WARNING: similar task already exists! id: {similar_task[0]}```"
    
        await c.execute(("INSERT INTO tasks (department_name, task_name, status) VALUES (?, ?, ?)"
                            "RETURNING id;"), [dpt, name, False])
            
        id = (await c.fetchone())[0]

        await client.db.commit()
        await intr.response.send_message(response_msg, ephemeral=hide_reply)

        embed = TaskEmbed(id=id, task_name=name, task_dpt=dpt)
        msg = await intr.channel.send(embed=embed)
        
        await c.execute("UPDATE tasks SET msg_id = ? WHERE id = ?;", [msg.id, id])

        await client.db.commit()
        await c.close()


    #-#-#-// Delete_Task //-#-#-#

    @app_commands.command(description="Deletes a chosen task")
    @app_commands.rename(id="task_id")
    @app_commands.describe(id="id of the task you want to delete")
    async def delete_task(self, intr: discord.Interaction, id: int):

        client = self.client

        c: asql.Cursor = await client.db.cursor()

        async with c:
            await c.execute("SELECT * FROM tasks WHERE id = ?;", [id])
            
            if (await c.fetchone()) is None: await c.close(); return

            await c.execute("DELETE FROM tasks WHERE id = ? RETURNING *;", [id])
            task_values = await c.fetchone()
            await client.db.commit()

        await intr.response.send_message(f"```yaml\n Deleted task under id {id}.```")

        msg_id = task_values[1]
        name, dpt = task_values[3], task_values[2]
        steps, people = task_values[6], task_values[5]

        embed = TaskEmbed(id=id, task_name=name, task_dpt=dpt, deleted=True, steps=steps, assigned_peeps=people)

        await updateTaskEmbed(intr, msg_id, embed)
        
        
    #-#-#-// Show_Task //-#-#-#

    @app_commands.command()
    async def show_task(self, intr :discord.Interaction, id :int):

        client = self.client

        c :asql.Cursor = await client.db.cursor()
        embed = await getTaskEmbedFromID(self.client, id)

        if not embed:

            await intr.response.send_message(f"```ml\n ERROR: task doesn't exist```")
            return

        await intr.response.send_message(embed = embed)

        msg = await intr.original_response()

        async with c:
            await c.execute("UPDATE tasks SET msg_id = ? WHERE id = ?", [msg.id, id])
            await client.db.commit()


    #-#-#-// List_Tasks //-#-#-#

    @app_commands.command()
    async def list_tasks(self, intr: discord.Interaction):

        client = self.client
        
        c :asql.Cursor = await client.db.cursor()
        response_msg = ("```yaml\n Here's a list of tasks!```\n"
                        "```\n")
        
        async with c:
            await c.execute("SELECT id, task_name, msg_id, status FROM tasks;")
            tasks = await c.fetchall()

        new_tasks = []
        for task in tasks:

            status = "Finished" if task[3] else "In Process"

            new_tasks.append([task[0], task[1], task[2], status])


        response_msg += createTable(["ids", "task_name", "message_ids", "status"], new_tasks, len(response_msg + "```"))

        await intr.response.defer()
        await intr.followup.send(response_msg +"```")