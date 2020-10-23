import psycopg2
import os
import json
from storage.config import *


class Database:
    DATABASE_URL = os.environ['DATABASE_URL']

    def add_user(self, settings, user_id, guild_id):
        command = f"INSERT INTO user_data(guild_id, user_id, info) " \
                  f"VALUES($${guild_id}$$, $${user_id}$$, $${json.dumps(settings)}$$);"
        self.send_commands([command])

    def update_user(self, settings, user_id, guild_id):
        command = f"UPDATE user_data SET info = $${json.dumps(settings)}$$ WHERE guild_id = $${guild_id}$$ and " \
                  f"user_id = $${user_id}$$;"
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

    def add_mark(self, guild_id, name, text="", files=None):
        if files is None:
            files = []

        data = {}
        if text is not None and text != "":
            data["text"] = text
        else:
            data["text"] = ""

        if files is not None:
            data["files"] = files
        else:
            data["files"] = []

        command = f"INSERT INTO mark_entries(guild_id, name, data) VALUES ($${guild_id}$$, $${name}$$, $${json.dumps(data)}$$);"
        self.send_commands([command])

    def get_marks(self, guild_id):
        command = "SELECT name, data FROM mark_entries WHERE guild_id IN ({}, $$global$$);"
        command = command.format("$$" + guild_id + "$$")
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(command)
            row = c.fetchall()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return None
        else:
            return row

    def get_mark(self, guild_id, name):
        command = f"SELECT data FROM mark_entries WHERE guild_id IN ($${guild_id}$$, $$global$$) AND name = $${name}$$;"

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

    def get_mark_named(self, name):
        command = f"SELECT name FROM mark_entries WHERE name = $${name}$$;"
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

    def remove_mark(self, guild_id, name):
        command = f"DELETE FROM mark_entries WHERE guild_id = $${guild_id}$$ AND name = $${name}$$;"
        self.send_commands([command])
