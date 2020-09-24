import psycopg2
import os


class Database:
    DATABASE_URL = os.environ['DATABASE_URL']

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

    def user_exists(self, user_id):
        user = "'" + user_id + "'"
        command = "SELECT id FROM user_storage WHERE id = %s ORDER BY id;"
        return self.exists(command % user)

    def user_guild_exists(self, user_id, guild_id):
        user = "'" + user_id + "'"
        guild = "'" + guild_id + "'"
        command = "SELECT user_id FROM user_data WHERE user_id = %s and guild_id = %s ORDER BY user_id;"
        return self.exists(command % user % guild)

    def guild_exists(self, guild_id):
        guild = "'" + guild_id + "'"
        command = "SELECT id FROM guild_storage WHERE id = %s ORDER BY id;"
        return self.exists(command % guild)

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
        self.send_commands(command)

    def new_guild(self, guild_id, prefix):
        guild_id = "'" + guild_id + "'"
        prefix = "'" + prefix + "'"
        command = """
                    INSERT INTO guild_storage(id, prefix)
                    VALUES(%s, %s);
                    """

        command = command % guild_id % prefix

        self.send_commands([command])

    def send_commands(self, commands):
        print("Connecting to database...")
        conn = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')
            c = conn.cursor()

            print("Creating table...")
            for command in commands:
                c.execute(command)
            c.close()
            conn.commit()
            print("Done!")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
