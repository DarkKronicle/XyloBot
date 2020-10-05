from io import BytesIO

from discord.ext import commands
import discord
from util.context import Context
import util.discord_util
from util.image_util import *
from PIL import Image, ImageFont, ImageDraw

def check_name(name):
    ext = [".png", ".jpg", ".jpeg"]
    for extension in ext:
        if name.endswith(extension):
            return True
    return False

class ImageCog(commands.Cog, name="Image"):
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
        if not check_name(attachment.filename):
            await ctx.send("That's not an image!")
            return
        url = attachment.url
        buffer = await util.discord_util.get_data_from_url(url)
        image = Image.open(fp=buffer)
        approve = Image.open("assets/images/transparent-stamp.png")
        approve_h = approve.size[1]
        approve_w = approve.size[0]
        image_h = approve.size[1]
        image_w = approve.size[0]
        image = resize(image, approve_w)
        image.paste(approve, (int((image_w / 2) - (approve_w / 2)), int((image_h / 2) - (approve_h / 2))), approve)
        buffer = BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        await ctx.send("The results are in: It's approved!", file=discord.File(fp=buffer, filename="approved.png"))


def setup(bot):
    bot.add_cog(ImageCog())
