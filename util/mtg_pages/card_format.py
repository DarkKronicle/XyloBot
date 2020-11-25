import enum
from functools import partial

import discord
from scrython.cards.cards_object import CardsObject


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
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_image(url=str(url))
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
    url = card.image_uris(0, "large")
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
    url = card.image_uris(0, "large")
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
    # https://github.com/NandaScott/Scrython/blob/master/examples/get_and_format_card.py
    if "Creature" in card.type_line():
        pt = "({}/{})".format(card.power(), card.toughness())
    else:
        pt = ""

    if card.cmc() == 0:
        mana_cost = ""
    else:
        mana_cost = card.mana_cost()

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
        oracle_text=card.oracle_text(),
        power_toughness=pt
    ).replace("    ", "")
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Text", url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


class CardView(enum.Enum):
    image = partial(card_image_embed)
    text = partial(card_text_embed)
    legalities = partial(card_legal_embed)
    prices = partial(card_prices_embed)