import enum
from functools import partial

import discord
from scrython.cards.cards_object import CardsObject
from scrython.rulings.rulings_object import RulingsObject


def append_exists(message, **kwargs):
    for k, v in kwargs.items():
        if isinstance(v, tuple):
            m = v[0]
            suffix = v[1]
        else:
            m = v
            suffix = ""
        if m is None:
            continue
        message = message + f"**{k}:** {m}{suffix}\n"
    return message


def color_from_card(card):
    try:
        if card.colors() is None:
            return discord.Colour.light_gray()
        try:
            color = card.colors()[0]
        except IndexError:
            color = card.colors()
    except KeyError:
        return discord.Colour.light_grey()
    if color == "W":
        return discord.Colour.lighter_gray()
    if color == "U":
        return discord.Colour.blue()
    if color == "R":
        return discord.Colour.red()
    if color == "B":
        return discord.Colour.darker_grey()
    if color == "G":
        return discord.Colour.green()
    return discord.Colour.dark_grey()


def card_image_embed(card: CardsObject):
    description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=(card.prices("usd"), "$"))
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Image", url=card.scryfall_uri())
    layout = card.scryfallJson['layout']
    double = layout == "transform" or layout == "double_faced_token"
    try:
        faces = card.card_faces()
        embed.set_image(url=faces[0]["image_uris"]["large"])
        embed.set_thumbnail(url=faces[1]["image_uris"]["large"])
        if card.released_at() is not None:
            embed.set_footer(text=card.released_at())
        return embed
    except KeyError:
        pass
    try:
        url = card.image_uris(0, "large")
    except:
        url = None
    if url is not None:
        embed.set_image(url=str(url))
    if double:
        embed.set_thumbnail(url=str(card.image_uris(1, "large")))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


def card_prices_embed(card: CardsObject):
    description = card.rarity()
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Prices", url=card.scryfall_uri())
    try:
        url = card.image_uris(0, "large")
    except:
        url = None
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    embed.add_field(name="USD", value=f"${card.prices('usd')}")
    embed.add_field(name="USD Foil", value=f"{card.prices('usd_foil')}")
    embed.add_field(name="EUR", value=f"€{card.prices('eur')}")
    embed.add_field(name="TIX", value=f"{card.prices('tix')}")
    return embed


def card_legal_embed(card: CardsObject):
    description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=(card.prices("usd"), "$"))
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Legalities", url=card.scryfall_uri())
    try:
        url = card.image_uris(0, "large")
    except:
        url = None
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())

    legal = card.legalities()

    def pretty(form, val):
        return form.capitalize(), val.replace("_", " ").capitalize()

    for k, v in legal.items():
        name, value = pretty(k, v)
        embed.add_field(name=name, value=value)

    return embed


def card_text_embed(card: CardsObject):

    def oracle(c: CardsObject):
        o = ""
        try:
            faces = c.card_faces()
            for f in faces:
                o += f["oracle_text"] + "\n\n"
        except:
            o = c.oracle_text()
        return o

    # https://github.com/NandaScott/Scrython/blob/master/examples/get_and_format_card.py
    if "Creature" in card.type_line():
        try:
            pt = "({}/{})".format(card.power(), card.toughness())
        except KeyError:
            pt = ""
    else:
        pt = ""

    if card.cmc() == 0:
        mana_cost = ""
    else:
        try:
            mana_cost = card.mana_cost()
        except KeyError:
            mana_cost = ""

    description = """
    `{mana_cost}`   -    {set_code}
    {type_line}

    {oracle_text} {power_toughness}
    *{rarity}*
    """.format(
        cardname=card.name(),
        mana_cost=mana_cost,
        type_line=card.type_line(),
        set_code=card.set_code(),
        rarity=card.rarity().capitalize(),
        oracle_text=oracle(card),
        power_toughness=pt
    ).replace("    ", "")
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Text", url=card.scryfall_uri())
    try:
        url = card.image_uris(0, "large")
    except:
        url = None
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


def rulings_embed(card: CardsObject, rulings: RulingsObject):
    data = rulings.data()
    embed = discord.Embed(
        colour=discord.Colour.gold(),
        description="Here's what I know about this card:"
    )
    embed.set_author(name=card.name() + " - Rulings", url=card.scryfall_uri())
    i = 0
    if len(data) == 0:
        embed.description = "Nothing found."
        return embed
    for ruling in data:
        i = i + 1
        if i > 10:
            break
        embed.add_field(name=ruling['source'], value=ruling['comment'], inline=False)
    return embed


class CardView(enum.Enum):
    image = partial(card_image_embed)
    text = partial(card_text_embed)
    legalities = partial(card_legal_embed)
    prices = partial(card_prices_embed)
