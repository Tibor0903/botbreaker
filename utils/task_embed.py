from discord import Embed as ds_Embed
from discord import colour as ds_colour

from json import loads as json_loads


class TaskEmbed(ds_Embed):

    def __init__(self, id :int, task_name :str, task_dpt :str, task_finished :bool = False, deleted :bool = False, steps :str = None, assigned_peeps :str = None):

        super().__init__(title=task_name)

        red_color   = "FF3838"
        green_color = "3DF991"
        blue_color  = "3D9AF9"

        if task_finished:

            task_color   = green_color
            status_emoji = ":white_check_mark:"
        else:

            task_color   = blue_color
            status_emoji = ":blue_square:"

        if deleted:

            task_color   = red_color
            status_emoji = ":x:"

        self.color = ds_colour.parse_hex_number(task_color)

        icon_url = ("https://cdn.discordapp.com/attachments/1234791407265251402/1236177556630142996/6d66b23b5f142921.jpg?"
                    "ex=66370f90&is=6635be10&hm=6f1163150dd284b768e4da7caba14450d6265c8d298bbc47d91beb8afba70c95&")

        self.set_author(name = task_dpt, icon_url = icon_url)
        description = f"Status: {status_emoji}\n"


        if assigned_peeps:

            description += "\nAssigned people: \n"

            user_ids = assigned_peeps.split(",")
            ids_len  = len(user_ids)

            for i, user_id in enumerate(user_ids):

                description += f"<@{user_id}>"

                if i+1 != ids_len: description += ", "

                if (i+1) % 3 == 0 and i+1 != ids_len: description += "\n"

            description += "\n"


        if steps:
            
            description += "\n"

            steps :list = (json_loads(steps))
            steps_len   = len(steps)

            for i, step in enumerate(steps):

                status_str = "Finished :white_check_mark:" if step["status"] else "In progress :blue_square:"

                description += f"{str(i+1)}. {step['name']}: {status_str}"

                if i+1 != steps_len: description += "\n"


        self.description = description
        self.set_footer(text = f"ID: {id}")