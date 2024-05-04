from datetime import datetime
import discord, time, os, json, aiosqlite as asql
from discord import app_commands

from dotenv import load_dotenv
from colorama import Style, Fore, Back
from colorama import just_fix_windows_console as fix_win_console

fix_win_console()
load_dotenv()

production_token = "0"
test_token = os.getenv("token")
debug_guild_id = os.getenv("debug_guild_id")

sys_message_divider = "---------------"


class ModifiedClient(discord.Client):
    def __init__(self, *, intents :discord.Intents) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        
        # This syncs commands with the debug guild on each run
        self.tree.copy_global_to(guild=debug_guild)
        await self.tree.sync(guild=debug_guild)


class TaskEmbed(discord.Embed):
    def __init__(self, *, id :int, task_name :str, task_dpt :str, finished :bool = False, deleted :bool = False, steps :str = None, assigned_peeps :str = None):

        super().__init__(title=task_name)

        color_hex_value = "3DF991" if finished else "3D9AF9"
        color_hex_value = "FF3838" if deleted else color_hex_value

        self.color = discord.colour.parse_hex_number(color_hex_value)

        status_emoji = ":white_check_mark:" if finished else ":blue_square:"
        if deleted: status_emoji = "[DELETED]"

        icon_url = ("https://cdn.discordapp.com/attachments/1234791407265251402/1236177556630142996/6d66b23b5f142921.jpg?"
                    "ex=66370f90&is=6635be10&hm=6f1163150dd284b768e4da7caba14450d6265c8d298bbc47d91beb8afba70c95&")

        self.set_author(name=task_dpt, icon_url=icon_url)
        description = f"Status: {status_emoji}\n\n"
        
        if steps:
            i = 0
            steps :list = (json.loads(steps))["steps"]
            for step in steps:

                status_str = "Finished :white_check_mark:" if step["status"] else "In progress :blue_square:"
                if deleted: status_str = ":x:"

                description += f"{str(i+1)}. {step["name"]}: {status_str}\n"
                i += 1

        if assigned_peeps:
            description += "\n Assigned people: \n"

            people = (json.loads(assigned_peeps))["user_ids"]
            for user_id in people:

                description += f"<@{user_id}>\n"

        self.description = description

        self.set_footer(text = f"ID: {id}")

        

intents = discord.Intents.default()
intents.members = True

client = ModifiedClient(intents = intents)
debug_guild = discord.Object(id = debug_guild_id)



#-#-#-#-#-#-#-#-#-#-#-#-#-#-// Functions //-#-#-#-#-#-#-#-#-#-#-#-#-#-#



def getCurrentTime() -> str:

    # 01/01/1970 00:00:00 GMT
    return time.strftime("%d/%m/%Y %H:%M:%S GMT", time.gmtime())


async def getTaskEmbedFromID(id :int):

    c :asql.Cursor = await client.db.cursor()

    async with c:
        await c.execute("SELECT * FROM tasks WHERE id = ?", [id])
        values = await c.fetchone()

    if not values: return None

    task_name, dpt_name = values[3], values[2]
    status = True if values[4] else False
    steps, assigned_people = values[6], values[5]

    embed = TaskEmbed(id=id, task_name=task_name, task_dpt=dpt_name, finished=status, steps=steps, assigned_peeps=assigned_people)

    return embed


async def updateTaskEmbed(intr :discord.Interaction, msg_id :int, embed :discord.Embed):

    for channel in intr.guild.channels:
        if type(channel) != discord.TextChannel: continue

        msg = await channel.fetch_message(msg_id)
        await msg.edit(embed = embed)



def createJSONOfAssignedPeople(json_str: str | None, user: discord.User) -> str:

    assigned_people = {"user_ids":[]} if not json_str else json.loads(json_str)
    
    assigned_people["user_ids"].append(user.id)
    return json.dumps(assigned_people)


def createJSONSteps(json_str: str | None, step_name: str, step_status: bool, index :int) -> str:
    
    steps = {"steps":[]} if not json_str else json.loads(json_str)
    index = len(steps["steps"]) if index <= 0 else index - 1

    steps["steps"].insert(index, {"name":step_name, "status":step_status})
    return json.dumps(steps)


def createTable(keys :list, values :list):

    horizontal_count = [len(key) for key in keys]

    for value_tuple in values:

        for value in value_tuple:
            i = value_tuple.index(value)

            if horizontal_count[i] >= len(str(value)): continue

            horizontal_count[i] = len(str(value))

    table = ""

    for key in keys:
        i = keys.index(key)

        table += key
        for i in range(horizontal_count[i] - len(key)): table += " "
        table += " | "

    divider = "\n"
    for i in range(len(keys)):
        
        for o in range(horizontal_count[i]): divider += "-"

        if i == len(keys) - 1: divider += "-|"
        else: divider += "-|-"

    value_rows = "\n"
    for value_tuple in values:
        for value in value_tuple:
            i = value_tuple.index(value)
            value = str(value)

            value_rows += value
            for o in range(horizontal_count[i] - len(value)): value_rows += " "
            value_rows += " | "

        value_rows += "\n"

    table += divider + value_rows

    return table


async def loadDatabase() -> None:

    client.db = await asql.connect("main.db")
    cursor = await client.db.cursor()

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
        
    await client.db.commit()



#-#-#-#-#-#-#-#-#-#-// Gateway //-#-#-#-#-#-#-#-#-#-#



@client.event
async def on_ready():

    await loadDatabase()
    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))

    print(Fore.GREEN+f"{sys_message_divider}\n")
    print(f"The bot has started session at {getCurrentTime()}!")
    print(f"\n{sys_message_divider}"+Style.RESET_ALL)


@client.event
async def on_resumed():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+f"{sys_message_divider}\n")
    print(f"The bot has resumed session at {getCurrentTime()}!")
    print(f"\n{sys_message_divider}"+Style.RESET_ALL)


@client.event
async def on_disconnect():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.RED+f"{sys_message_divider}\n")
    print(f"The bot has disconnected at {getCurrentTime()}!")
    print(f"\n{sys_message_divider}"+Style.RESET_ALL)



#-#-#-#-#-#-#-#-#-#-#-#-#-// Slash Commands //-#-#-#-#-#-#-#-#-#-#-#-#-#



@client.tree.command()
async def embedtest(intr):

    embed=discord.Embed(title="Animators")
    embed.add_field(name="task 1", value="- step 1 (:white_check_mark:) \n- step 2", inline=False)

    await intr.response.send_message('', embed=embed)


#-#-#-// Create_Task //-#-#-#

@client.tree.command(description="Creates a task")
@app_commands.rename(dpt="department_name", name="task_name")
@app_commands.describe(dpt="the department's name", 
                       name="task's name (animate something, code something, etc.)",
                       hide_reply="hides a reply to the command (also doesn't show who ran the command)")
async def create_task(intr :discord.Interaction, dpt :str, name :str, hide_reply :bool = False):

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

@client.tree.command(description="Deletes a chosen task")
@app_commands.rename(id="task_id")
@app_commands.describe(id="id of the task you want to delete")
async def delete_task(intr: discord.Interaction, id: int):

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

@client.tree.command()
async def show_task(intr :discord.Interaction, id :int):

    c :asql.Cursor = await client.db.cursor()
    embed = await getTaskEmbedFromID(id)

    if not embed:

        await intr.response.send_message(f"```ml\n ERROR: task doesn't exist```")
        return

    await intr.response.send_message(embed = embed)

    msg = await intr.original_response()

    async with c:
        await c.execute("UPDATE tasks SET msg_id = ? WHERE id = ?", [msg.id, id])
        await client.db.commit()


#-#-#-// List_Tasks //-#-#-#

@client.tree.command()
async def list_tasks(intr: discord.Interaction):
    
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


    response_msg += createTable(["ids", "task_name", "message_ids", "status"], new_tasks)

    await intr.response.defer()
    await intr.followup.send(response_msg +"```")


#-#-#-// Assign_People //-#-#-#

@client.tree.command(description="Assigns chosen user to a task")
@app_commands.rename(id="task_id")
@app_commands.describe(id="id of the task you want to assign the user to",
                       user="the user you want to assign to the task (automatically selects you if skipped)")
async def assign_people(intr: discord.Interaction, id: int, user: discord.User = None):

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

@client.tree.command()
async def create_step(intr :discord.Interaction, id :int, name :str, index: int = 0, status :bool = False):

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

@client.tree.command()
async def update_step(intr :discord.Interaction, task_id :int, step_index :int, new_name :str):

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


#-#-#-// get db //-#-#-#

@client.tree.command(name = 'getdb', description='get the database (debug)', guild = debug_guild)
async def get_db(intr :discord.Interaction):
    await intr.response.send_message('',file=discord.File('main.db'))



#-#-#-#-#-#-#-#-#-// Bot Connection //-#-#-#-#-#-#-#-#-#



try:
    token = 0

    if os.getlogin() == 'pi':

        print(Fore.BLUE+'The bot is using the production token!')
        token = production_token

    else:
        print(Fore.BLUE+'The bot is using the test token!')
        token = test_token

    print(f'Start time: {getCurrentTime()}\n')
    print(f'{sys_message_divider}'+Style.RESET_ALL)
    client.run(token)

except NameError:
    print(Fore.RED+ '\nFatal: Token variable not found' +Style.RESET_ALL)

except discord.errors.LoginFailure or discord.errors.HTTPException:
    print(Fore.RED+ '\nFatal: Invalid token' +Style.RESET_ALL)