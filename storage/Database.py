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
