import psycopg2
import os
import json
from storage.Config import *


class Database:
    DATABASE_URL = os.environ['DATABASE_URL']

    def alter(self):
        command = """
                ALTER TABLE guild_storage ADD COLUMN settings json; 
                """
        self.send_commands([command])

    def create_tables(self):
        commands = ["""
                    CREATE TABLE IF NOT EXISTS user_storage (
                        id VARCHAR(20) PRIMARY KEY,
                        twitch VARCHAR(50),
                        youtube VARCHAR(50)
                    ); 
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id VARCHAR(20) NOT NULL,
                        guild_id VARCHAR(20) NOT NULL,
                        first_name VARCHAR(20),
                        last_name VARCHAR(20),
                        school VARCHAR(20),
                        info VARCHAR(255), 
                        birthday DATE,
                        PRIMARY KEY (user_id, guild_id)
                    ); 
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS guild_storage (
                        id VARCHAR(20) PRIMARY KEY,
                        prefix VARCHAR(5) NOT NULL DEFAULT '>' 
                    ); 
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS verify_queue (
                        user_id VARCHAR(20) NOT NULL,
                        guild_id VARCHAR(20) NOT NULL,
                        first_name VARCHAR(20),
                        last_name VARCHAR(20),
                        school VARCHAR(20),
                        info VARCHAR(255), 
                        birthday DATE, 
                        PRIMARY KEY (user_id, guild_id)
                    );
                    """]
        self.send_commands(commands)

    def get_all_unverified(self, guild_id):
        command = "SELECT user_id FROM verify_queue WHERE guild_id = {} ORDER BY user_id;"
        command = command.format("$$" + guild_id + "$$")
        conn = None
        rows = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            rows = c.fetchall()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if rows is None:
            return None
        else:
            return rows

    def add_unverified(self, settings, user_id, guild_id):
        command = f"INSERT INTO verify_queue(guild_id, user_id, info) " \
                  f"VALUES($${guild_id}$$, $${user_id}$$, $${json.dumps(settings)}$$);"
        self.send_commands([command])

    def delete_unverified(self, guild_id, user_id):
        command = f"DELETE FROM verify_queue WHERE guild_id = $${guild_id}$$ AND user_id = $${user_id}$$"
        self.send_commands([command])

    def add_user(self, settings, user_id, guild_id):
        command = f"INSERT INTO user_data(guild_id, user_id, info) " \
                  f"VALUES($${guild_id}$$, $${user_id}$$, $${json.dumps(settings)}$$);"
        self.send_commands([command])

    def get_user(self, guild_id, user_id):
        command = "SELECT info FROM user_data WHERE guild_id = {} and user_id = {};"
        command = command.format("$$" + guild_id + "$$", "$$" + user_id + "$$")
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            row = c.fetchone()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return None
        else:
            data = row[0]
            return data

    def get_unverified(self, guild_id, user_id):
        command = "SELECT info FROM verify_queue WHERE guild_id = {} and user_id = {};"
        command = command.format("$$" + guild_id + "$$", "$$" + user_id + "$$")
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            row = c.fetchone()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return None
        else:
            data = row[0]
            return data


    def user_exists(self, user_id):
        user = "$$" + user_id + "$$"
        command = "SELECT id FROM user_storage WHERE id = {} ORDER BY id;"
        return self.exists(command.format(user))

    def user_guild_exists(self, user_id, guild_id):
        user = "$$" + user_id + "$$"
        guild = "$$" + guild_id + "$$"
        command = "SELECT user_id FROM user_data WHERE user_id = {} AND guild_id = {} ORDER BY user_id;"
        return self.exists(command.format(user, guild))

    def guild_exists(self, guild_id):
        guild = "$$" + guild_id + "$$"
        command = "SELECT id FROM guild_storage WHERE id = {} ORDER BY id;"
        return self.exists(command.format(guild))

    def set_prefix(self, guild_id, prefix):
        guild_id = "$$" + guild_id + "$$"
        prefix = "$$" + prefix + "$$"
        command = """
                UPDATE guild_storage SET prefix = {} WHERE id = {}; 
                """
        command = command.format(prefix, guild_id)
        self.send_commands([command])

    def get_prefix(self, guild_id):
        command = "SELECT prefix FROM guild_storage WHERE id = {} ORDER BY id;"
        command = command.format("$$" + guild_id + "$$")
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            row = c.fetchone()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return None
        else:
            return row[0]

    def set_settings(self, guild_id, settings: dict):
        guild_id = "$$" + guild_id + "$$"
        command = """
                   UPDATE guild_storage SET settings = {} WHERE id = {}; 
                   """
        command = command.format("$$" + json.dumps(settings) + "$$", guild_id)
        self.send_commands([command])

    def get_settings(self, guild_id):
        command = "SELECT settings FROM guild_storage WHERE id = {} ORDER BY id;"
        command = command.format("$$" + guild_id + "$$")
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            row = c.fetchone()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            self.default_settings(guild_id)
            return ConfigData.defaultsettings.data
        else:
            data = row[0]
            return data

    def exists(self, command):
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            row = c.fetchone()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return False
        else:
            return True

    def add_user_storage(self, values: dict):
        columns = values.keys()
        insert = values.values()
        if "user_id" not in columns or "guild_id" not in columns:
            raise ValueError("guild_id or user_id cannot be NoneType")
        command = ["""
         
        """]
        self.send_commands([command])

    def default_settings(self, guild_id):
        if not self.guild_exists(guild_id):
            self.new_guild(guild_id, ">")
        self.set_settings(guild_id, ConfigData.defaultsettings.data)

    def new_guild(self, guild_id, prefix):
        guild_id = "$$" + guild_id + "$$"
        prefix = "$$" + prefix + "$$"
        command = """
                    INSERT INTO guild_storage(id, prefix)
                    VALUES({}, {});
                    """

        command = command.format(guild_id, prefix)

        self.send_commands([command])

    def send_commands(self, commands):
       # print("Connecting to database...")
        conn = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')
            c = conn.cursor()

            for command in commands:
                c.execute(command)
            c.close()
            conn.commit()
            # print("Done!")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
