import discord
import io
import aiohttp


async def get_file_from_image(url: str, name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = io.BytesIO(await resp.read())
            return discord.File(data, name)


async def get_data_from_url(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = io.BytesIO(await resp.read())
            return data
