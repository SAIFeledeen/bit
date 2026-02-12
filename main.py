import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import asyncio
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID')) if os.getenv('ADMIN_ROLE_ID') else None

class OrderBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

class OrderView(discord.ui.View):
    def __init__(self, order_summary: str):
        super().__init__(timeout=None)
        self.order_summary = order_summary

    @discord.ui.button(label="Claim Order / Open Ticket", style=discord.ButtonStyle.green, custom_id="claim_btn")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        button.label = "Order Claimed"
        button.style = discord.ButtonStyle.grey
        
        await interaction.message.edit(view=self)

        guild = interaction.guild
        user = interaction.user
        admin_role = guild.get_role(ADMIN_ROLE_ID) if ADMIN_ROLE_ID else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"order-{user.name}",
            overwrites=overwrites
        )

        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        
        ticket_welcome = (
            f"## Order Ticket for {user.mention}\n"
            f"{self.order_summary}\n"
            f"{'─' * 28}\n"
            f"An admin will be with you shortly."
        )
        await channel.send(ticket_welcome)

bot = OrderBot()

@bot.tree.command(name="order", description="Place an order")
@app_commands.describe(
    item1="First item", quant1="Qty", price1="Price per unit",
    item2="Second item", quant2="Qty", price2="Price per unit",
    item3="Third item", quant3="Qty", price3="Price per unit",
    item4="Fourth item", quant4="Qty", price4="Price per unit",
    item5="Fifth item", quant5="Qty", price5="Price per unit"
)
async def order(
    interaction: discord.Interaction, 
    item1: str, quant1: int, price1: int,
    item2: Optional[str] = None, quant2: Optional[int] = None, price2: Optional[int] = None,
    item3: Optional[str] = None, quant3: Optional[int] = None, price3: Optional[int] = None,
    item4: Optional[str] = None, quant4: Optional[int] = None, price4: Optional[int] = None,
    item5: Optional[str] = None, quant5: Optional[int] = None, price5: Optional[int] = None
):
    summary_lines = []
    total_quantity = 0
    grand_total_price = 0


    pairs = [
        (item1, quant1, price1), 
        (item2, quant2, price2), 
        (item3, quant3, price3), 
        (item4, quant4, price4), 
        (item5, quant5, price5)
    ]
    
    for item, quant, price in pairs:
        if item and quant is not None and price is not None:
            subtotal = quant * price
            summary_lines.append(f"**{item}**: {quant} x {price} = **{subtotal}**")
            total_quantity += quant
            grand_total_price += subtotal

    order_text = "\n".join(summary_lines)

    embed = discord.Embed(
        title="🛒 New Order Received",
        description=order_text,
        color=discord.Color.blue()
    )
    embed.add_field(name="Total Items", value=str(total_quantity), inline=True)
    embed.add_field(name="Total Price", value=f"**{grand_total_price}**", inline=True)
    embed.set_footer(text="Click the button below to claim this order.")

    await interaction.response.send_message(embed=embed, view=OrderView(order_text))

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        bot.http.connector = connector
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass