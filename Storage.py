import psycopg2
import os


class Storage:
    DATABASE_URL = os.environ['DATABASE_URL']
    c = None
    conn = None

    # def createtable(self):
    #     print("Connecting to database...")
    #     self.conn = None
    #     command = (
    #         """
    #         CREATE TABLE userdata (
    #             user_id VARCHAR(20) PRIMARY KEY,
    #             user_name VARCHAR(50),
    #             user_school VARCHAR(50)
    #         );
    #         """
    #     )
    #     try:
    #         self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')
    #
    #         self.c = self.conn.cursor()
    #
    #         print("Creating table...")
    #         self.c.execute(command)
    #         self.c.close()
    #         self.conn.commit()
    #         print("Done!")
    #     except (Exception, psycopg2.DatabaseError) as error:
    #         print(error)
    #     finally:
    #         if self.conn is not None:
    #             self.conn.close()

    def insertuserdata(self, id, name, school):
        print("Connecting to database...")
        self.conn = None
        namecom = """INSERT INTO userdata(user_id, user_name, user_school)
                  VALUES(%s, %s, %s);
            """
        try:
            self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            self.c = self.conn.cursor()

            print("Inserting new data for: " + name)
            self.c.execute(namecom, (id, name, school))
            self.c.close()
            self.conn.commit()
            print("Done!")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if self.conn is not None:
                self.conn.close()

    def getuserdata(self, id):
        print("Connecting to database...")
        self.conn = None
        namecom = """INSERT INTO userdata(user_id, user_name, user_school)
                  VALUES(%s, %s, %s);
            """
        try:
            self.conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            self.c = self.conn.cursor()

            print("Grabbing data...")
            self.c.execute("SELECT user_name, user_school FROM userdata ORDER BY user_name")
            print("The number of parts: ", self.c.rowcount)
            row = self.c.fetchone()
            while row is not None:
                print(row)
                row = self.c.fetchone()

            self.c.close()
            print("Done!")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if self.conn is not None:
                self.conn.close()
