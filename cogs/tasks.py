import aiosqlite as asql

from utils.functions import *
from utils.task_embed import TaskEmbed
from utils import buttons as view_buttons

import discord
from discord import app_commands
from discord.ext import commands


task_404 = "Task #{id} doesn't exist or the bot couldn't find it"


async def setup(client :commands.Bot):

    await client.add_cog(tasks(client))


class tasks(commands.Cog):

    def __init__(self, client) -> None:

        self.client = client

    
    #-#-#-#-#-#-#-#-// Commands //-#-#-#-#-#-#-#-#

    @app_commands.command(description="Creates a task to the list")
    @app_commands.rename(dpt="department_name", name="task_name")
    @app_commands.describe(dpt="the department's name", name="task's name (animate something, code something, etc.)",
                           finished="is the task finished or not")
    async def create_task(self, intr :discord.Interaction, dpt :str, name :str, finished :bool = False):

        client = self.client
        similar_task_response = ("Similar task already exists! (id: {id})\n"
                                 "Do you still want to create the task?")

        c: asql.Cursor = await client.db.cursor()

        await c.execute("SELECT id FROM tasks WHERE department_name = ? AND task_name = ?;", [dpt, name])

        similar_task = await c.fetchone()
        similar_task_exists = not (similar_task is None) and len(similar_task) # If the task doesn't exist, the len is 0 (False)

        if similar_task_exists:

            buttons = view_buttons.TaskCreationButtons(name, dpt, finished, client)

            await intr.response.send_message(similar_task_response.format(id = similar_task[0]), view=buttons)
            await c.close()
            return


        await c.execute(("INSERT INTO tasks (department_name, task_name, status) VALUES (?, ?, ?)"
                            "RETURNING id;"), [dpt, name, finished])
            
        id = (await c.fetchone())[0]

        await client.db.commit()
        await c.close()
        
        embed = TaskEmbed(id, name, dpt, finished)
        await intr.response.send_message(embed=embed)


    #-#-#-// Delete_Task //-#-#-#

    @app_commands.command(description="Deletes a chosen task")
    @app_commands.rename  (id="task_id")
    @app_commands.describe(id="id of the task you want to delete")
    async def delete_task(self, intr: discord.Interaction, id: int):

        client = self.client

        c: asql.Cursor = await client.db.cursor()

        async with c:

            await c.execute("SELECT task_name, department_name FROM tasks WHERE id = ?;", [id])

            items = await c.fetchone()
            if items is None: 

                await intr.response.send_message(task_404.format(id=id))
                await c.close(); return
            

        embed   = await getTaskEmbedFromID(client, id)
        buttons = view_buttons.TaskDeletionButtons(id, client)

        await intr.response.send_message(f"Do you really want to delete this task?", embed=embed, view=buttons)


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

            if task_info is None: await intr.response.send_message(task_404.format(id=id)); return

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

        c :asql.Cursor = await self.client.db.cursor()

        async with c:

            await c.execute("SELECT * FROM tasks WHERE id = ?;", [id])
            if (await c.fetchone())[0] is None: 
                
                await intr.response.send_message(task_404.format(id=id))
                return
            

        embed = await getTaskEmbedFromID(self.client, id)
        await intr.response.send_message(embed=embed)


    #-#-#-// List_Tasks //-#-#-#

    @app_commands.command(description="Lists every tasks or tasks, assigned to specific people")
    @app_commands.describe(member = 'Member, whose tasks you want to see (if "member" and "all" are skipped, it selects you)', 
                           all = "If True, you'll see every task on the server at the moment",
                           sort = "Sorts in alphabetic order")
    async def list_tasks(self, intr: discord.Interaction, member: discord.User = None, all: bool = None, sort: bool = True):

        c :asql.Cursor = await self.client.db.cursor()

        if not member and not all: member = intr.user

        if member:

            member_command = f"WHERE assigned_people LIKE '%{member.id}%'"
        else:

            member_command = ""

        order_command = "ORDER BY department_name"
        if not sort: order_command = ""

        async with c:

            await c.execute(f"SELECT id, department_name, task_name, status FROM tasks {member_command} {order_command};")
            
            rows = await c.fetchall()

            if not len(rows): 
                
                await intr.response.send_message("The server doesn't have any tasks or you don't have any assigned tasks")
                return
            
            tasks = []
            for task in rows:

                status = "Done" if task[3] else "In process"

                tasks.append([task[0], task[1], task[2], status])


        await intr.response.defer(thinking=True)

        columns = ["IDs", "Department(s)", "Tasks", "Status"]

        table = createTable(columns, tasks)

        await intr.followup.send(file=table)
        
    
    #-#-#-// Assign_Person //-#-#-#

    @app_commands.command(description="Assigns chosen user to a task")
    @app_commands.rename(id="task_id")
    @app_commands.describe(id="id of the task you want to assign the user to",
                           user="the user you want to assign to the task (automatically selects you if skipped)")
    async def assign_person(self, intr: discord.Interaction, id: int, user: discord.User = None):

        c: asql.Cursor = await self.client.db.cursor()

        if not user: user = intr.user

        await c.execute("SELECT assigned_people FROM tasks WHERE id = ?;", [id])

        row = await c.fetchone()
        if not row:
            
            await intr.response.send_message(task_404.format(id=id))
            await c.close(); return

        old_asgn_people = row[0]
        comma = ","

        if listFind(str(old_asgn_people).split(","), str(user.id)):

            await intr.response.send_message(f"{user.display_name} is already assigned to Task #{id}")
            await c.close(); return

        if not old_asgn_people: 
            
            old_asgn_people = ""
            comma = ""

        new_asgn_people = str(old_asgn_people) + comma + str(user.id)

        await c.execute("UPDATE tasks SET assigned_people = ? WHERE id = ?;", [new_asgn_people, id])

        await self.client.db.commit()
        await c.close()

        embed = await getTaskEmbedFromID(self.client, id)
        await intr.response.send_message(f"Successfully assigned {user.display_name} to Task #{id}", embed=embed)


    @app_commands.command(description="Removes an assigned user from the task")
    @app_commands.rename(id="task_id")
    @app_commands.describe(id="ID of the task you want to remove the user from",
                           user="The user you want to remove from the task (automatically selects you if skipped)")
    async def remove_person(self, intr: discord.Interaction, id: int, user: discord.User = None):

        c: asql.Cursor = await self.client.db.cursor()

        if not user: user = intr.user

        await c.execute("SELECT assigned_people FROM tasks WHERE id = ?;", [id])


        # Checks if task even exists
        row = await c.fetchone()
        if not row:
            
            await intr.response.send_message(task_404.format(id=id))
            await c.close(); return


        # Checks if the person is assigned
        asgn_people = row[0]
        split_asgn_people = str(asgn_people).split(",")
        if not listFind(split_asgn_people, str(user.id)):

            await intr.response.send_message(f"{user.display_name} is not assigned to Task #{id}")
            await c.close(); return
        

        split_asgn_people.remove(str(user.id))
        new_asgn_people = ",".join(split_asgn_people)

        await c.execute("UPDATE tasks SET assigned_people = ? WHERE id = ?;", [new_asgn_people, id])

        await self.client.db.commit()
        await c.close()

        embed = await getTaskEmbedFromID(self.client, id)
        await intr.response.send_message(f"Successfully removed {user.display_name} from Task #{id}", embed=embed)


    #-#-#-// Add_Step //-#-#-#

    @app_commands.command(description="Adds a step to chosen task")
    @app_commands.rename(id="task_id", name="step_name", index="place", status="finished")
    @app_commands.describe(id="ID of the task you want to add a step to", name="Step's name",
                           index="Step's placement in the task's description", status="Is the step done or not?")
    async def add_step(self, intr :discord.Interaction, id :int, name :str, index: int = 0, status :bool = False):

        c :asql.Cursor = await self.client.db.cursor()

        index -= 1

        async with c:

            await c.execute("SELECT steps FROM tasks WHERE id = ?;", [id])

            row = await c.fetchone()
            if not row: await intr.response.send_message(task_404.format(id=id)); return
            
            old_steps = row[0]

            if not old_steps: old_steps = []
            else: old_steps = json.loads(old_steps)

            if index < 0: index = len(old_steps)

            old_steps.insert(index, {"name" : name, "status" : status})

            old_steps = json.dumps(old_steps)

            await c.execute("UPDATE tasks SET steps = ? WHERE id = ?;", [old_steps, id])
            await self.client.db.commit()

        embed = await getTaskEmbedFromID(self.client, id)
        await intr.response.send_message(f"Successfully added a new step to Task #{id}", embed=embed)


    #-#-#-// Remove_Step //-#-#-#

    @app_commands.command(description="Removes a chosen step from task")
    @app_commands.rename(id="task_id", index="step_place")
    @app_commands.describe(id="ID of the task you want to remove the step from",
                           index="Step's place in the task")
    async def remove_step(self, intr: discord.Interaction, id: int, index: int):

        c :asql.Cursor = await self.client.db.cursor()

        index -= 1

        async with c:

            await c.execute("SELECT steps FROM tasks WHERE id = ?;", [id])

            row = await c.fetchone()
            if not row: await intr.response.send_message(task_404.format(id=id)); return

            steps = row[0]
            if not steps: await intr.response.send_message(f"Task #{id} doesn't have any steps"); return

            steps = json.loads(steps)

            if not len(steps):

                await c.execute("UPDATE tasks SET steps = NULL WHERE id = ?;", [id])
                await self.client.db.commit()

                await intr.response.send_message(f"Task #{id} doesn't have any steps"); return

            try: steps[index]
            except IndexError:

                await intr.response.send_message(f"Couldn't find step #{index+1}"); return
            
            steps.pop(index)
            steps = json.dumps(steps)

            await c.execute("UPDATE tasks SET steps = ? WHERE id = ?;", [steps, id])
            await self.client.db.commit()


        embed = await getTaskEmbedFromID(self.client, id)
        await intr.response.send_message(f"Successfully removed step #{index+1} from Task #{id}", embed=embed)


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