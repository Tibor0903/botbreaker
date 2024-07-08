import discord
from aiosqlite import Cursor

from utils.task_embed import TaskEmbed
from utils.functions import getTaskEmbedFromID



class TaskCreationButtons(discord.ui.View):

    def __init__(self, name :str, dpt :str, finished :bool, client, timeout = 180):
        super().__init__(timeout=timeout)

        self.name = name
        self.dpt = dpt
        self.status = finished
        self.db_client = client


    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def confirm_button(self, intr :discord.Interaction, button :discord.ui.Button):

        self.clear_items()
        await intr.response.edit_message(view=self)
        
        c = await self.db_client.db.cursor()
        async with c:

            await c.execute(("INSERT INTO tasks (department_name, task_name, status) VALUES (?, ?, ?)"
                            "RETURNING id;"), [self.dpt, self.name, self.status])
            
            id = (await c.fetchone())[0]
            await self.db_client.db.commit()

        embed = TaskEmbed(id, self.name, self.dpt, self.status)
        await intr.channel.send(embed=embed)


    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def cancel_button(self, intr :discord.Interaction, button :discord.ui.Button):
        
        self.clear_items()
        await intr.response.edit_message(content= ":(", view=self)



class TaskDeletionButtons(discord.ui.View):

    def __init__(self, id :int, client, timeout = 180):
        super().__init__(timeout=timeout)

        self.id = id
        self.db_client = client

    
    @discord.ui.button(label="No", style=discord.ButtonStyle.gray)
    async def cancel_button(self, intr :discord.Interaction, button :discord.ui.Button):
        
        self.clear_items()
        await intr.response.edit_message(content= f"Task (id: {self.id}) removal has been canceled", view=self)


    @discord.ui.button(label="Yes, delete the task", style=discord.ButtonStyle.danger)
    async def deletion_button(self, intr :discord.Interaction, button :discord.ui.Button):

        client = self.db_client
        
        self.clear_items()

        embed = await getTaskEmbedFromID(client, self.id, True)
        await intr.response.edit_message(content= f"Task (id: {self.id}) has been successfully removed", embed=embed, view=self)

        c :Cursor = await client.db.cursor()
        async with c:

            await c.execute("DELETE FROM tasks WHERE id = ?;", [self.id])
            await client.db.commit()