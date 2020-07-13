import psycopg2
import os


class Storage:
    """
    Class to manage the database
    """
    DATABASE_URL = os.environ['DATABASE_URL']

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

    def insertuserdata(self, userid: str, name: str, school: str):
        """
        Insert data into database table.
        """
        conn = None
        namecom = """INSERT INTO userdata(user_id, user_name, user_school)
                    VALUES(%s, %s, %s);
                    """
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            c.execute(namecom, (userid, name, school))
            c.close()
            conn.commit()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        finally:
            if conn is not None:
                conn.close()

    def getuserdata(self, userid: str):
        """
        Return data for a user's ID

        :type userid: int
        """
        conn = None
        row = None
        try:
            conn = psycopg2.connect(self.DATABASE_URL, sslmode='require')

            c = conn.cursor()

            # ID's are stored in string for more flexibility.
            strid = "'" + str(userid) + "'"
            c.execute("SELECT user_name, user_school FROM userdata WHERE user_id = %s ORDER BY user_name" % strid)
            row = c.fetchone()
            c.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        finally:
            if conn is not None:
                conn.close()

        return row
