import discord, time, os, json, aiosqlite as asql
from discord import app_commands

from dotenv import load_dotenv
from colorama import Style, Fore, Back
from colorama import just_fix_windows_console as fix_win_console
#from config import *


fix_win_console()
load_dotenv()

production_token = "0"
test_token = os.getenv("token")
debug_guild_id = os.getenv("debug_guild_id")


class ModifiedClient(discord.Client):
    def __init__(self, *, intents :discord.Intents) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        
        # This syncs commands with the debug guild on each run
        self.tree.copy_global_to(guild=debug_guild)
        await self.tree.sync(guild=debug_guild)


intents = discord.Intents.default()
intents.members = True

client = ModifiedClient(intents = intents)
debug_guild = discord.Object(id = debug_guild_id)



#-#-// Functions //-#-#

def getCurrentTime() -> str:

    # 01/01/1970 00:00:00 UTC
    return time.strftime("%d/%m/%Y %H:%M:%S UTC", time.gmtime())


def createTaskEmbed(id: int, dpt: str, desc: str, finished: bool) -> discord.Embed:

    color_hex_value = "3DF991" if finished else "3D9AF9"

    color = discord.colour.parse_hex_number(color_hex_value)
    embed = discord.Embed(color=color, title=desc)

    embed.set_author(name=dpt)
    embed.set_footer(text="ID: "+str(id))

    return embed


def createJSONOfAssignedPeople(json_str: str | None, user: discord.User) -> str:

    assigned_people = {"user_ids":[]} if not json_str else json.loads(json_str)
    
    assigned_people["user_ids"].append(user.id)
    return json.dumps(assigned_people)


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



#-#-// Gateway //-#-#

@client.event
async def on_ready():

    await loadDatabase()
    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))

    print(Fore.GREEN+"-----------\n")
    print(f"The bot has started session at {getCurrentTime()}!")
    print("\n-----------"+Style.RESET_ALL)


@client.event
async def on_resumed():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.GREEN+"-----------\n")
    print(f"The bot has resumed session at {getCurrentTime()}!")
    print("\n-----------"+Style.RESET_ALL)


@client.event
async def on_disconnect():

    await client.change_presence(status = discord.Status.online, activity = discord.Game('BLADEBREAKER'))
    print(Fore.RED+"-----------\n")
    print(f"The bot has disconnected at {getCurrentTime()}!")
    print("\n-----------"+Style.RESET_ALL)



#-#-// Slash Commands //-#-#

@client.tree.command()
async def embedtest(intr):

    embed=discord.Embed(title="Animators")
    embed.add_field(name="task 1", value="- step 1 (:white_check_mark:) \n- step 2", inline=False)

    await intr.response.send_message('', embed=embed)


@client.tree.command(description="Creates a task")
@app_commands.rename(dpt="department_name", name="task_name")
@app_commands.describe(dpt="the department's name", 
                       name="task's name (animate something, code something, etc.)")
async def create_task(intr :discord.Interaction, dpt :str, name :str):

    c: asql.Cursor = await client.db.cursor()
    id: int

    await c.execute("SELECT id FROM tasks WHERE department_name = ? AND task_name = ?;", [dpt, name])
    existing_task = await c.fetchone()

    if len(existing_task): # If the task doesn't exist, the len is 0 (False)

        await intr.response.send_message(f"Task already exists! ID: {existing_task[0]}", ephemeral=True)
        await c.close()
        return
  
    await c.execute(("INSERT INTO tasks (department_name, task_name, status) VALUES (?, ?, ?)"
                        "RETURNING id;"), (dpt, name, False))
        
    id = (await c.fetchone())[0]

    await client.db.commit()
    await intr.response.send_message("Created a task", ephemeral=True)

    embed = createTaskEmbed(id, dpt, name, False)
    msg = await intr.channel.send(embed=embed)
    
    await c.execute("UPDATE tasks SET msg_id = ? WHERE id = ?;", (msg.id, id))

    await client.db.commit()
    await c.close()


@client.tree.command(description="Deletes a chosen task")
@app_commands.rename(id="task_id")
@app_commands.describe(id="id of the task you want to delete")
async def delete_task(intr: discord.Interaction, id: int):

    c: asql.Cursor = await client.db.cursor()

    async with c:
        await c.execute(f"DELETE FROM tasks WHERE id = ?;", [id])
        await client.db.commit()

    await intr.response.send_message(f"Deleted task under id {id}.")    


@client.tree.command()
async def list_tasks(intr: discord.Interaction):
    
    c: asql.Cursor = await client.db.cursor()
    response = ""

    async with c:
        await c.execute("SELECT * FROM tasks;")
        tasks = await c.fetchall()

    for task in tasks:

        id, dpt_name, name = task[0], task[2], task[3]
        finished = True if task[4] else False

        response += ("```"
                     f"Task{id}: ID - {id}\n"
                     f"    ({dpt_name}) {name}\n"
                     f"    Status: {"Done" if finished else "Not finished"}"
                     "```\n\n"
                    )
    
    await intr.response.send_message(response)


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

    await c.execute("UPDATE tasks SET assigned_people = ? WHERE id = ?;", [assigned_people, id])
    await client.db.commit()
    await c.close()
    
    await intr.response.send_message(f"Assigned {user.mention} to Task{id}!", ephemeral=True)



#-#-// Bot Connection //-#-#

try:

    token = 0

    if os.getlogin() == 'pi':

        print(Fore.BLUE+'The bot is using the production token!')
        token = production_token

    else:
        print(Fore.BLUE+'The bot is using the test token!')
        token = test_token

    print(f'Start time: {getCurrentTime()}\n')
    print('---------------'+Style.RESET_ALL)
    client.run(token)

except NameError:
    print(Fore.RED+ '\nFatal: Token variable not found' +Style.RESET_ALL)

except discord.errors.LoginFailure or discord.errors.HTTPException:
    print(Fore.RED+ '\nFatal: Invalid token' +Style.RESET_ALL)