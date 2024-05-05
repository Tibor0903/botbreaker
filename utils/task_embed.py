from discord import Embed as ds_Embed
from discord import colour as ds_colour

from json import loads as json_loads


class TaskEmbed(ds_Embed):

    def __init__(self, *, id :int, task_name :str, task_dpt :str, finished :bool = False, deleted :bool = False, steps :str = None, assigned_peeps :str = None):

        super().__init__(title=task_name)

        color_hex_value = "3DF991" if finished else "3D9AF9"
        color_hex_value = "FF3838" if deleted else color_hex_value

        self.color = ds_colour.parse_hex_number(color_hex_value)

        status_emoji = ":white_check_mark:" if finished else ":blue_square:"
        if deleted: status_emoji = "[DELETED]"

        icon_url = ("https://cdn.discordapp.com/attachments/1234791407265251402/1236177556630142996/6d66b23b5f142921.jpg?"
                    "ex=66370f90&is=6635be10&hm=6f1163150dd284b768e4da7caba14450d6265c8d298bbc47d91beb8afba70c95&")

        self.set_author(name=task_dpt, icon_url=icon_url)
        description = f"Status: {status_emoji}\n\n"
        
        if steps:
            i = 0
            steps :list = (json_loads(steps))["steps"]
            for step in steps:

                status_str = "Finished :white_check_mark:" if step["status"] else "In progress :blue_square:"
                if deleted: status_str = ":x:"

                description += f"{str(i+1)}. {step["name"]}: {status_str}\n"
                i += 1

        if assigned_peeps:
            description += "\n Assigned people: \n"

            people = (json_loads(assigned_peeps))["user_ids"]
            for user_id in people:

                description += f"<@{user_id}>\n"

        self.description = description

        self.set_footer(text = f"ID: {id}")