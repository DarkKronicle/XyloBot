import psycopg2
import os


class Storage:
    DATABASE_URL = os.environ['DATABASE_URL']
    c = None

    def connect(self):
        print("Connecting to database...")
        conn = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            self.c = conn.cursor()

            print('PostgreSQL database version:')
            self.c.execute('SELECT version()')

            db_version = self.c.fetchone()
            print(db_version)
            self.c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

    def close(self):
        self.c.close()
