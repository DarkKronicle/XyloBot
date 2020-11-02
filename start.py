import argparse
import asyncio
import importlib
import logging
import traceback

import psycopg2

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
    connection = psycopg2.connect(f"dbname={config['postgresql_name']} user={config['postgresql_user']} password={config['postgresql_password']}")
    for table in db.Table.all_tables():
        try:
            run(table.create(connection=connection))
        except Exception:
            print(f"Failed creating table {table.tablename}")
            traceback.print_exc()
    connection.commit()
    connection.cursor().close()
    connection.close()


def main():
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
