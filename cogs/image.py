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

    @commands.group(name="image")
    async def image(self, ctx: Context):
        """
        Manipulate images with the power of Xylo!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('image')

    @image.command(name="approved", usage="<URL>")
    async def approve(self, ctx: Context, *args):
        """
        Stamp a picture with an approved stamp. You can input a URL as an argument on attach an image.
        """
        message: discord.Message = ctx.message
        if len(args) == 0:
            if len(message.attachments) == 0:
                await ctx.send("Make sure to send in a file or specify a URL!")
                return
            attachment: discord.Attachment = message.attachments[0]
            if not check_name(attachment.filename):
                await ctx.send("That's not an image!")
                return
            url = attachment.url
        else:
            url = args[0]
        buffer = await util.discord_util.get_data_from_url(url)
        if buffer is None:
            await ctx.send("Something went wrong getting your image. Make sure your URL or file is correct.")
            return
        image = Image.open(fp=buffer)
        approve = Image.open("assets/images/approved.png")

        image = stack_images(image, approve)

        buffer = BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        await ctx.send(f"This has been approved by {ctx.author.mention}.", file=discord.File(fp=buffer, filename="approved.png"))
        await ctx.delete()


def setup(bot):
    bot.add_cog(ImageCog())
