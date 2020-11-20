import argparse
import asyncio
import importlib
import logging
import sys
import traceback
import urllib

import aiohttp
import scrython
import psycopg2
from scrython.foundation import FoundationObject, ScryfallError

from storage import db
from storage.json_reader import JSONReader
from xylo_bot import XyloBot, startup_extensions


def run_bot():
    bot = XyloBot()
    bot.run()


config = JSONReader('config.json').data


def database():
    run = asyncio.get_event_loop().run_until_complete

    cogs = startup_extensions

    for ext in cogs:
        try:
            importlib.import_module("cogs." + ext)
        except Exception:
            print(f'Could not load {ext}')
            traceback.print_exc()
            return

    print(f"Preparing to create {len(db.Table.all_tables())} tables.")
    connection = psycopg2.connect(
        f"dbname={config['postgresql_name']} user={config['postgresql_user']} password={config['postgresql_password']}")
    for table in db.Table.all_tables():
        try:
            run(table.create(connection=connection))
        except Exception:
            print(f"Failed creating table {table.tablename}")
            traceback.print_exc()
    connection.commit()
    connection.cursor().close()
    connection.close()


def patch_scrython():
    """
    Scrython and discord.py don't really like to share asyncio loops. To fix this I change where it uses loops to
    just use async functions that can be called whenever. Not just in the __init__.
    """
    def new_init(self, _url, override=False, **kwargs):
        self.params = {
            'format': kwargs.get('format', 'json'), 'face': kwargs.get('face', ''),
            'version': kwargs.get('version', ''), 'pretty': kwargs.get('pretty', '')
        }

        self.encodedParams = urllib.parse.urlencode(self.params)
        self._url = 'https://api.scryfall.com/{0}&{1}'.format(_url, self.encodedParams)

        if override:
            self._url = _url

    async def get_request(self, client, url, **kwargs):
        async with client.get(url, **kwargs) as response:
            return await response.json()

    async def request_data(self):
        async with aiohttp.ClientSession() as client:
            self.scryfallJson = await self.get_request(client, self._url)
        if self.scryfallJson['object'] == 'error':
            raise ScryfallError(self.scryfallJson, self.scryfallJson['details'])

    FoundationObject.__init__ = new_init
    FoundationObject.request_data = request_data
    FoundationObject.get_request = get_request


def my_except_hook(exctype, value, traceback):
    if exctype == RuntimeError:
        print("DARK YOU NEED TO FIX ME!")
    else:
        sys.__excepthook__(exctype, value, traceback)


def main():
    patch_scrython()
    db.Table.create_data(config['postgresql_name'], config['postgresql_user'], config['postgresql_password'])
    database()
    run_bot()


def _cli():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    # parser.add_argument('config_file', help="Which config file to use",
    #                     default="configs.json")
    # ADD OTHER VARIABLES BELOW THIS LINE
    parser.add_argument('-d', '--debug', help="Pring debuggin information",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.ERROR)
    parser.add_argument('-v', '--verbose', help="Print extra information about the process",
                        action="store_const", dest="loglevel", const=logging.INFO)
    # turn those words into arguments/variables
    args = parser.parse_args()

    # set up the logging defaults
    logging.basicConfig(level=args.loglevel,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    return vars(args)


if __name__ == "__main__":
    main()
