import aiosqlite as asql

from utils.functions import *
from utils.task_embed import TaskEmbed

import discord
from discord import app_commands
from discord.ext import commands


async def setup(client :commands.Bot):

    await client.add_cog(tasks(client))


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


    #-#-#-#-#-#-#-// Update_Task //-#-#-#-#-#-#-#

    @app_commands.command(description="Updates a chosen task")
    @app_commands.rename(new_dpt_name="new_department_name", new_status="finished")
    @app_commands.describe(id="id of the task you want to update", new_task_name="new task name", new_dpt_name="new department name",
                           new_status="task is now finished or not")
    async def update_task(self, intr :discord.Interaction, id :int, new_task_name :str = None, new_dpt_name :str = None, new_status :bool = None):

        client = self.client
        c :asql.Cursor = await client.db.cursor()

        async with c:
            await c.execute("SELECT * FROM tasks WHERE id = ?;", [id])
            task_info = await c.fetchone()

        print(task_info)
        await intr.response.send_message("console")

        
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

        embed = await getTaskEmbedFromID(id)
        await updateTaskEmbed(intr, msg_id, embed)


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

        embed = await getTaskEmbedFromID(id)
        await updateTaskEmbed(intr, msg_id, embed)


    #-#-#-// Update Step //-#-#-#

    @app_commands.command()
    async def update_step(self, intr :discord.Interaction, task_id :int, step_index :int, new_name :str):

        client = self.client

        id=task_id
        index=step_index-1 # need -1, idk why


        c: asql.Cursor = await client.db.cursor()

        await c.execute("SELECT steps FROM tasks WHERE id = ?;", [id])
        steps = (await c.fetchone())[0]
        
        steps_dict = json.loads(steps)
        step = steps_dict["steps"][index]

        #print(step)
        step['name'] = new_name
        #print(step)
        steps_dict["steps"][index] = step

        await c.execute("UPDATE tasks SET steps = ? WHERE id = ? RETURNING msg_id;", [json.dumps(steps_dict), id])
        msg_id = (await c.fetchone())[0]

        await client.db.commit()
        await c.close()

        await intr.response.send_message(f"```yaml\n Updated step {step_index} in task {task_id}!```")

        embed = await getTaskEmbedFromID(id)
        await updateTaskEmbed(intr, msg_id, embed)