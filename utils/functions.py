import discord, time, json, aiosqlite as asql
import PIL.Image as Image, pandas as pd, matplotlib.pyplot as plt

from utils.task_embed import TaskEmbed



def getCurrentTime() -> str:

    # 01/01/1970 00:00:00 GMT
    return time.strftime("%d/%m/%Y %H:%M:%S GMT", time.gmtime())


def listFind(array :list, value_to_find) -> bool:

    try:

        array.index(value_to_find)
        return True
    
    except ValueError: return False


async def getTaskEmbedFromID(client, id :int, deleted :bool = False):

    c :asql.Cursor = await client.db.cursor()

    async with c:
        await c.execute("SELECT * FROM tasks WHERE id = ?", [id])
        values = await c.fetchone()

    if not values: return None

    task_name, dpt_name = values[2], values[1]
    status = values[3]
    steps, assigned_people = values[4], str(values[5])

    embed = TaskEmbed(id, task_name, dpt_name, status, deleted, steps, assigned_people)

    return embed


def createJSONSteps(json_str: str | None, step_name: str, step_status: bool, index :int) -> str:
    
    steps = {"steps":[]} if not json_str else json.loads(json_str)
    index = len(steps["steps"]) if index <= 0 else index - 1

    steps["steps"].insert(index, {"name":step_name, "status":step_status})
    return json.dumps(steps)


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