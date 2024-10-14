import discord, time, json, aiosqlite as asql
import PIL.Image as Image, pandas as pd, matplotlib.pyplot as plt

from utils.task_embed import TaskEmbed



def getCurrentTime() -> str:

    # 01/01/1970 00:00:00 GMT
    return time.strftime("%d/%m/%Y %H:%M:%S GMT", time.gmtime())


async def getTaskEmbedFromID(client, id :int, deleted :bool = False):

    c :asql.Cursor = await client.db.cursor()

    async with c:
        await c.execute("SELECT * FROM tasks WHERE id = ?", [id])
        values = await c.fetchone()

    if not values: return None

    task_name, dpt_name = values[2], values[1]
    status = values[3]
    steps, assigned_people = values[4], values[5]

    if assigned_people: assigned_people = str(assigned_people)

    embed = TaskEmbed(id, task_name, dpt_name, status, deleted, steps, assigned_people)

    return embed


async def makeTasksFromTXT(client, file :discord.Attachment, ignore_similar_tasks :bool):

    c :asql.Cursor = await client.db.cursor()

    encoding = file.content_type[20:]
    txt = str(await file.read(), encoding)

    tasks = txt.splitlines()


    def removeSpaces(string :str, reverse :bool = False) -> str:

        new_string = string
        if reverse: new_string = reversed(string)

        for char in new_string:

            if char == " ":

                if not reverse: string = string[1:]
                if reverse    : string = string[:-1]
            else:
                break

        return string
        


    processed_tasks = []
    for task in tasks:

        task = task.split(";")
        if len(task) < 2: continue  # Skips empty lines

        for i in range(len(task)):

            task[i] = removeSpaces(task[i])
            task[i] = removeSpaces(task[i], True)

        processed_tasks.append(task)


    rows = []
    for task in processed_tasks:

        task_dpt    = task[0]
        task_name   = task[1]
        task_status = task[2]

        if not ignore_similar_tasks:
            
            await c.execute("SELECT id FROM tasks WHERE department_name = ? AND task_name = ?;", [task_dpt, task_name])

            similar_task = await c.fetchone()
            if not (similar_task is None) and len(similar_task): continue


        status_value = False

        str_status_value = str(task_status).lower()
        if str_status_value == "true": 
            status_value = True

        elif str_status_value != "false" and str_status_value != "": 
            status_value = bool(int(task_status))

        task_status = status_value

        await c.execute("INSERT INTO tasks (department_name, task_name, status) VALUES (?, ?, ?) RETURNING id;", task)

        id = (await c.fetchone())[0]
        await client.db.commit()
        
        status_names = ["In process", "Done"]
        task_status = status_names[int(task_status)]

        row = [id, task_dpt, task_name, task_status]

        rows.append(row)

    print(len(rows))

    column_names = ["IDs", "Department(s)", "Tasks", "Status"]

    return createTable(column_names, rows)


def createTable(column_names :list[str], rows :list[ list[str | int | bool] ]) -> discord.File:

    figure, ax = plt.subplots()

    # Hides axis
    figure.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    df = pd.DataFrame(rows, columns=column_names)

    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', colLoc='center', cellLoc="left")
    table.auto_set_column_width(col=list(range(len(df.columns))))

    figure.tight_layout()


    file_name = f"app_cache/table{time.time().__round__()}.png"
    figure.set_size_inches(13, 7.5)

    plt.savefig(file_name, dpi = 200)

    with Image.open(file_name) as f:

        new_image = f.crop(f.getbbox())
        new_image.save(file_name)


    return discord.File(file_name)