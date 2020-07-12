import psycopg2
import os


class Storage:
    DATABASE_URL = os.environ['DATABASE_URL']
    c = None
    conn = None

    def createtable(self):
        print("Connecting to database...")
        self.conn = None
        commands = (
            """
            CREATE TABLE userdata (
                user_id VARCHAR(20) PRIMARY KEY,
                user_name VARCHAR(50),
                user_school VARCHAR(50)
            );
            """
        )
        try:
            self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            self.c = self.conn.cursor()

            print("Creating table...")
            for command in commands:
                self.c.execute(command)

            self.c.close()
            self.conn.commit()
            print("Done!")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if self.conn is not None:
                self.conn.close()


