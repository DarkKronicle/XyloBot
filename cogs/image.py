from io import BytesIO

from discord.ext import commands
import discord
from util.context import Context
import util.discord_util
from util.image_util import *
from PIL import Image, ImageFont, ImageDraw


class Image(commands.Cog):
    @commands.group(name="edit")
    async def edit(self, ctx):
        pass

    @edit.command(name="approval")
    async def approve(self, ctx: Context):
        message: discord.Message = ctx.message
        if len(message.attachments) == 0:
            await ctx.send("Make sure to send in a file!")
            return
        attachment: discord.Attachment = message.attachments[0]
        name: str = attachment.filename
        ext = [".png", ".jpg", ".jpeg"]
        one = False
        for extension in ext:
            if name.endswith(extension):
                one = True
                break
        if not one:
            await ctx.send("That's not an image!")
            return
        url = attachment.url
        buffer = await util.discord_util.get_data_from_url(url)
        if buffer is None:
            await ctx.send("Something went wrong getting your image.")
            return
        image = Image.open(fp=buffer)
        image = resize(image, 770)
        approve = Image.open("assets/images/transparent-stamp.png")
        image.paste(approve, (0, 0))
        buffer = BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        await ctx.send("The results are in: It's approved!", file=discord.File(fp=buffer, filename="approved.png"))


def setup(bot):
    bot.add_cog(Image())
