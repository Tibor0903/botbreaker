import discord, time, json, aiosqlite as asql

from utils.task_embed import TaskEmbed



def getCurrentTime() -> str:

    # 01/01/1970 00:00:00 GMT
    return time.strftime("%d/%m/%Y %H:%M:%S GMT", time.gmtime())


async def getTaskEmbedFromID(client, id :int):

    c :asql.Cursor = await client.db.cursor()

    async with c:
        await c.execute("SELECT * FROM tasks WHERE id = ?", [id])
        values = await c.fetchone()

    if not values: return None

    task_name, dpt_name = values[3], values[2]
    status = True if values[4] else False
    steps, assigned_people = values[6], values[5]

    embed = TaskEmbed(id, task_name, dpt_name, status, steps, assigned_people)

    return embed


def createJSONOfAssignedPeople(json_str: str | None, user: discord.User) -> str:

    assigned_people = {"user_ids":[]} if not json_str else json.loads(json_str)
    
    assigned_people["user_ids"].append(user.id)
    return json.dumps(assigned_people)


def createJSONSteps(json_str: str | None, step_name: str, step_status: bool, index :int) -> str:
    
    steps = {"steps":[]} if not json_str else json.loads(json_str)
    index = len(steps["steps"]) if index <= 0 else index - 1

    steps["steps"].insert(index, {"name":step_name, "status":step_status})
    return json.dumps(steps)


def createTable(keys :list, values :list, used_char_amount :int) -> str:

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

    available_char_count = 2000 - (2 + used_char_amount + len(table) + len(divider))

    value_rows = "\n"
    for value_tuple in values:
        for value in value_tuple:

            i = value_tuple.index(value)
            value = str(value)

            value_row = ""

            value_row += value
            for o in range(horizontal_count[i] - len(value)): value_row += " "
            value_row += " | "

            if available_char_count >= len(value_row): 

                value_rows += value_row
                available_char_count -= len(value_row)
                continue

            break

        if available_char_count < 2: break
        available_char_count -= 2
        value_rows += "\n"

    table += divider + value_rows

    return table