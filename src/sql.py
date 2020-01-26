import sqlite3


class Sqlite3_db():
    def __init__(self):
        self.connection = sqlite3.connect("sql/sql.db")
        self.cursor = self.connection.cursor()

        # Create blacklisted_channels table
        sql_command = """
        CREATE TABLE IF NOT EXISTS blacklisted_channels ( 
        channel_id VARCHAR(30) NOT NULL PRIMARY KEY,
        guild_id VARCHAR(30) NOT NULL 
        );
        """
        self.cursor.execute(sql_command)

        sql_command = """
        CREATE TABLE IF NOT EXISTS admins ( 
        user_id VARCHAR(30) NOT NULL,
        guild_id VARCHAR(30) NOT NULL 
        );
        """
        self.cursor.execute(sql_command)

        self.connection.commit()
        return

    def add_blacklist_channel(self, guild_id: str, channel_id: str):
        sql_command = f"""
        INSERT INTO blacklisted_channels (guild_id, channel_id) VALUES ({guild_id}, {channel_id});
        """
        try:
            self.cursor.execute(sql_command)
            self.connection.commit()
        except Exception as e:
            print(e)
            return

        return

    def add_admin(self, guild_id: str, user_id: str):
        sql_command = f"""
        INSERT INTO admins (guild_id, user_id) VALUES ({guild_id}, {user_id});
        """

        try:
            self.cursor.execute(sql_command)
            self.connection.commit()
        except Exception as e:
            print(e)
            return

        return

    def remove_admin(self, guild_id: str, user_id: str):
        sql_command = f"""
        DELETE FROM admins WHERE (guild_id={guild_id} AND user_id={user_id}); 
        """

        try:
            self.cursor.execute(sql_command)
            self.connection.commit()
        except Exception as e:
            print(e)
            return

        return

    # TODO
    def remove_channel(self, guild_id: str, channel_id: str):
        sql_command = f"""
        DELETE FROM blacklisted_channels WHERE (guild_id={guild_id} AND channel_id={channel_id}); 
        """

        try:
            self.cursor.execute(sql_command)
            self.connection.commit()
        except Exception as e:
            print(e)
            return

        return

    def get_blacklisted_channels(self, guild_id: str):
        sql_command = f"""
        SELECT channel_id FROM blacklisted_channels WHERE guild_id = {guild_id};
        """
        self.cursor.execute(sql_command)

        result_tuples = self.cursor.fetchall()
        print(result_tuples)

        result = [t[0] for t in result_tuples]
        print(result)

        return result

    def get_admins(self, guild_id: str):
        sql_command = f"""
        SELECT user_id FROM admins WHERE guild_id = {guild_id};
        """
        self.cursor.execute(sql_command)

        result_tuples = self.cursor.fetchall()
        print(result_tuples)

        result = [t[0] for t in result_tuples]
        print(result)

        return result
