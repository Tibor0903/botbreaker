import aiosqlite as asql

from utils.functions import *
from utils.task_embed import TaskEmbed
from utils import buttons as view_buttons

import discord
from discord import app_commands
from discord.ext import commands


async def setup(client :commands.Bot):

    await client.add_cog(tasks(client))


class tasks(commands.Cog):

    def __init__(self, client) -> None:

        self.client = client

    
    #-#-#-#-#-#-#-#-// Commands //-#-#-#-#-#-#-#-#

    @app_commands.command(description="Adds a task to the list")
    @app_commands.rename(dpt="department_name", name="task_name")
    @app_commands.describe(dpt="the department's name", name="task's name (animate something, code something, etc.)",
                           finished="is the task finished or not")
    async def add_task(self, intr :discord.Interaction, dpt :str, name :str, finished :bool = False):

        client = self.client
        similar_task_response = ("Similar task already exists! (id: {id})\n"
                                 "Do you still want to create the task?")

        c: asql.Cursor = await client.db.cursor()

        await c.execute("SELECT id FROM tasks WHERE department_name = ? AND task_name = ?;", [dpt, name])

        similar_task = await c.fetchone()
        similar_task_exists = not (similar_task is None) and len(similar_task) # If the task doesn't exist, the len is 0 (False)

        if similar_task_exists:

            buttons = view_buttons.TaskCreationButtons(name, dpt, finished, client)

            await intr.response.send_message(similar_task_response.format(id = similar_task[0]), view=buttons, ephemeral=True)
            await c.close()
            return


        await c.execute(("INSERT INTO tasks (department_name, task_name, status) VALUES (?, ?, ?)"
                            "RETURNING id;"), [dpt, name, finished])
            
        id = (await c.fetchone())[0]

        await client.db.commit()
        await c.close()
        
        embed = TaskEmbed(id, name, dpt, finished)
        await intr.response.send_message(embed=embed)


    #-#-#-// Remove_Task //-#-#-#

    @app_commands.command(description="Removes/deletes a chosen task")
    @app_commands.rename  (id="task_id")
    @app_commands.describe(id="id of the task you want to remove")
    async def remove_task(self, intr: discord.Interaction, id: int):

        client = self.client

        c: asql.Cursor = await client.db.cursor()

        async with c:

            await c.execute("SELECT task_name, department_name FROM tasks WHERE id = ?;", [id])

            items = await c.fetchone()
            if items is None: 

                await intr.response.send_message(f"Couldn't find a task under id {id}", ephemeral=True)
                await c.close(); return
            

        embed   = await getTaskEmbedFromID(client, id)
        buttons = view_buttons.TaskDeletionButtons(id, client)

        await intr.response.send_message(f"Do you really want to remove this task?", embed=embed, view=buttons)


    #-#-#-#-#-#-#-// Update_Task //-#-#-#-#-#-#-#

    @app_commands.command(description="Updates a chosen task")
    @app_commands.rename(new_dpt_name="new_department_name", new_status="finished")
    @app_commands.describe(id="id of the task you want to update", new_task_name="new task name", new_dpt_name="new department name",
                           new_status="task is now finished or not")
    async def update_task(self, intr :discord.Interaction, id :int, new_task_name :str = None, new_dpt_name :str = None, new_status :bool = None):

        client = self.client
        c :asql.Cursor = await client.db.cursor()

        async with c:

            await c.execute("SELECT task_name, department_name, status FROM tasks WHERE id = ?;", [id])
            task_info = await c.fetchone()

            if task_info is None: await intr.response.send_message(f"Couldn't find a task under id {id}"); return

            # (previous comment) theres probably a better way of doing this, oh well
            # tbh, i didn't make this code better cuz it technically stayed the same

            if new_task_name is None: new_task_name = task_info[0]
            if new_dpt_name  is None: new_dpt_name  = task_info[1]
            if new_status    is None: new_status    = task_info[2]

            await c.execute("UPDATE tasks SET task_name = ?, department_name = ?, status = ? WHERE id = ?;", [new_task_name, new_dpt_name, new_status, id])
            await client.db.commit()

        embed = await getTaskEmbedFromID(self.client, id)
        await intr.response.send_message(embed=embed)

        
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

            status = "Finished" if task[3] else "In Progress"

            new_tasks.append([task[0], task[1], status])


        response_msg += createTable(["ids", "task_name", "status"], new_tasks, len(response_msg + "```"))

        await intr.response.defer()
        await intr.followup.send(response_msg +"```")

    
    #-#-#-// Assign_People //-#-#-#

    @app_commands.command(description="Assigns chosen user to a task")
    @app_commands.rename(id="task_id")
    @app_commands.describe(id="id of the task you want to assign the user to",
                        user="the user you want to assign to the task (automatically selects you if skipped)")
    async def assign_people(self, intr: discord.Interaction, id: int, user: discord.User = None):

        client = self.client

        c: asql.Cursor = await client.db.cursor()
        user = user if user else intr.user

        await c.execute("SELECT assigned_people FROM tasks WHERE id = ?;", [id])
        stored_assigned_people = (await c.fetchone())[0]

        assigned_people = createJSONOfAssignedPeople(stored_assigned_people, user)

        await c.execute("UPDATE tasks SET assigned_people = ? WHERE id = ? RETURNING msg_id;", [assigned_people, id])
        msg_id = (await c.fetchone())[0]

        await client.db.commit()
        await c.close()
        
        await intr.response.send_message(f"Assigned {user.mention} to Task{id}!", ephemeral=True)


    #-#-#-// Add_Step //-#-#-#

    @app_commands.command()
    async def create_step(self, intr :discord.Interaction, id :int, name :str, index: int = 0, status :bool = False):

        client = self.client

        c: asql.Cursor = await client.db.cursor()

        await c.execute("SELECT steps FROM tasks WHERE id = ?;", [id])
        steps = (await c.fetchone())[0]

        steps = createJSONSteps(steps, name, status, index)

        await c.execute("UPDATE tasks SET steps = ? WHERE id = ? RETURNING msg_id;", [steps, id])
        msg_id = (await c.fetchone())[0]

        await client.db.commit()
        await c.close()

        await intr.response.send_message(f"```yaml\n Created a step for task {id}!```")


    #-#-#-// Update Step //-#-#-#

    @app_commands.command()
    async def update_step(self, intr :discord.Interaction, task_id :int, step_index :int, new_name :str):

        client = self.client

        id    = task_id
        index = step_index - 1 # -1 is here because the first step must be zero, the second - one and so on


        c: asql.Cursor = await client.db.cursor()

        await c.execute("SELECT steps FROM tasks WHERE id = ?;", [id])
        steps = (await c.fetchone())[0]
        
        steps_dict = json.loads(steps)
        step = steps_dict["steps"][index]

        step['name'] = new_name
        steps_dict["steps"][index] = step

        await c.execute("UPDATE tasks SET steps = ? WHERE id = ? RETURNING msg_id;", [json.dumps(steps_dict), id])
        msg_id = (await c.fetchone())[0]

        await client.db.commit()
        await c.close()

        await intr.response.send_message(f"```yaml\n Updated step {step_index} in task {task_id}!```")

        embed = await getTaskEmbedFromID(id)