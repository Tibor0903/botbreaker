import discord
from utils.task_embed import TaskEmbed



class TaskCreationButtons(discord.ui.View):

    def __init__(self, id :int, name :str, dpt :str, finished :bool, client, timeout = 10):
        super().__init__(timeout=timeout)

        self.id = id
        self.name = name
        self.dpt = dpt
        self.status = finished
        self.db_client = client


    async def on_timeout(self):

        c = await self.db_client.db.cursor()

        async with c:

            await c.execute("SELECT task_name, department_name FROM tasks WHERE id = ?;", [self.id])
            items = await c.fetchone()

            if not (items is None) and self.name == items[0] and self.dpt == items[1]:

                await c.execute("DELETE FROM tasks WHERE id = ?;", [self.id])


    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def confirm_button(self, intr :discord.Interaction, button :discord.ui.Button):

        button.disabled = True
        await intr.response.edit_message(view=self)

        embed = TaskEmbed(id=self.id, task_name=self.name, task_dpt=self.dpt, finished=self.status)
        msg = await intr.channel.send(embed=embed)
        
        c = await self.db_client.db.cursor()
        async with c:

            await c.execute("UPDATE tasks SET msg_id = ? WHERE id = ?;", [msg.id, self.id])
            await self.db_client.db.commit()


    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def cancel_button(self, intr :discord.Interaction, button :discord.ui.Button):
        
        button.disabled = True
        await intr.response.edit_message(view=self)

        c = await self.db_client.db.cursor()
        async with c:

            await c.execute("DELETE FROM tasks WHERE id = ?;", [self.id])
            await self.db_client.db.commit()