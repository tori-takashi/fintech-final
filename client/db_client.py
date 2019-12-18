from configparser import SafeConfigParser
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DBClient:
    def __init__(self, db_type, opt=None):
        self.config = SafeConfigParser()
        self.opt = opt

        # config.ini should be same place to executing file
        self.config.read("config.ini")
        self.db_type = db_type

        # sql alchemy configurations
        self.engine = self.establish_connection_to_db()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def is_sqlite3(self):
        return self.db_type == "sqlite3"

    def establish_connection_to_db(self):
        if self.is_sqlite3():
            return self.sqlite3_establish_connection()

    def sqlite3_establish_connection(self):
        if self.opt == None:
            return create_engine("sqlite3:///" + self.config['sqlite3']['db_path'], echo=True)
        else:
            return create_engine("sqlite3:///" + self.opt)

    def write_to_table(self, table_name, dataframe, if_exists):
        dataframe.to_sql(table_name, self.engine,
                         if_exists=if_exists, index=False)

    def overwrite_to_table(self, table_name, dataframe):
        self.write_to_table(table_name, dataframe, if_exists="replace")

    def append_to_table(self, table_name, dataframe):
        self.write_to_table(table_name, dataframe, if_exists="append")

    def is_table_exist(self, table_name):
        query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{}';".format(table_name)
        results = self.exec_sql(table_name, query, False)
        for result in results:
            if result == (1,):
                return True
            else:
                return False

    def get_last_row(self, table_name):
        if self.is_sqlite3():
            query = "SELECT * FROM " + table_name + " WHERE index = last_insert_rowid();"
        self.exec_sql(table_name, query)

    def exec_sql(self, table_name, query, return_df=True):
        result_rows = self.cursor.execute(query)
        if return_df:
            column_names = self.get_column_name(table_name)
            return pd.DataFrame(data=result_rows, columns=column_names)
        else:
            return result_rows

    def get_column_name(self, table_name):
        if self.is_sqlite3():
            query = "SELECT * FROM " + table_name + ";"
            result = self.cursor.execute(query)
            return result.description
